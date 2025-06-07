import { getLogger } from "../utils/log/log.ts";
import { fetchThingModel } from "../utils/tm.ts";
import cache, { EndNode } from "../services/cache.ts";
import { AppManifest } from "../models/appManifest.ts";
import { InstantiationOpts, produceTD } from "../utils/td.ts";
import { ContextualLogger } from "../utils/log/contextLogger.ts";
import { Buffer, crc32, mqtt, ThingDescription, UUID } from "../../deps.ts";
import {
  AppSrcFile,
  encodeContentBase64,
  fetchAppManifest,
  fetchAppSrc,
  filterAppFetchErrors,
} from "../services/appManifestService.ts";

type MqttFormOptions = {
  href: string;
  topic: string;
  qos?: 0 | 1 | 2;
  retain?: boolean;
};

type WriteActionInput = {
  path: string;
  payload: {
    data: string;
    hash: string;
    algo: "crc32";
  };
  append?: boolean;
};

type DeleteActionInput = {
  path: string;
  recursive?: boolean; // If path is a directory, delete all contents recursively
};

type OTAUErrorResult = {
  error: true;
  message: string;
};

type OTAUWriteResult = {
  error: false;
  written: string;
};

type OTAUDeleteResult = {
  error: false;
  deleted: string[];
};

type OTAUReport = {
  timestamp: {
    epoch_year?: number;
    seconds: number;
  };
  result: OTAUWriteResult | OTAUDeleteResult | OTAUErrorResult;
};

export type ControllerOpts = {
  subscribeEventQos: 0 | 1 | 2;
  observePropertyQoS: 0 | 1 | 2;
};

const CoreStatusValues = ["UNDEF", "OTAU", "APP"] as const;
type CoreStatus = (typeof CoreStatusValues)[number];

class Controller {
  static compatible = {
    url: "https://example.com/embedded-core-tm",
    version: "1.0.0",
  };

  private topicPrefix: string;
  private client?: mqtt.MqttClient;
  private logger: ContextualLogger;
  private coreStatus: CoreStatus = "UNDEF";
  private adaptationInProgress = false;

  private adaptationReplaceSet: Set<string> = new Set();
  private static readonly adaptationReplaceIgnore = [
    "main.py",
    "main.mpy",
    "citylink/core.py",
    "citylink/core.mpy",
    "config/config.json",
  ];
  // coreDirs are not elegible for recursive deletion
  private static readonly coreDirs = ["citylink", "citylink/ext", "config"];

  private otauInitPromise?: {
    resolve: () => void;
    reject: (e?: unknown) => void;
  };

  private otauFinishPromise?: {
    resolve: () => void;
    reject: (e?: unknown) => void;
  };

  private otauWritePromise?: {
    resolve: (val: string | PromiseLike<string>) => void;
    reject: (e?: unknown) => void;
  };

  private otauDeletePromise?: {
    resolve: (val: string[] | PromiseLike<string[]>) => void;
    reject: (e?: unknown) => void;
  };

  constructor(
    public id: UUID,
    private node: EndNode,
    private brokerURL: string = "mqtt://localhost:1883",
    private brokerOpts: mqtt.IClientOptions = {},
    private controllerOpts: ControllerOpts = {
      subscribeEventQos: 0,
      observePropertyQoS: 0,
    },
  ) {
    this.topicPrefix = `citylink/${this.id}/`;
    this.logger = new ContextualLogger(getLogger(import.meta.url), {
      node: this.id,
    });
  }

  launch(_httpProxy?: boolean, _httpBaseURL?: URL): void {
    this.client = mqtt.connect(this.brokerURL, this.brokerOpts);

    this.client.on("connect", () => {
      this.logger.info(`🔌 Connected to MQTT broker at ${this.brokerURL}`);
      this.subscribeToAll(
        "property",
        this.controllerOpts.observePropertyQoS,
        "citylink:platform_",
      );
      this.subscribeToAll(
        "event",
        this.controllerOpts.subscribeEventQos,
        "citylink:platform_",
      );
      this.publishDefaultProperties();

      if (this.coreStatus === "UNDEF") {
        this.logger.info(
          `🟡 Node is in UNDEF state. Waiting for core status update...`,
        );
      }
    });

    this.client.on("message", (topic, message) => {
      // Filter out messages that don't start with our topic prefix
      if (!topic.startsWith(this.topicPrefix)) {
        this.logger.debug(`Ignoring message on unrelated topic: ${topic}`);
        return;
      }

      // Remove the prefix to get the affordance namespace and name
      const affordance = topic.slice(this.topicPrefix.length);
      const [affordanceType, affordanceNamespace, ...affordanceNameParts] =
        affordance.split("/");
      const affordanceName = affordanceNameParts.join("/");

      if (!["properties", "events", "actions"].includes(affordanceType)) return;
      if (!affordanceType || !affordanceNamespace || !affordanceName) return;

      // Ignore all messages that relate to the platform namespace
      if (affordanceNamespace === "platform") {
        this.logger.debug(
          `Ignoring platform message for ${affordanceType} "${affordanceName}"`,
        );
        return;
      }

      this.logger.info(
        `📩 --${affordanceType}-- ${affordanceNamespace}/${affordanceName}: ${message.toString()}`,
      );

      if (affordanceNamespace === "core") {
        this.handleCoreMessage(affordanceType, affordanceName, message);
      }
    });
  }

  // TODO: deduplicate this with EndNode.ts ...
  // Resource fetching is duplicated with the registration procedure
  async otauInit(appManifestUrl: URL): Promise<void>;
  async otauInit(appManifest: AppManifest): Promise<void>;
  async otauInit(arg: URL | AppManifest): Promise<void> {
    if (this.otauInitPromise || this.otauFinishPromise) {
      this.logger.warn(
        "⚠️ OTAU procedure already in progress or finished. Cannot start a new one.",
      );
      return Promise.reject(new Error("In progress"));
    }

    if (this.coreStatus !== "APP") {
      this.logger.error(
        `❌ Cannot start adaptation procedure in current status: ${this.coreStatus}`,
      );
      return Promise.reject(
        new Error(`Invalid core status: ${this.coreStatus}`),
      );
    }

    let manifest: AppManifest;
    if (arg instanceof URL) {
      this.logger.info(`📥 Fetching app manifest from ${arg.toString()}`);
      const fetched = await fetchAppManifest(arg.toString());
      if (fetched instanceof Error) {
        this.logger.error(
          `❌ Failed to fetch app manifest: ${fetched.message}`,
        );
        return Promise.reject(fetched);
      }
      manifest = fetched;
      this.logger.info(
        `📥 App manifest fetched successfully from ${arg.toString()}`,
      );
    } else {
      manifest = arg as AppManifest;
      this.logger.info(`📥 Using provided app manifest`);
    }

    this.logger.info(`📥 Fetching Thing Model for new application.`);
    const tm = await fetchThingModel(manifest.wot.tm);
    if (tm instanceof Error) {
      return Promise.reject(`❌ Failed to fetch Thing Model: ${tm.message}`);
    }

    const opts: InstantiationOpts = {
      endNodeUUID: this.id,
      protocol: "mqtt",
    };

    this.logger.info(
      `⚙️ Instantiating Thing Description from new Thing Model.`,
    );

    const td = await produceTD(tm, opts);
    if (td instanceof Error) {
      return Promise.reject(`❌ Error during TD instantiation: ${td.message}`);
    }

    cache.updateEndNode(this.id, { tm, td, manifest });

    return new Promise((resolve, reject) => {
      this.logger.info("🔄 Starting adaptation procedure...");
      this.otauInitPromise = { resolve, reject };
      this.invokeAction("citylink:embeddedCore_OTAUInit").catch((err) => {
        this.logger.error(
          `❌ Failed to invoke OTAU init action: ${err.message}`,
        );
        this.otauInitPromise?.reject(err);
        this.otauInitPromise = undefined;
      });
    });
  }

  private handleCoreMessage(
    affordanceType: string,
    affordanceName: string,
    message: Buffer,
  ) {
    switch (affordanceType) {
      case "properties":
        this.handleCoreProperty(affordanceName, message);
        break;
      case "events":
        this.handleCoreEvent(affordanceName, message);
        break;
      case "actions":
        this.logger.error(
          "⚠️ Core actions should not be subscribed by the controller",
        );
        break;
      default:
        this.logger.warn(
          `⚠️ Unknown core affordance type "${affordanceType}" for "${affordanceName}"`,
        );
    }
  }

  private handleCoreProperty(
    affordanceName: string,
    message: Buffer,
  ): void {
    const value = message.toString();

    switch (affordanceName) {
      case "status": {
        this.logger.info(`Core status update: ${JSON.stringify(value)}`);
        if (!CoreStatusValues.includes(value as CoreStatus)) {
          this.logger.error(
            `❌ Invalid core status value: ${value}. Expected one of ${
              CoreStatusValues.join(", ")
            }`,
          );
          return;
        }
        this.handleCoreStatus(value as CoreStatus);
      }
    }
  }

  private handleCoreStatus(value: CoreStatus) {
    this.coreStatus = value;

    switch (value) {
      case "OTAU":
        this.logger.info(`🟡 Node entered OTAU mode.`);
        if (this.otauInitPromise) {
          this.otauInitPromise?.resolve();
          this.otauInitPromise = undefined;
        } else if (this.otauFinishPromise) {
          this.logger.warn("Aborting current adaptation process.");
          this.otauFinishPromise.reject(
            new Error("❌Node rebooted into OTAU mode unexpectedly."),
          );
        }

        if (this.adaptationInProgress) {
          this.logger.warn(
            "⚠️ Adaptation already in progress. Skipping re-initialization.",
          );
          return;
        }

        this.logger.info("🔄 Over The Air Update procedure initialized.");
        this.adaptationFetchAndUpload();
        break;

      case "APP":
        this.logger.info(`🟢 Node entered to APP mode.`);
        this.otauFinishPromise?.resolve();
        this.otauFinishPromise = undefined;
        break;

      case "UNDEF":
        this.logger.warn(`⚪ Node is in undefined state.`);
        break;
    }
  }

  private handleCoreEvent(affordanceName: string, message: Buffer): void {
    const value = message.toString();

    switch (affordanceName) {
      case "otau/report":
        this.logger.info(`Received OTAU write event: ${value}`);
        this.handleOtauReport(value);
        break;
      default:
        this.logger.warn(
          `⚠️ Unknown core event "${affordanceName}" with value "${value}"`,
        );
    }
  }

  private handleOtauReport(value: string): void {
    const report = JSON.parse(value);
    if (!report || typeof report !== "object") {
      this.logger.error(`❌ Invalid OTAU report format: ${value}`);
      return;
    }

    const { timestamp, result } = report as OTAUReport;
    if (!timestamp || !result) {
      this.logger.error(`❌ OTAU report missing timestamp or result: ${value}`);
      return;
    }

    const { epoch_year = 1970, seconds } = report.timestamp;
    const base = Date.UTC(epoch_year, 0, 1); // January 1st of the year
    const date = new Date(base + seconds * 1000);

    this.logger.info(
      `📅 OTAU report received at ${date.toISOString()}: ${
        JSON.stringify(result, null, 2)
      }`,
    );

    if (result.error) {
      //TODO: assert only one of these is present
      this.otauWritePromise?.reject(new Error(result.message));
      this.otauDeletePromise?.reject(new Error(result.message));
    } else if ("written" in result) {
      this.otauWritePromise!.resolve(result.written);
    } else if ("deleted" in result) {
      this.otauDeletePromise!.resolve(result.deleted);
    } else {
      this.logger.error(
        "❌ Unknown OTAU report result format:",
        JSON.stringify(result),
      );
    }
  }

  private adaptationFetchAndUpload(): void {
    this.adaptationInProgress = true;
    this.logger.info("📦 Downloading application source...");

    fetchAppSrc(this.node.manifest.download).then((fetchResult) => {
      const fetchErrors = filterAppFetchErrors(fetchResult);
      if (fetchErrors.length > 0) {
        this.logger.error(
          `❌ Failed to fetch application source: ${
            fetchErrors.map((e) => e.error).join(", ")
          }`,
        );

        this.logger.critical("❗️Adaptation failed due to fetch errors.");
        return;
      }

      const appSource = fetchResult as AppSrcFile[];
      this.logger.info(
        `📦 Downloaded ${appSource.length} files for adaptation.`,
      );

      this.adaptEndNode(appSource).finally(() => {
        this.adaptationInProgress = false;
        this.logger.info("🔄 Adaptation procedure completed.");
      });
    }).catch((error) => {
      this.logger.error(
        `❌ Error during application source fetch: ${error.message}`,
      );
      this.logger.critical("❗️Adaptation failed due to fetch error.");
    });
  }

  private async adaptEndNode(appSource: AppSrcFile[]) {
    if (this.coreStatus !== "OTAU") {
      this.logger.warn(
        `❌ Cannot start adaptation procedure in current status: ${this.coreStatus}`,
      );
      return;
    }

    //TODO: allow for customization of the type of adaptation
    const hasMain = appSource.some((file) =>
      file.path === "main.py" || file.path === "main.mpy"
    );
    if (!hasMain) {
      this.logger.error(
        `❌ Application source must contain "main.py" or "main.mpy" file for adaptation.`,
      );
      return;
    }

    this.logger.info("🔄 Starting adaptation procedure...");
    // Step 1: Delete files from previous adaptation (if any)
    const toDelete = this.resolveMinimumDeletions(appSource);
    if (toDelete.size > 0) {
      this.logger.info(
        `📤 Deleting ${toDelete.size} file(s) from previous adaptation...`,
      );
    }

    for (const path of toDelete) {
      try {
        this.logger.debug(`📤 Deleting file ${path} from end node...`);
        const deletedPaths = await this.otauDelete(path, true);
        this.logger.debug(`✅ File(s) deleted: ${deletedPaths.join(", ")}`);
      } catch (err) {
        this.logger.error(`❌ Failed to delete file ${path}:`, err);
        // Stop on first failure
        return;
      }
    }

    this.logger.info("📥 Writing files to end node...");
    for (const file of appSource) {
      try {
        this.logger.debug(`📥 Writing file ${file.path}`);

        const writtenPath = await this.otauWrite(file);

        if (writtenPath !== file.path) {
          this.logger.warn(
            `⚠️ Written path "${writtenPath}" does not match expected "${file.path}".`,
          );
          //TODO: handle retry or rollback logic here
          break; // Stop processing if mismatch
        }

        this.logger.debug(`✅ File ${writtenPath} written successfully.`);

        // Add to adaptationReplaceSet for future deletions
        if (!Controller.adaptationReplaceIgnore.includes(file.path)) {
          this.adaptationReplaceSet.add(file.path);
        }
      } catch (err) {
        this.logger.error(`❌ Failed to write file ${file.path}:`, err);
        break; // Stop on failure
      }
    }

    // if (this.prevAdaptationReplaceList.length !== appSource.length) {
    //   const remaining = appSource.length -
    //     this.prevAdaptationReplaceList.length;
    //   this.logger.warn(
    //     `⚠️ ${remaining} file(s) were not processed due to previous errors.`,
    //   );
    //
    //   // Optional: try to rollback or cleanup
    // }

    try {
      await this.otauFinish();
    } catch (err) {
      this.logger.error(`❌ Failed to finish OTAU procedure: ${err}`);
      this.logger.critical("❗️End node may be in an inconsistent state.");
    }
  }

  private resolveMinimumDeletions(src: AppSrcFile[]): Set<string> {
    // Create a set of paths from the new src files
    const newFiles = new Set(
      src.map((file) => file.path),
    );

    // Files that need to be removed are those from the adaptationReplaceSet
    // that will not be overwritten by the new src files.
    return new Set<string>([...this.adaptationReplaceSet]).difference(newFiles);
  }

  private otauWrite(file: AppSrcFile) {
    const data = encodeContentBase64(file.content);
    const hash = `0x${(crc32(data) >>> 0).toString(16)}`;

    // TODO: Maybe verify this against the TD instead
    const writeInput: WriteActionInput = {
      path: file.path,
      payload: { data, hash, algo: "crc32" },
      append: false,
    };

    return new Promise<string>((resolve, reject) => {
      this.logger.info(`📤 Writing file ${file.path} to end node...`);
      this.otauWritePromise = { resolve, reject };

      this.invokeAction("citylink:embeddedCore_OTAUWrite", writeInput)
        .catch((err) => {
          this.logger.error(`❌ Failed to write file ${file.path}:`, err);
          this.otauWritePromise?.reject(err);
          this.otauWritePromise = undefined;
        });
    });
  }

  private otauDelete(
    path: string,
    recursive: boolean = false,
  ): Promise<string[]> {
    const deleteInput: DeleteActionInput = { path, recursive };

    // Reject deletion if recursive and path is a core directory
    if (recursive && Controller.coreDirs.some((dir) => path.startsWith(dir))) {
      this.logger.error(
        `❌ Cannot delete core directory "${path}" recursively.`,
      );
      return Promise.reject(
        new Error(`Cannot delete core directory "${path}" recursively.`),
      );
    }

    return new Promise<string[]>((resolve, reject) => {
      const delType = recursive ? "directory" : "file";

      this.logger.info(`📤 Deleting ${delType} "${path}" from end node...`);
      this.otauDeletePromise = { resolve, reject };

      this.invokeAction("citylink:embeddedCore_OTAUDelete", deleteInput).catch(
        (err) => {
          this.logger.error(`❌ Failed to delete ${delType} "${path}":`, err);
          this.otauDeletePromise?.reject(err);
          this.otauDeletePromise = undefined;
        },
      );
    });
  }

  private otauFinish(): Promise<void> {
    if (this.coreStatus !== "OTAU") {
      this.logger.error(
        `❌ Cannot finish OTAU procedure in current status: ${this.coreStatus}`,
      );
      return Promise.reject(new Error("invalid core status"));
    }

    return new Promise((resolve, reject) => {
      this.logger.info("✅ Sending finish signal for OTAU procedure.");
      this.logger.warn(
        "⚠️ Device will reboot and its state will be `UNDEF` until reconnection.",
      );
      this.otauFinishPromise = { resolve, reject };
      this.invokeAction("citylink:embeddedCore_OTAUFinish").catch((err) => {
        this.logger.error(
          `❌ Failed to invoke OTAU init action: ${err.message}`,
        );
        this.otauFinishPromise?.reject(err);
        this.otauFinishPromise = undefined;
      });
    });
  }

  private publish(value: unknown, opts: MqttFormOptions): Promise<void> {
    if (opts.href !== this.brokerURL) {
      return Promise.reject(
        new Error(`❌ Mismatched href: ${opts.href} != ${this.brokerURL}`),
      );
    }

    return new Promise((resolve, reject) => {
      this.logger.debug(
        `📤 Publishing value: ${JSON.stringify(value)} to topic: ${opts.topic}`,
      );

      this.client!.publish(opts.topic, JSON.stringify(value), {
        retain: opts.retain,
        qos: opts.qos,
      }, (err) => {
        if (err) {
          reject(err);
        } else resolve();
      });
    });
  }

  private extractMqttOptions(
    forms: ThingDescription["forms"],
    affordanceType: "property" | "event" | "action",
    expectedOp: string,
  ): MqttFormOptions | null {
    const topicKey = (() => {
      switch (affordanceType) {
        case "property":
        case "event":
          return "mqv:filter";
        case "action":
          return "mqv:topic";
      }
    })();

    if (!forms || !forms.length) return null;

    for (const form of forms) {
      const ops = Array.isArray(form.op) ? form.op : [form.op];
      if (!ops.includes(expectedOp)) continue;

      const topic = form[topicKey] as string | undefined;
      const href = form.href;
      if (!topic || !href) continue;

      return {
        href,
        topic,
        qos: form["mqv:qos"] as 0 | 1 | 2 | undefined,
        retain: form["mqv:retain"] as boolean | undefined,
      };
    }

    return null;
  }

  private publishDefaultProperties(): void {
    for (const [name, prop] of Object.entries(this.node.td.properties ?? {})) {
      const val = prop.const ?? prop.default ?? null;
      if (val === null) continue;

      const opts = this.extractMqttOptions(
        prop.forms,
        "property",
        "readproperty",
      );
      if (opts) {
        this.publish(val, opts).catch((err) => {
          this.logger.error(
            `❌ Failed to publish default property "${name}": ${err.message}`,
          );
        });
      } else {
        this.logger.warn(`⚠️ No MQTT config for property "${name}"`);
      }
    }
  }

  private subscribeToAll(
    type: "property" | "event",
    qos: 0 | 1 | 2,
    ignore_prefix?: string,
  ): void {
    // Check first top level forms for subscribeallevents or observeallproperties
    const topLevelOP = type === "property"
      ? "observeallproperties"
      : "subscribeallevents";

    const opts = this.extractMqttOptions(
      this.node.td.forms,
      type,
      topLevelOP,
    );

    if (opts) {
      this.subscribeToTopic(topLevelOP, opts.topic, qos);
      return; // If we have a top-level subscription, we don't need to iterate affordances
    } else {
      this.logger.warn(
        `⚠️ No MQTT config for top-level ${type} subscription. trying individual affordances.`,
      );
    }

    const op = type === "property" ? "observeproperty" : "subscribeevent";
    const entries = type === "property"
      ? Object.entries(this.node.td.properties ?? {})
      : Object.entries(this.node.td.events ?? {});

    for (const [name, obj] of entries) {
      if (ignore_prefix && name.startsWith(ignore_prefix)) {
        this.logger.debug(`Skipping ${type} "${name}" due to ignore prefix`);
        continue;
      }

      const opts = this.extractMqttOptions(obj.forms, type, op);
      if (opts) {
        this.subscribeToTopic(name, opts.topic, qos);
      } else {
        this.logger.warn(`⚠️ No MQTT config for ${type} "${name}"`);
      }
    }
  }

  private subscribeToTopic(name: string, topic: string, qos: 0 | 1 | 2): void {
    this.client?.subscribe(topic, { qos }, (err) => {
      if (err) {
        this.logger.error(`❌ Subscription failed for "${name}":`, err);
      } else {
        this.logger.info(`📡 Subscribed to "${name}" on topic "${topic}"`);
      }
    });
  }

  private invokeAction(
    name: string,
    input?: unknown,
  ): Promise<void> {
    const action = this.node.td.actions?.[name];
    if (!action) {
      return Promise.reject(
        new Error(`❌Action "${name}" not found in Thing Description`),
      );
    }

    const opts = this.extractMqttOptions(
      action.forms,
      "action",
      "invokeaction",
    );
    if (!opts) {
      return Promise.reject(
        new Error(
          `❌ No MQTT config for action "${name}" in Thing Description.`,
        ),
      );
    }

    //TODO: validate input against action.input schema
    const actionInput = input ?? "";
    this.logger.debug(
      `📤 Invoking action "${name}" with input: ${actionInput}`,
    );

    return new Promise((resolve, reject) => {
      this.publish(actionInput, opts)
        .then(() => {
          this.logger.info(`✅ Action "${name}" invoked successfully.`);
          resolve();
        })
        .catch((err) => {
          this.logger.error(`❌ Failed to invoke action "${name}":`, err);
          reject(err);
        });
    });
  }
}

export default Controller;

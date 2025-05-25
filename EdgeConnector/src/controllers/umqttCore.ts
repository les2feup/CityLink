import { Buffer, mqtt, ThingDescription, UUID } from "../../deps.ts";
import {
  AppFetchSuccess,
  fetchAppManifest,
  fetchAppSrc,
  filterAppFetchErrors,
} from "../services/appManifestService.ts";
import { EndNode } from "../services/cache.ts";
import { getLogger } from "../utils/log/log.ts";

type MqttFormOptions = {
  href: string;
  topic: string;
  qos?: 0 | 1 | 2;
  retain?: boolean;
};

export type ControllerOpts = {
  subscribeEventQos: 0 | 1 | 2;
  observePropertyQoS: 0 | 1 | 2;
};

const CoreStatusValues = ["OK", "ADAPT", "ERROR", "UNDEF"] as const;
type CoreStatus = (typeof CoreStatusValues)[number];

class Controller {
  static compatible = {
    url: "https://example.com/embedded-core-tm",
    version: "1.0.0",
  };

  private topicPrefix: string;
  private client?: mqtt.MqttClient;
  private logger = getLogger(import.meta.url);
  private coreStatus: CoreStatus = "UNDEF";

  constructor(
    public id: UUID,
    public node: EndNode,
    public brokerURL: string = "mqtt://localhost:1883",
    public brokerOpts: mqtt.IClientOptions = {},
    public controllerOpts: ControllerOpts = {
      subscribeEventQos: 0,
      observePropertyQoS: 0,
    },
  ) {
    this.topicPrefix = `citylink/${this.id}/`;
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
        this.logger.warn(
          "⚠️ Events are not yet implemented in core affordances",
        );
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
      case "OK":
        this.logger.info("Core is operating normally.");
        break;
      case "ADAPT":
        this.logger.warn("Core is in adaptation mode");
        this.adaptationProcedure();
        break;
      case "ERROR":
        this.logger.error("Core encountered an error. Check logs for details.");
        break;
      case "UNDEF":
        this.logger.warn("Core status is undefined. Please investigate.");
        break;
    }
  }

  private adaptationProcedure(): void {
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

      const appSource = fetchResult as AppFetchSuccess[];
      this.logger.info(
        `📦 Downloaded ${appSource.length} files for adaptation.`,
      );

      this.adaptEndNode(appSource);
    });
  }

  adaptEndNode(_appSource: AppFetchSuccess[]) {
    if (this.coreStatus !== "ADAPT") {
      this.logger.error(
        `❌ Cannot adapt end node in current status: ${this.coreStatus}`,
      );
      return;
    }

    this.logger.info("🔄 Starting adaptation procedure...");

    // TODO: Implement adaptation logic based on appSource
  }

  private publish(value: unknown, opts: MqttFormOptions): void {
    if (opts.href !== this.brokerURL) {
      this.logger.error(
        `❌ Mismatched href: ${opts.href} != ${this.brokerURL}`,
      );
      return;
    }

    this.client?.publish(opts.topic, JSON.stringify(value), {
      retain: opts.retain,
      qos: opts.qos,
    }, (err) => {
      if (err) {
        this.logger.error(`❌ Failed to publish to ${opts.topic}:`, err);
      } else {
        this.logger.debug(`✅ Published to ${opts.topic}:`, value);
      }
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
        this.publish(val, opts);
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
}

export default Controller;

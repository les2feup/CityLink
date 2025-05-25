import { mqtt, ThingDescription, UUID } from "../../deps.ts";
import { getLogger } from "../utils/log/log.ts";

const logger = getLogger();

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

class Controller {
  static compatible = {
    url: "https://example.com/embedded-core-tm",
    version: "1.0.0",
  };

  private client?: mqtt.MqttClient;

  constructor(
    public id: UUID,
    public td: ThingDescription,
    public brokerURL: string = "mqtt://localhost:1883",
    public brokerOpts: mqtt.IClientOptions = {},
    public controllerOpts: ControllerOpts = {
      subscribeEventQos: 0,
      observePropertyQoS: 0,
    },
  ) {}

  launch(_httpProxy?: boolean, _httpBaseURL?: URL): void {
    this.client = mqtt.connect(this.brokerURL, this.brokerOpts);

    this.client.on("connect", () => {
      logger.info(`🔌 Connected to MQTT broker at ${this.brokerURL}`);
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
      // this.publishDefaultProperties();
    });

    this.client.on("message", (topic, message) => {
      logger.info(`📩 [${topic}] ${message.toString()}`);
    });
  }

  private publish(value: unknown, opts: MqttFormOptions): void {
    if (opts.href !== this.brokerURL) {
      logger.error(`❌ Mismatched href: ${opts.href} != ${this.brokerURL}`);
      return;
    }

    this.client?.publish(opts.topic, JSON.stringify(value), {
      retain: opts.retain,
      qos: opts.qos,
    }, (err) => {
      if (err) {
        logger.error(`❌ Failed to publish to ${opts.topic}:`, err);
      } else {
        logger.info(`✅ Published to ${opts.topic}:`, value);
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
    for (const [name, prop] of Object.entries(this.td.properties ?? {})) {
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
        logger.warn(`⚠️ No MQTT config for property "${name}"`);
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
      this.td.forms,
      type,
      topLevelOP,
    );

    if (opts) {
      this.subscribeToTopic(topLevelOP, opts.topic, qos);
    } else {
      logger.warn(
        `⚠️ No MQTT config for top-level ${type} subscription. trying individual affordances.`,
      );
    }

    const op = type === "property" ? "observeproperty" : "subscribeevent";
    const entries = type === "property"
      ? Object.entries(this.td.properties ?? {})
      : Object.entries(this.td.events ?? {});

    for (const [name, obj] of entries) {
      if (ignore_prefix && name.startsWith(ignore_prefix)) {
        logger.debug(`Skipping ${type} "${name}" due to ignore prefix`);
        continue;
      }

      const opts = this.extractMqttOptions(obj.forms, type, op);
      if (opts) {
        this.subscribeToTopic(name, opts.topic, qos);
      } else {
        logger.warn(`⚠️ No MQTT config for ${type} "${name}"`);
      }
    }
  }

  private subscribeToTopic(name: string, topic: string, qos: 0 | 1 | 2): void {
    this.client?.subscribe(topic, { qos }, (err) => {
      if (err) {
        logger.error(`❌ Subscription failed for "${name}":`, err);
      } else {
        logger.info(`📡 Subscribed to "${name}" on topic "${topic}"`);
      }
    });
  }
}

export default Controller;

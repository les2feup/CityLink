import { mqtt, ThingDescription, UUID } from "../../deps.ts";

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
      console.log(`🔌 Connected to MQTT broker at ${this.brokerURL}`);
      this.subscribeToAll(
        "property",
        "observeproperty",
        this.controllerOpts.observePropertyQoS,
      );
      this.subscribeToAll(
        "event",
        "subscribeevent",
        this.controllerOpts.subscribeEventQos,
      );
      this.publishDefaultProperties();
    });

    this.client.on("message", (topic, message) => {
      console.log(`📩 [${topic}] ${message.toString()}`);
    });
  }

  private publish(value: unknown, opts: MqttFormOptions): void {
    if (opts.href !== this.brokerURL) {
      console.error(`❌ Mismatched href: ${opts.href} != ${this.brokerURL}`);
      return;
    }

    this.client?.publish(opts.topic, JSON.stringify(value), {
      retain: opts.retain,
      qos: opts.qos,
    }, (err) => {
      if (err) {
        console.error(`❌ Failed to publish to ${opts.topic}:`, err);
      } else {
        console.log(`✅ Published to ${opts.topic}:`, value);
      }
    });
  }

  private extractMqttOptions(
    affordanceType: "property" | "action" | "event",
    affordanceName: string,
    expectedOp: string,
  ): MqttFormOptions | null {
    const [forms, topicKey] = (() => {
      switch (affordanceType) {
        case "property":
          return [
            this.td.properties?.[affordanceName]?.forms ?? [],
            "mqv:filter",
          ];
        case "event":
          return [
            this.td.events?.[affordanceName]?.forms ?? [],
            "mqv:filter",
          ];
        case "action":
          return [this.td.actions?.[affordanceName]?.forms ?? [], "mqv:topic"];
      }
    })();

    if (!forms.length) return null;

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

      const opts = this.extractMqttOptions("property", name, "readproperty");
      if (opts) {
        this.publish(val, opts);
      } else {
        console.warn(`⚠️ No MQTT config for property "${name}"`);
      }
    }
  }

  private subscribeToAll(
    type: "property" | "event",
    op: string,
    qos: 0 | 1 | 2,
  ): void {
    const entries = type === "property"
      ? Object.entries(this.td.properties ?? {})
      : Object.entries(this.td.events ?? {});

    for (const [name] of entries) {
      const opts = this.extractMqttOptions(type, name, op);
      if (opts) {
        this.subscribeToTopic(name, opts.topic, qos);
      } else {
        console.warn(`⚠️ No MQTT config for ${type} "${name}"`);
      }
    }
  }

  private subscribeToTopic(name: string, topic: string, qos: 0 | 1 | 2): void {
    this.client?.subscribe(topic, { qos }, (err) => {
      if (err) {
        console.error(`❌ Subscription failed for "${name}":`, err);
      } else {
        console.log(`📡 Subscribed to "${name}" on topic "${topic}"`);
      }
    });
  }
}

export default Controller;

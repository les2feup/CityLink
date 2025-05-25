import { Buffer, mqtt, ThingDescription, UUID } from "../../deps.ts";
import { getLogger } from "../utils/log/log.ts";
const logger = getLogger();

export type InstantiationOpts = {
  endNodeUUID: UUID;
  protocol: "mqtt" | "http" | "coap";
  extra?: {
    [key: string]: string; // custom fields
  };
};
type Callback<T = void> = (arg: T) => void;
type CancelSubscription = () => void;

export function subscribeEvent(
  td: ThingDescription,
  event: string,
  onEvent: (topic: string, message: Buffer) => void,
  onSubscribe?: Callback<string>,
  onError?: Callback<Error>,
  subscribeOpts?: { qos?: 0 | 1 | 2 },
): Error | CancelSubscription {
  const eventDef = td.events?.[event];
  const eventForm = eventDef?.forms?.[0];

  if (!eventForm) {
    return new Error(`No valid form found for event "${event}"`);
  }

  const brokerUrl = eventForm.href;
  const topic = eventForm["mqv:filter"] as string;
  if (!topic) {
    return new Error(`Missing topic ("mqv:filter") for event "${event}"`);
  }

  const client = mqtt.connect(brokerUrl);
  let isSubscribed = false;
  let isTerminated = false;

  const qos = subscribeOpts?.qos ?? 0;
  client.on("connect", () => {
    client.subscribe(topic, { qos }, (err) => {
      if (err) {
        onError?.(err);
        client.end();
        isTerminated = true;
        return;
      }

      isSubscribed = true;
      logger.debug(
        `Subscribed to "${topic}" for event "${event}" in TD "${td.id}"`,
      );
      onSubscribe?.(topic);
    });
  });

  client.on("message", (receivedTopic, message) => {
    onEvent(receivedTopic, message);
  });

  client.on("error", (err) => {
    logger.error("MQTT error:", err);
    onError?.(err);
  });

  const cancelSubscription: CancelSubscription = () => {
    if (isTerminated || !isSubscribed) {
      logger.warn(
        `Cannot cancel subscription: either already ended or not active for event "${event}"`,
      );
      client.end();
      return;
    }

    client.unsubscribe(topic, (err) => {
      if (err) {
        logger.error(`Failed to unsubscribe from topic "${topic}":`, err);
      } else {
        logger.info(`Unsubscribed from topic "${topic}"`);
      }
      client.end();
      isTerminated = true;
    });
  };

  return cancelSubscription;
}

export function invokeAction(
  td: ThingDescription,
  action: string,
  input: string | Buffer,
  onPublish?: Callback<string>,
  onError?: Callback<Error>,
): Error | null {
  const actionDef = td.actions?.[action];
  const actionForm = actionDef?.forms?.[0];
  if (!actionForm) {
    return new Error(`No valid form found for action "${action}"`);
  }

  const qos = (actionForm["mqv:qos"] as 0 | 1 | 2) ?? 0;
  const retain = (actionForm["mqv:retain"] as boolean) ?? false;
  const topic = actionForm["mqv:topic"] as string;
  if (!topic) {
    return new Error(`Missing topic ("mqv:topic") for action "${action}"`);
  }

  logger.debug("Initiating MQTT client for action:", action);

  const brokerUrl = actionForm.href;
  const client = mqtt.connect(brokerUrl);
  client.on("connect", () => {
    logger.debug(
      `Connected to MQTT broker on ${actionForm.href} for action:`,
      action,
    );
    client.publish(topic, input, { qos, retain }, (err) => {
      if (err) {
        onError?.(err);
      } else {
        onPublish?.(topic);
        logger.info(`Published to topic "${topic}" for action "${action}"`);
      }
      client.end();
    });
  });

  client.on("error", (err) => {
    logger.error("MQTT error:", err);
    onError?.(err);
    client.end();
  });

  return null;
}

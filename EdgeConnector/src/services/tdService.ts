import {
  Buffer,
  CompositionOptions,
  mqtt,
  ThingDescription,
  ThingModel,
  ThingModelHelpers,
  UUID,
} from "../../deps.ts";
import { createTemplateMapMQTT } from "./../models/templateMaps/mqttTemplateMap.ts";
import { MQTT_BROKER_URL } from "./../config/config.ts";

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
      console.debug(
        `Subscribed to "${topic}" for event "${event}" in TD "${td.id}"`,
      );
      onSubscribe?.(topic);
    });
  });

  client.on("message", (receivedTopic, message) => {
    onEvent(receivedTopic, message);
  });

  client.on("error", (err) => {
    console.error("MQTT error:", err);
    onError?.(err);
  });

  const cancelSubscription: CancelSubscription = () => {
    if (isTerminated || !isSubscribed) {
      console.warn(
        `Cannot cancel subscription: either already ended or not active for event "${event}"`,
      );
      client.end();
      return;
    }

    client.unsubscribe(topic, (err) => {
      if (err) {
        console.error(`Failed to unsubscribe from topic "${topic}":`, err);
      } else {
        console.log(`Unsubscribed from topic "${topic}"`);
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

  console.debug("Initiating MQTT client for action:", action);

  const brokerUrl = actionForm.href;
  const client = mqtt.connect(brokerUrl);
  client.on("connect", () => {
    console.debug(
      `Connected to MQTT broker on ${actionForm.href} for action:`,
      action,
    );
    client.publish(topic, input, { qos, retain }, (err) => {
      if (err) {
        onError?.(err);
      } else {
        onPublish?.(topic);
        console.log(`Published to topic "${topic}" for action "${action}"`);
      }
      client.end();
    });
  });

  client.on("error", (err) => {
    console.error("MQTT error:", err);
    onError?.(err);
    client.end();
  });

  return null;
}

export async function produceTD(
  model: ThingModel,
  opts: InstantiationOpts,
): Promise<ThingDescription | Error> {
  const tmTools = new ThingModelHelpers();
  if (!model.title) {
    return new Error("Model title is missing");
  }

  const map = getTemplateMap(opts);
  if (map instanceof Error) {
    return map;
  }

  const options: CompositionOptions = {
    map,
    selfComposition: true,
  };

  try {
    const [partialTD] = await tmTools.getPartialTDs(model, options);
    partialTD.id = map.CITYLINK_ID;

    console.log(
      `New Thing Description id "${partialTD.id}" registered for model "${model.title}"`,
    );

    return fillPlatfromForms(partialTD, map);
  } catch (error) {
    if (error instanceof Error) {
      return new Error(
        `Error during TD instantiation: ${error.message}`,
      );
    } else {
      return new Error("Unknown error during TD instantiation");
    }
  }
}

function getTemplateMap(
  opts: InstantiationOpts,
): Record<string, string> | Error {
  switch (opts.protocol) {
    case "mqtt": {
      const baseMap = createTemplateMapMQTT(
        MQTT_BROKER_URL,
        opts.endNodeUUID,
      );
      if (baseMap instanceof Error) {
        return baseMap;
      }

      return {
        ...baseMap,
        ...opts.extra,
      };
    }
    case "http":
      return new Error("HTTP protocol is not supported yet");
    case "coap":
      return new Error("CoAP protocol is not supported yet");
    default:
      return new Error(
        `Unsupported protocol: ${opts.protocol}`,
      );
  }
}

//TODO: These properties should be published to the broker
//      with the retain flag set to true and qos set to 2.
//      Afterwards there is no need to publish them again.
//      Either that or remove the form from the TD since all
//      these properties **should** be read-only constants.
function fillPlatfromForms(
  td: WoT.ExposedThingInit,
  map: Record<string, string>,
): ThingDescription {
  const merge = (prop_name: string) => {
    return {
      readOnly: true,
      writeOnly: false,
      forms: [
        {
          href: map.CITYLINK_HREF,
          "mqv:filter": `${map.CITYLINK_PROPERTY}/platform/${prop_name}`,
          "mqv:qos": 2,
          "mqv:retain": true,
          op: [
            "readProperty",
            "subscribeProperty",
            "unsubscribeProperty",
          ],
          contentType: "application/json",
        },
      ],
    };
  };

  const properties = td.properties!;
  const prefix = "citylink:platform_";
  // map over properties that start with the citylink:platfrom prefix
  // citylink:platform_<prop_name> and apply the merge
  for (const key of Object.keys(properties)) {
    if (key.startsWith(prefix) && !properties[key]?.forms) {
      const actualPropName = key.slice(prefix.length);
      const merged = merge(actualPropName);
      const original = properties[key]!;

      // Merge values (non-destructively)
      properties[key] = {
        ...original,
        ...merged,
        forms: [...(original.forms ?? []), ...merged.forms],
      };

      console.log("Filled platform form for", actualPropName, "in TD", td.id);
    }
  }

  return td as ThingDescription;
}

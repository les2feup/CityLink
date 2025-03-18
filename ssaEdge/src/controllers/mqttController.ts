import { mqtt, ThingModelHelpers } from "../../deps.ts";
import {
  MODEL_HOST_ADDR,
  MQTT_BROKER_ADDR,
} from "../config/config.ts";
import { createThingFromModel } from "../services/thingModelService.ts";

import type { Buffer, ThingDescription } from "../../deps.ts";
import type { RegistrationPayload } from "../models/registration.ts";

/**
 * Sets up the MQTT connection and subscribes to the registration topic.
 */
export function setupMQTT(
  tmTools: ThingModelHelpers,
  hostedThings: Map<string, Map<string, ThingDescription>>,
): void {
  const client = mqtt.connect(`mqtt://${MQTT_BROKER_ADDR}`);

  client.on("connect", () => {
    client.subscribe("registration/#", (err) => {
      if (err) {
        console.error("Error subscribing to registration topic:", err);
        // Emit an event or implement a retry mechanism
        // For example:
        setTimeout(() => setupMQTT(tmTools, hostedThings), 5000); // Retry after 5 seconds
        return;
      }
      console.log(
        "Connected to MQTT broker and subscribed to registration topic",
      );
    });
  });

  client.on("message", (topic: string, message: Buffer) => {
    handleRegistrationMessage(tmTools, hostedThings, topic, message);
  });

  client.on("error", (error: Error) => {
    console.error("MQTT client encountered an error:", error);
  });
}

/**
 * Processes and registers an incoming MQTT registration message.
 *
 * This asynchronous function validates the message received on a topic formatted as
 * "registration/{uuid}", ensuring that the UUID in the topic matches the one in the JSON
 * payload and that the payload includes both a "model" and "version". It then fetches the
 * corresponding model using the provided helper, constructs a Thing Description (TD), and
 * registers it in the collection of hosted things.
 *
 * @param tmTools An instance of ThingModelHelpers used to retrieve the device model.
 * @param hostedThings A map organizing registered Thing Descriptions by model and UUID.
 * @param topic The MQTT topic from which the message was received, expected in "registration/{uuid}" format.
 * @param message The message payload as a Buffer containing JSON registration data.
 */
async function handleRegistrationMessage(
  tmTools: ThingModelHelpers,
  hostedThings: Map<string, Map<string, WoT.ThingDescription>>,
  topic: string,
  message: Buffer,
): Promise<void> {
  console.log(`Received message on topic ${topic}: ${message.toString()}`);
  const parts = topic.split("/");
  if (parts.length !== 2 || parts[0] !== "registration") {
    console.error("Invalid topic format:", topic);
    return;
  }

  const topicUuid = parts[1];
  let payload: RegistrationPayload;
  try {
    payload = JSON.parse(message.toString());
  } catch (error) {
    console.error("Error parsing MQTT message payload:", error);
    return;
  }

  if (topicUuid !== payload.uuid) {
    console.error("UUID mismatch between topic and payload:", {
      topicUuid,
      payloadUuid: payload.uuid,
    });
    return;
  }
  if (!payload.model) {
    console.error("Registration payload missing 'model' property");
    return;
  }
  if (payload.version === undefined) {
    console.error("Registration payload missing 'version' property");
    return;
  }

  const map = {
    THING_UUID_V4: payload.uuid,
    MQTT_BROKER_ADDR: MQTT_BROKER_ADDR,
    THING_REGISTRY_ADDR: "http://localhost:8080",
  };

  try {
    const model_uri = `http://${MODEL_HOST_ADDR}/models/${payload.model}`;
    const model = await tmTools.fetchModel(model_uri);
    const td = await createThingFromModel(tmTools, model, map);
    console.log(`Created TD from model: ${td.title}`);

    let modelMap = hostedThings.get(payload.model);
    if (!modelMap) {
      modelMap = new Map<string, ThingDescription>();
      hostedThings.set(payload.model, modelMap);
    }
    modelMap.set(payload.uuid, td);
    console.log(`Hosted thing registered: ${td.title}:${td.id}`);
  } catch (error) {
    console.error("Error during Thing creation:", error);
  }
}

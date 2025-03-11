import { mqtt, ThingModelHelpers } from "../../deps.ts";
import {
  HTTP_HOSTNAME,
  HTTP_PORT,
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
        Deno.exit(1);
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
    THING_MODEL: payload.model,
    THING_UUID_V4: payload.uuid,
    MQTT_BROKER_ADDR: MQTT_BROKER_ADDR,
  };

  try {
    const model_uri =
      `http://${HTTP_HOSTNAME}:${HTTP_PORT}/models/${payload.model}`;
    const model = await tmTools.fetchModel(model_uri);
    const td = await createThingFromModel(tmTools, model, map);
    console.log(`Created TD from model: ${td.title}`);

    let modelMap = hostedThings.get(payload.model);
    if (!modelMap) {
      modelMap = new Map<string, ThingDescription>();
      hostedThings.set(payload.model, modelMap);
    }
    modelMap.set(payload.uuid, td);
    console.log(`Hosted thing registered: ${td.title}`);
  } catch (error) {
    console.error("Error during Thing creation:", error);
  }
}

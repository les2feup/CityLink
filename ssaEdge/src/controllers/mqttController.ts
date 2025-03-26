import { mqtt, randomUUID, ThingModelHelpers } from "../../deps.ts";
import { MQTT_BROKER_ADDR } from "../config/config.ts";
import { createThingFromModel } from "../services/thingModelService.ts";

import type { Buffer, ThingDescription, ThingModel } from "../../deps.ts";
import type { RegistrationPayload } from "../models/registration.ts";

/**
 * Sets up the MQTT connection and subscribes to the registration topic.
 */
export function setupMQTT(
  tmTools: ThingModelHelpers,
  hostedModels: Map<string, ThingModel>,
  hostedThings: Map<string, Map<string, ThingDescription>>,
): void {
  const client = mqtt.connect(`mqtt://${MQTT_BROKER_ADDR}`);

  client.on("connect", () => {
    client.subscribe("ssa/+/registration", (err) => {
      if (err) {
        console.error("Error subscribing to registration topic:", err);
        // Emit an event or implement a retry mechanism
        // For example:
        setTimeout(() => setupMQTT(tmTools, hostedModels, hostedThings), 5000); // Retry after 5 seconds
        return;
      }
      console.log(
        "Connected to MQTT broker and subscribed to registration topic",
      );
    });
  });

  client.on("message", (topic: string, message: Buffer) => {
    handleRegistrationMessage(
      client,
      tmTools,
      hostedModels,
      hostedThings,
      topic,
      message,
    );
  });

  client.on("error", (error: Error) => {
    console.error("MQTT client encountered an error:", error);
  });
}

function parseAndValidatePayload(
  message: Buffer,
): RegistrationPayload | Error {
  let payload: RegistrationPayload;

  try {
    payload = JSON.parse(message.toString());
  } catch (error) {
    return new Error("Error parsing registration payload as JSON: " + error);
  }

  if (!payload.name) {
    return new Error("Registration payload 'name' property is missing");
  }

  if (!payload.href) {
    console.error("Registration payload missing 'href' property");
    return new Error("Registration payload 'href' property is missing");
  }

  if (!payload.version || !payload.version.instance || !payload.version.model) {
    return new Error("Registration payload 'version' is missing or invalid");
  }

  return payload;
}

async function getThingModel(
  modelName: string,
  modelHref: string,
  hostedModels: Map<string, ThingModel>,
  tmTools: ThingModelHelpers,
): Promise<ThingModel> {
  let model = hostedModels.get(modelName);
  if (model) {
    return model;
  }

  //TODO: Setting a timeout for fetching the model
  model = await tmTools.fetchModel(modelHref);
  if (!model.title) {
    model.title = modelName;
  }

  hostedModels.set(model.title, model);
  return model;
}

async function instantiateThing(
  thingUUID: string,
  model: ThingModel,
  tmTools: ThingModelHelpers,
  hostedThings: Map<string, Map<string, ThingDescription>>,
) {
  if (!model.title) {
    throw new Error("Model title is missing");
  }

  const map = {
    THING_UUID_V4: thingUUID,
    MQTT_BROKER_ADDR: MQTT_BROKER_ADDR,
  };

  const td = await createThingFromModel(tmTools, model, map);
  console.log(`Created TD from model: ${td.title}`);

  let modelMap = hostedThings.get(model.title);
  if (!modelMap) {
    modelMap = new Map<string, ThingDescription>();
    hostedThings.set(model.title, modelMap);
  }

  modelMap.set(thingUUID, td);
  console.log(`Hosted thing registered: ${td.title}:${td.id}`);
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
  client: mqtt.MqttClient,
  tmTools: ThingModelHelpers,
  hostedModels: Map<string, ThingModel>,
  hostedThings: Map<string, Map<string, WoT.ThingDescription>>,
  topic: string,
  message: Buffer,
): Promise<void> {
  console.log(`Received message on topic ${topic}: ${message.toString()}`);
  const parts = topic.split("/");
  if (parts.length !== 3 || parts[0] !== "ssa" || parts[2] !== "registration") {
    console.error("Invalid topic format:", topic);
    return;
  }

  const thingID = parts[1];
  const thingUUID = randomUUID();

  try {
    const payload = parseAndValidatePayload(message);
    if (payload instanceof Error) {
      throw payload;
    }

    const model = await getThingModel(
      payload.name,
      payload.href,
      hostedModels,
      tmTools,
    );

    await instantiateThing(thingUUID, model, tmTools, hostedThings);
    client.publish(
      `ssa/${thingID}/registration/ack`,
      JSON.stringify({ status: "", id: thingUUID }),
    );
  } catch (error: unknown) {
    let message: string = "Unknown error during Thing creation";
    if (error instanceof Error) {
      message = error.message;
    } else if (typeof error === "string") {
      message = error;
    }

    console.error("Error during Thing creation:", error);
    client.publish(
      `ssa/${thingID}/registration/ack`,
      JSON.stringify({ status: "error", message }),
    );
  }
}

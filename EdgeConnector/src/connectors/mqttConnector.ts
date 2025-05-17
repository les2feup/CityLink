import { MQTT_BROKER_ADDR } from "../config/config.ts";
import { fetchAppManifest } from "../services/appManifestService.ts";
import { RegistrationPayload } from "../models/registration.ts";
import { mqtt, randomUUID, ThingModelHelpers } from "../../deps.ts";
import type { Buffer, ThingDescription, ThingModel } from "../../deps.ts";
import {
  fetchThingModel,
  instantiateTDs,
} from "../services/thingModelService.ts";

/**
 * Sets up the MQTT connection and subscribes to the registration topic.
 */
export function launch(
  tmTools: ThingModelHelpers,
  hostedModels: Map<string, ThingModel>,
  hostedThings: Map<string, Map<string, ThingDescription>>,
  onError?: (error: Error) => void,
): void {
  const client = mqtt.connect(`${MQTT_BROKER_ADDR}`);

  client.on("connect", () => {
    client.subscribe("citylink/+/registration", (err) => {
      if (err) {
        console.error("Error subscribing to registration topic:", err);
        // Emit an event or implement a retry mechanism
        // For example:
        setTimeout(
          () => launch(tmTools, hostedModels, hostedThings),
          5000,
        ); // Retry after 5 seconds
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
    if (onError) {
      onError(error);
    }
  });
}

function parseRegistrationMessage(
  message: Buffer,
): RegistrationPayload | Error {
  const json = JSON.parse(message.toString());
  const parsed = RegistrationPayload.safeParse(json);

  if (!parsed.success) {
    return new Error(
      `Invalid registration payload: ${
        JSON.stringify(parsed.error.issues, null, 2)
      }`,
    );
  }

  return parsed.data;
}

async function instantiateTD(
  thingUUID: string,
  model: ThingModel,
  tmTools: ThingModelHelpers,
  hostedThings: Map<string, Map<string, ThingDescription>>,
) {
  if (!model.title) {
    throw new Error("Model title is missing");
  }

  //TODO: Add support for a custom template map received from the registration payload.
  const map = {
    CITYLINK_ID: `urn:uuid:${thingUUID}`,
    CITYLINK_HREF: MQTT_BROKER_ADDR,
    CITYLINK_PROPERTY: `citylink/${thingUUID}/properties`,
    CITYLINK_ACTION: `citylink/${thingUUID}/actions`,
    CITYLINK_EVENT: `citylink/${thingUUID}/events`,
  };

  let modelMap = hostedThings.get(model.title);
  if (!modelMap) {
    modelMap = new Map<string, ThingDescription>();
    hostedThings.set(model.title, modelMap);
  }

  const thingDescriptions = await instantiateTDs(tmTools, model, map);
  thingDescriptions.forEach((td, index) => {
    if (!td.title) {
      throw new Error("Thing Description title is missing");
    }
    td.id = `${map.CITYLINK_ID}${(index > 0) ? `:submodel:${index}` : ""}`;
    modelMap.set(td.id, td);
    console.log(
      `New Thing Description registered: title ${td.title} id ${td.id}`,
    );
  });
}

async function handleRegistrationMessage(
  client: mqtt.MqttClient,
  tmTools: ThingModelHelpers,
  hostedModels: Map<string, ThingModel>,
  hostedThings: Map<string, Map<string, ThingDescription>>,
  topic: string,
  message: Buffer,
): Promise<void> {
  console.log(`Received message on topic ${topic}: ${message.toString()}`);
  const parts = topic.split("/");
  if (
    parts.length !== 3 || parts[0] !== "citylink" || parts[2] !== "registration"
  ) {
    console.error("Invalid topic format:", topic);
    return;
  }

  const endNodeID = parts[1];
  const generatedUUID = randomUUID();

  try {
    const payload = parseRegistrationMessage(message);
    if (payload instanceof Error) {
      throw payload;
    }

    const manifest = await fetchAppManifest(payload.manifest);
    if (manifest instanceof Error) {
      throw manifest;
    }

    const model = await fetchThingModel(tmTools, manifest.wot.tm);
    if (model instanceof Error) {
      throw model;
    }

    await instantiateTD(generatedUUID, model, tmTools, hostedThings);
    client.publish(
      `citylink/${endNodeID}/registration/ack`,
      JSON.stringify({ status: "sucess", id: generatedUUID }),
    );
  } catch (error: unknown) {
    let message: string = "Unknown error during Thing creation";
    if (error instanceof Error) {
      message = error.message;
    } else if (typeof error === "string") {
      message = error;
    }

    console.error("Error during Thing creation:", message);
    client.publish(
      `citylink/${endNodeID}/registration/ack`,
      JSON.stringify({ status: "error", message }),
    );
  }
}

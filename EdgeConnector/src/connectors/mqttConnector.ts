import { MQTT_BROKER_URL } from "../config/config.ts";
import { RegistrationSchema } from "../models/registrationSchema.ts";
import { fetchThingModel } from "../services/tmService.ts";
import { instantiateTDs, InstantiationOpts } from "../services/tdService.ts";
import { Buffer, mqtt, randomUUID } from "../../deps.ts";
import {
  fetchAppManifest,
  fetchAppSrc,
  FetchError,
  FetchResult,
  FetchSuccess,
} from "../services/appManifestService.ts";

export function init(
  onError?: (error: Error) => void,
): void {
  const client = mqtt.connect(`${MQTT_BROKER_URL}`);

  client.on("connect", () => {
    client.subscribe("citylink/+/registration", (err) => {
      if (err) {
        console.error("Error subscribing to registration topic:", err);
        // Emit an event or implement a retry mechanism
        // For example:
        setTimeout(
          () => init(onError),
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
): RegistrationSchema | Error {
  const json = JSON.parse(message.toString());
  const parsed = RegistrationSchema.safeParse(json);

  if (!parsed.success) {
    return new Error(
      `Invalid registration payload: ${
        JSON.stringify(parsed.error.issues, null, 2)
      }`,
    );
  }

  return parsed.data;
}

async function handleRegistrationMessage(
  client: mqtt.MqttClient,
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
    console.log("App manifest retrieved sucessfully");

    const model = await fetchThingModel(manifest.wot.tm);
    if (model instanceof Error) {
      throw model;
    }
    console.log("Thing model retrieved sucessfully");

    if (!payload.tmOnly) {
      const results: FetchResult[] = await fetchAppSrc(manifest.download);
      const fetchErrors = results.filter(
        (r): r is FetchError => "error" in r,
      );

      if (fetchErrors.length > 0) {
        throw new Error(
          `Error fetching app source: ${
            fetchErrors
              .map((r) => `${r.url}: ${r.error.message}`)
              .join(", ")
          }`,
        );
      }

      const fetchSuccess = results.filter(
        (r): r is FetchSuccess => "name" in r && "content" in r,
      );

      fetchSuccess.forEach((result) => {
        console.log(
          `Fetched ${result.name} from ${result.url} with content type ${typeof result
            .content}`,
        );
      });
    }

    const opts: InstantiationOpts = [{
      endNodeUUID: generatedUUID,
      selfComposition: false,
      protocol: "mqtt",
    }];

    //TODO: maybe tds should be returned instead of cached directly
    const errors = await instantiateTDs(model, opts);
    if (errors) {
      throw new Error(
        `Error during TD instantiation: ${
          errors.map((e) => e.message).join(", ")
        }`,
      );
    }
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

export default {
  init,
};

import { Buffer, mqtt } from "../../../deps.ts";
import { RegistrationSchema } from "../../models/registrationSchema.ts";
import { fetchAppManifest } from "../../services/appManifestService.ts";
import { fetchThingModel } from "../../services/tmService.ts";
import { InstantiationOpts, produceTD } from "../../services/tdService.ts";
import cache from "../../services/cacheService.ts";

async function handler(
  client: mqtt.MqttClient,
  endNodeID: string,
  message: Buffer,
): Promise<void> {
  // Check if endNodeID is already registered
  const isRegistered = cache.getTDbyUUID(endNodeID);
  if (isRegistered) {
    console.log(
      `End node ${endNodeID} is already registered. Ignoring registration message.`,
    );
    return;
  }

  const parsed = RegistrationSchema.safeParse(message);
  if (!parsed.success) {
    throw new Error(
      `Invalid registration payload: ${
        JSON.stringify(parsed.error.issues, null, 2)
      }`,
    );
  }

  const regData = parsed.data;
  const manifest = await fetchAppManifest(regData.manifest);
  if (manifest instanceof Error) {
    throw manifest;
  }

  const model = await fetchThingModel(manifest.wot.tm);
  if (model instanceof Error) {
    throw model;
  }

  const opts: InstantiationOpts = {
    endNodeUUID: crypto.randomUUID(),
    protocol: "mqtt",
  };

  const td = await produceTD(model, opts);
  if (td instanceof Error) {
    throw new Error(`Error during TD instantiation: ${td.message}`);
  }

  //NOTE: maybe create a different cache for TDs that are waiting for adaptation
  cache.setTD(model.title!, td.id!, td);
  client.publish(
    `citylink/${endNodeID}/registration/ack`,
    JSON.stringify({ status: "success", id: opts.endNodeUUID }),
  );

  if (regData.tmOnly) {
    return;
  }

  // TODO: trigger the adaptation job
}

export async function registrationHandler(
  client: mqtt.MqttClient,
  endNodeID: string,
  message: Buffer,
): Promise<void> {
  try {
    await handler(client, endNodeID, message);
  } catch (e) {
    const message = e instanceof Error ? e.message : "Unknown error";
    client.publish(
      `citylink/${endNodeID}/registration/ack`,
      JSON.stringify({ status: "error", message }),
    );
    throw e;
  }
}

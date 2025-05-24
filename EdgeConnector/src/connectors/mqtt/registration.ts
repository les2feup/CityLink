import { Buffer, mqtt, UUID } from "../../../deps.ts";
import { RegistrationSchema } from "../../models/registrationSchema.ts";
import { fetchAppManifest } from "../../services/appManifestService.ts";
import { fetchThingModel } from "../../services/tmService.ts";
import { InstantiationOpts, produceTD } from "../../services/tdService.ts";
import cache from "../../services/cacheService.ts";

import umqttCore from "../../controllers/umqttCore.ts";

type RegistrationAck = {
  status: "success" | "error" | "ack";
  id?: UUID; // Optional ID for success responses
  message?: string; // Optional error message for error responses
};

async function handler(
  endNodeID: string | UUID,
  message: Buffer,
): Promise<RegistrationAck> {
  // Check if endNodeID is already registered
  if (cache.getEndNode(endNodeID as UUID)) {
    console.log(
      `End node ${endNodeID} is already registered.`,
    );

    return { status: "ack" };
  }

  const json = JSON.parse(message.toString());
  const parsed = RegistrationSchema.safeParse(json);
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

  const tm = await fetchThingModel(manifest.wot.tm);
  if (tm instanceof Error) {
    throw tm;
  }

  const opts: InstantiationOpts = {
    endNodeUUID: crypto.randomUUID(),
    protocol: "mqtt",
  };

  const td = await produceTD(tm, opts);
  if (td instanceof Error) {
    throw new Error(`Error during TD instantiation: ${td.message}`);
  }

  cache.insertEndNode(opts.endNodeUUID, manifest, tm, td);

  return { status: "success", id: opts.endNodeUUID };
}

export async function registrationHandler(
  client: mqtt.MqttClient,
  endNodeID: string | UUID,
  message: Buffer,
): Promise<UUID | Error> {
  const ack = (a: RegistrationAck) => {
    client.publish(
      `citylink/${endNodeID}/registration/ack`,
      JSON.stringify(a),
    );
  };

  try {
    const res = await handler(endNodeID, message);
    ack(res);
    return res.id || endNodeID as UUID;
  } catch (e) {
    const message = e instanceof Error ? e.message : "Unknown error";
    const err = e instanceof Error ? e : new Error(message);
    ack({ status: "error", message });
    return err;
  }
}

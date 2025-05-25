import { Buffer, mqtt, UUID } from "../../../deps.ts";
import { RegistrationSchema } from "../../models/registrationSchema.ts";
import { fetchAppManifest } from "../../services/appManifestService.ts";
import { fetchThingModel } from "../../utils/tm.ts";
import { InstantiationOpts, produceTD } from "../../utils/td.ts";
import cache from "../../services/cache.ts";
import { getLogger } from "../../utils/log/log.ts";
import { MqttConnectorOpts } from "./connector.ts";
import umqttCore from "../../controllers/umqttCore.ts";

type RegistrationAck = {
  status: "success" | "error" | "ack";
  id?: UUID; // Optional ID for success responses
  message?: string; // Optional error message for error responses
};

async function handler(
  endNodeID: string | UUID,
  message: Buffer,
  brokerUrl: string,
): Promise<RegistrationAck> {
  const logger = getLogger(import.meta.url);
  // Check if endNodeID is already registered
  const node = cache.getEndNode(endNodeID as UUID);
  if (node) {
    logger.info(
      `End node ${endNodeID} is already registered.`,
    );

    if (!node.controller) {
      logger.info(
        `Launching controller for end node ${endNodeID}.`,
      );
      launchNodeController(endNodeID as UUID, { url: brokerUrl });
    }

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
  launchNodeController(endNodeID as UUID, { url: brokerUrl });

  return { status: "success", id: opts.endNodeUUID };
}

export async function registrationHandler(
  client: mqtt.MqttClient,
  endNodeID: string | UUID,
  message: Buffer,
  opts: MqttConnectorOpts,
): Promise<UUID | Error> {
  const ack = (a: RegistrationAck) => {
    client.publish(
      `citylink/${endNodeID}/registration/ack`,
      JSON.stringify(a),
    );
  };

  try {
    const res = await handler(endNodeID, message, opts.url);
    ack(res);
    return res.id || endNodeID as UUID;
  } catch (e) {
    const message = e instanceof Error ? e.message : "Unknown error";
    const err = e instanceof Error ? e : new Error(message);
    ack({ status: "error", message });
    return err;
  }
}

function launchNodeController(
  nodeId: UUID,
  opts: MqttConnectorOpts,
) {
  const logger = getLogger(import.meta.url);
  const node = cache.getEndNode(nodeId);
  if (!node) {
    logger.error(`Node with ID ${nodeId} not found in cache.`);
    return;
  }
  if (node.controller) {
    logger.warn(`Node with ID ${nodeId} already has a controller.`);
    return;
  }

  const controller = new umqttCore(nodeId, node.td, opts.url);
  controller.launch();
  cache.updateEndNode(nodeId, { controller });
  logger.info(`Node controller launched for node ID ${nodeId}`);
}

import { Buffer, mqtt, UUID } from "../../../deps.ts";
import { RegistrationSchema } from "../../models/registrationSchema.ts";
import { fetchAppManifest } from "../../services/appManifestService.ts";
import { fetchThingModel } from "../../utils/tm.ts";
import { InstantiationOpts, produceTD } from "../../utils/td.ts";
import { getLogger } from "../../utils/log/log.ts";
import { MqttConnectorOpts } from "./connector.ts";
import umqttCore from "../../controllers/umqttCore.ts";
import cache from "../../services/cache.ts";

const idsInProgress = new Set<UUID | string>();

type RegistrationAck = {
  status: "success" | "error" | "ack";
  id?: UUID; // Optional ID for success responses
  message?: string; // Optional error message for error responses
};

async function handler(
  preRegisterID: string | UUID,
  message: Buffer,
  brokerUrl: string,
): Promise<RegistrationAck> {
  idsInProgress.add(preRegisterID as UUID);

  const logger = getLogger(import.meta.url);
  const node = cache.getEndNode(preRegisterID as UUID);
  if (node) {
    logger.info(
      `End node ${preRegisterID} is already registered.`,
    );

    if (!node.controller) {
      logger.info(
        `Launching controller for end node ${preRegisterID}.`,
      );
      launchNodeController(preRegisterID as UUID, { url: brokerUrl });
    }

    return { status: "success" };
  }

  logger.info(`Registering end node ${preRegisterID}.`);

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

  logger.info(`📥 Fetching manifest for end node ${preRegisterID}.`);
  const manifest = await fetchAppManifest(regData.manifest);
  if (manifest instanceof Error) {
    throw manifest;
  }

  logger.info(`📥 Fetching thing model for end node ${preRegisterID}.`);
  const tm = await fetchThingModel(manifest.wot.tm);
  if (tm instanceof Error) {
    throw tm;
  }

  const opts: InstantiationOpts = {
    endNodeUUID: crypto.randomUUID(),
    protocol: "mqtt",
  };

  logger.info(
    `⚙️ Instantiating Thing Description for end node ${preRegisterID}.`,
  );
  const td = await produceTD(tm, opts);
  if (td instanceof Error) {
    throw new Error(`Error during TD instantiation: ${td.message}`);
  }

  cache.insertEndNode(opts.endNodeUUID, manifest, tm, td);
  launchNodeController(opts.endNodeUUID, { url: brokerUrl });

  return { status: "success", id: opts.endNodeUUID };
}

export async function registrationHandler(
  client: mqtt.MqttClient,
  endNodeID: string | UUID,
  message: Buffer,
  opts: MqttConnectorOpts,
): Promise<UUID | Error> {
  const reply = (a: RegistrationAck) => {
    client.publish(
      `citylink/${endNodeID}/registration/ack`,
      JSON.stringify(a),
    );
  };

  //TODO: ack as in progress
  if (idsInProgress.has(endNodeID)) {
    return new Error(`Registration of ${endNodeID} is already in progress.`);
  }

  reply({ status: "ack" });

  try {
    const res = await handler(endNodeID, message, opts.url);
    reply(res);
    idsInProgress.delete(endNodeID);
    return res.id || endNodeID as UUID;
  } catch (e) {
    const message = e instanceof Error ? e.message : "Unknown error";
    const err = e instanceof Error ? e : new Error(message);

    reply({ status: "error", message });
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
    logger.error(
      `Cannot launch controller for node ID ${nodeId}: Node not found.`,
    );
    return;
  }
  if (node.controller) {
    logger.warn(
      `Cannot launch controller for node ID ${nodeId}: Controller already exists.`,
    );
    return;
  }

  logger.info(`🚀 Launching controller for node ID ${nodeId}.`);
  const controller = new umqttCore(nodeId, node, opts.url);
  controller.launch();

  cache.updateEndNode(nodeId, { controller });
}

import { AppContentTypes } from "./../models/appManifest.ts";
import cache from "./../services/cacheService.ts";
import {
  mqtt,
  MqttClientFactory,
  Servient,
  ThingDescription,
} from "../../deps.ts";

const endNodeCleanupLists = new Map<string, string[]>();

const servient = new Servient();
servient.addClientFactory(new MqttClientFactory());

export function performEndNodeAdaptation(
  endNodeUUID: string,
  _source: { filename: string; content: AppContentTypes }[],
): Error | null {
  console.log(`Adapting end node "${endNodeUUID}"...`);

  const td = cache.getTDbyUUID(`urn:uuid:${endNodeUUID}`);
  if (!td) {
    return new Error(
      `td for end node with UUID "${endNodeUUID}" not found.`,
    );
  }

  console.log(`Found TD for end node "${endNodeUUID}" with UUID "${td.id}".`);

  servient.start().then(async (WoT) => {
    const thing = await WoT.consume(td);
    const consumedTD = thing.getThingDescription();
    console.log("==== Consumed TD ====");
    console.log(JSON.stringify(consumedTD, null, 2));
    console.log("======================");

    // TODO: fetch and consume the TD for the embeddedCore in order to
    // perform the correct VFSoperations
  }).catch((error) => {
    console.error("Servient error:", error);
  });

  // const cleanupList = endNodeCleanupLists.get(endNodeUUID);
  // if (cleanupList) {
  //   deleteEndNodeFiles(client, endNodeUUID, cleanupList);
  // }

  return null;
}

function deleteEndNodeFiles(
  _client: mqtt.MqttClient,
  _endNodeUUID: string,
  cleanupList: string[],
): void {
  if (cleanupList) {
    for (const _file of cleanupList) {
      //TODO: implement file deletion logic
    }
  }
}

import { AppContentTypes } from "./../models/appManifest.ts";
import { mqtt } from "../../deps.ts";

const endNodeCleanupLists = new Map<string, string[]>();

export function performEndNodeAdaptation(
  client: mqtt.MqttClient,
  endNodeUUID: string,
  _source: { filename: string; content: AppContentTypes }[],
): Error | null {
  const cleanupList = endNodeCleanupLists.get(endNodeUUID);
  if (cleanupList) {
    deleteEndNodeFiles(client, endNodeUUID, cleanupList);
  }

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


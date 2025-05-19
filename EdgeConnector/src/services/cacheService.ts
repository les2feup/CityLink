import { AppContentTypes, AppManifest } from "../models/appManifest.ts";
import { ThingDescription, ThingModel } from "../../deps.ts";

// Simple in-memory cache.
// No need for persistent storage or more complex caching strategies
// for this proof-of-concept implementation.

const manifestCache = new Map<string, AppManifest>();
const dlCache = new Map<string, AppContentTypes>();

const tmCache = new Map<string, ThingModel>();
const tdCache = new Map<string, Map<string, ThingDescription>>();

export function getManifest(
  manifestUrl: string,
): AppManifest | undefined {
  return manifestCache.get(manifestUrl);
}

export function setManifest(
  manifestUrl: string,
  manifest: AppManifest,
): void {
  manifestCache.set(manifestUrl, manifest);
}

export function getTM(tmUrl: string): ThingModel | undefined {
  return tmCache.get(tmUrl);
}

export function setTM(tmUrl: string, tm: ThingModel): void {
  tmCache.set(tmUrl, tm);
}

export function getTD(
  model: string,
  uuid: string,
): ThingDescription | undefined {
  return tdCache.get(model)?.get(uuid);
}

export function setTD(
  modelTitle: string,
  uuid: string,
  td: ThingDescription,
): void {
  if (!tdCache.has(modelTitle)) {
    tdCache.set(modelTitle, new Map<string, ThingDescription>());
  }
  tdCache.get(modelTitle)?.set(uuid, td);
}

export function getTDMap(
  modelTitle: string,
): Map<string, ThingDescription> | undefined {
  return tdCache.get(modelTitle);
}

export function getDlContent(fileUrl: string): AppContentTypes | undefined {
  return dlCache.get(fileUrl);
}

export function setDlContent(
  fileUrl: string,
  file: AppContentTypes,
): void {
  dlCache.set(fileUrl, file);
}

export function rawTDCache(): Map<string, Map<string, ThingDescription>> {
  return tdCache;
}

export function rawTMCache(): Map<string, ThingModel> {
  return tmCache;
}

export function clear(): void {
  manifestCache.clear();
  tmCache.clear();
  tdCache.clear();
  dlCache.clear();
}

export default {
  getManifest,
  setManifest,
  getTM,
  setTM,
  getTD,
  setTD,
  getTDMap,
  getDlContent,
  setDlContent,
  rawTDCache,
  rawTMCache,
  clear,
};

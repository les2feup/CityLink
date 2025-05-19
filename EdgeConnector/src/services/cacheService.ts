import { AppContentTypes, AppManifest } from "../models/appManifest.ts";
import { ThingDescription, ThingModel } from "../../deps.ts";

// Simple in-memory cache.
// No need for persistent storage or more complex caching strategies
// for this proof-of-concept implementation.

const manifestCache = new Map<string, AppManifest>();
const appCache = new Map<string, AppContentTypes>();

const tmCache = new Map<string, ThingModel>();
const tmUrlCache = new Map<string, string>();
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

export function getTM(
  key: string,
): ThingModel | undefined {
  return tmCache.get(key) ?? tmCache.get(tmUrlCache.get(key) ?? "");
}

export function setTM(
  tm: ThingModel,
  title: string,
  tmUrl: string,
): void {
  tmUrlCache.set(tmUrl, title);
  tmCache.set(title, tm);
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

export function getAppContent(fileUrl: string): AppContentTypes | undefined {
  return appCache.get(fileUrl);
}

export function setAppContent(
  fileUrl: string,
  file: AppContentTypes,
): void {
  appCache.set(fileUrl, file);
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
  appCache.clear();
}

export default {
  getManifest,
  setManifest,
  getTM,
  setTM,
  getTD,
  setTD,
  getTDMap,
  getAppContent,
  setAppContent,
  rawTDCache,
  rawTMCache,
  clear,
};

import { AppContentTypes, AppManifest } from "../models/appManifest.ts";
import { ThingDescription, ThingModel } from "../../deps.ts";

// --- Type Aliases ---
export type ManifestURL = string;
export type AppSrcURL = string;
export type TMURL = string;
export type TMTitle = string;
export type EndNodeUUID = string;

export type TDKey = { kind: "TDKey"; value: [TMTitle, EndNodeUUID] };

// --- Cache Key Mapping ---
export type CacheKey =
  | { cache: "manifest"; key: ManifestURL }
  | { cache: "app"; key: AppSrcURL }
  | { cache: "tm"; key: TMTitle }
  | { cache: "tmUrl"; key: TMURL }
  | { cache: "tdMap"; key: TMTitle }
  | { cache: "td"; key: TDKey }
  | { cache: "endNode"; key: EndNodeUUID };

// --- Cache Entry Types ---
export interface EndNodeCacheEntry {
  manifestKey: ManifestURL;
  tdKey: TDKey;
}

// --- Cache Maps ---
const manifestCache = new Map<ManifestURL, AppManifest>();
const appCache = new Map<AppSrcURL, AppContentTypes>();

const tmCache = new Map<TMTitle, ThingModel>();
const tmUrlCache = new Map<TMURL, TMTitle>();
const tdMapCache = new Map<TMTitle, Map<EndNodeUUID, ThingDescription>>();

const endNodeCache = new Map<EndNodeUUID, EndNodeCacheEntry>();

// --- Manifest Cache ---
export function getManifest(url: ManifestURL): AppManifest | undefined {
  return manifestCache.get(url);
}

export function setManifest(url: ManifestURL, manifest: AppManifest): void {
  manifestCache.set(url, manifest);
}

// --- Thing Model Cache ---
export function getTM(key: TMTitle | TMURL): ThingModel | undefined {
  const title = tmCache.has(key) ? key : tmUrlCache.get(key as TMURL);
  return title ? tmCache.get(title) : undefined;
}

export function setTM(tm: ThingModel, title: TMTitle, tmUrl: TMURL): void {
  tmUrlCache.set(tmUrl, title);
  tmCache.set(title, tm);
}

// --- Thing Description Cache ---
export function getTD(
  modelTitle: TMTitle,
  uuid: EndNodeUUID,
): ThingDescription | undefined {
  return tdMapCache.get(modelTitle)?.get(uuid);
}

export function getTDbyUUID(uuid: EndNodeUUID): ThingDescription | undefined {
  for (const [model, tdMap] of tdMapCache) {
    if (tdMap.has(uuid)) {
      console.debug(`Found TD for UUID "${uuid}" in model "${model}".`);
      return tdMap.get(uuid);
    }
  }
  return undefined;
}

export function setTD(
  modelTitle: TMTitle,
  uuid: EndNodeUUID,
  td: ThingDescription,
): void {
  const tdMap = tdMapCache.get(modelTitle) ??
    new Map<EndNodeUUID, ThingDescription>();
  tdMap.set(uuid, td);
  tdMapCache.set(modelTitle, tdMap);
}

export function getTDMap(
  modelTitle: TMTitle,
): Map<EndNodeUUID, ThingDescription> | undefined {
  return tdMapCache.get(modelTitle);
}

// --- App Content Cache ---
export function getAppContent(fileUrl: AppSrcURL): AppContentTypes | undefined {
  return appCache.get(fileUrl);
}

export function setAppContent(
  fileUrl: AppSrcURL,
  content: AppContentTypes,
): void {
  appCache.set(fileUrl, content);
}

// --- End Node Cache ---
export function getEndNode(uuid: EndNodeUUID): EndNodeCacheEntry | undefined {
  return endNodeCache.get(uuid);
}

export function setEndNode(
  uuid: EndNodeUUID,
  manifestKey: ManifestURL,
  tdKey: TDKey,
): void {
  endNodeCache.set(uuid, { manifestKey, tdKey });
}

// --- Raw Cache Accessors (debug/dev purposes) ---
export function rawTDCache(): ReadonlyMap<
  TMTitle,
  Map<EndNodeUUID, ThingDescription>
> {
  return tdMapCache;
}

export function rawTMCache(): ReadonlyMap<TMTitle, ThingModel> {
  return tmCache;
}

// --- Cache Clear ---
export function clear(): void {
  manifestCache.clear();
  appCache.clear();
  tmCache.clear();
  tmUrlCache.clear();
  tdMapCache.clear();
  endNodeCache.clear();
}

// --- Export Unified Cache API ---
export default {
  getManifest,
  setManifest,
  getTM,
  setTM,
  getTD,
  getTDbyUUID,
  setTD,
  getTDMap,
  getAppContent,
  setAppContent,
  getEndNode,
  setEndNode,
  rawTDCache,
  rawTMCache,
  clear,
};

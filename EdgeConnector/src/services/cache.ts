import { AppContentTypes, AppManifest } from "../models/appManifest.ts";
import { ThingDescription, ThingModel, UUID } from "../../deps.ts";

import umqttCore from "../controllers/umqttCore.ts";
import { getLogger } from "../utils/log/log.ts";

// --- Type Aliases ---
export type ManifestURL = string;
export type AppSrcURL = string;
export type TMURL = string;
export type TMTitle = string;
export type EndNodeUUID = UUID;

// --- Cache Key Mapping ---
export type CacheKey =
  | { cache: "manifest"; key: ManifestURL }
  | { cache: "app"; key: AppSrcURL }
  | { cache: "tm"; key: TMTitle }
  | { cache: "tmUrl"; key: TMURL }
  | { cache: "tdMap"; key: TMTitle }
  | { cache: "endNode"; key: EndNodeUUID };

// --- Cache Entry Types ---
export interface EndNode {
  manifest: AppManifest;
  tm: ThingModel;
  td: ThingDescription;
  controller?: umqttCore;
}

interface EndNodeEntry {
  manifestUrl: ManifestURL;
  tmTitle: TMTitle;
  controller?: umqttCore;
  td: ThingDescription;
}

// --- Cache Maps ---
const manifestCache = new Map<ManifestURL, AppManifest>();
const appCache = new Map<AppSrcURL, AppContentTypes>();

const tmCache = new Map<TMTitle, ThingModel>();
const tmUrlCache = new Map<TMURL, TMTitle>();

const endNodeCache = new Map<EndNodeUUID, EndNodeEntry>();

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
// Overload signatures
export function getEndNode(uuid: EndNodeUUID): EndNode | undefined;
export function getEndNode(
  filter: (node: EndNode) => boolean,
): EndNode[];

// Single implementation
export function getEndNode(
  arg: EndNodeUUID | ((node: EndNode) => boolean),
): EndNode | EndNode[] | undefined {
  const logger = getLogger(import.meta.url);
  const reconstruct = (entry: EndNodeEntry): EndNode | undefined => {
    const manifest = manifestCache.get(entry.manifestUrl);
    const tm = tmCache.get(entry.tmTitle);
    if (!manifest || !tm) return undefined;

    return {
      manifest,
      tm,
      td: entry.td,
      controller: entry.controller,
    };
  };

  if (typeof arg === "function") {
    return Array.from(endNodeCache.values())
      .map(reconstruct)
      .filter((node): node is EndNode => !!node)
      .filter(arg);
  } else {
    const raw = endNodeCache.get(arg);
    if (!raw) {
      logger.warn(`End node with UUID "${arg}" not found.`);
      return undefined;
    }
    return raw ? reconstruct(raw) : undefined;
  }
}

export function insertEndNode(
  uuid: EndNodeUUID,
  manifest: AppManifest,
  tm: ThingModel,
  td: ThingDescription,
  controller?: umqttCore,
): void {
  const logger = getLogger(import.meta.url);
  if (endNodeCache.has(uuid)) {
    logger.warn(`End node with UUID "${uuid}" already exists.`);
    return;
  }

  const manifestUrl = [...manifestCache.entries()]
    .find(([_, m]) => m === manifest)?.[0];

  const tmTitle = [...tmCache.entries()]
    .find(([_, t]) => t === tm)?.[0];

  if (!manifestUrl || !tmTitle) {
    logger.warn(`Manifest or ThingModel not found in caches`);
    return;
  }

  endNodeCache.set(uuid, {
    manifestUrl,
    tmTitle,
    td,
    controller,
  });
}

export function updateEndNode(
  uuid: EndNodeUUID,
  n: {
    manifest?: AppManifest;
    td?: ThingDescription;
    tm?: ThingModel;
    controller?: umqttCore;
  },
): void {
  const entry = endNodeCache.get(uuid);
  const logger = getLogger(import.meta.url);
  if (!entry) {
    logger.warn(`End node with UUID "${uuid}" does not exist.`);
    return;
  }

  if (n.td) entry.td = n.td;
  if (n.controller) entry.controller = n.controller;

  if (n.manifest) {
    const manifestUrl = [...manifestCache.entries()]
      .find(([_, m]) => m === n.manifest)?.[0];
    if (manifestUrl) entry.manifestUrl = manifestUrl;
  }

  if (n.tm) {
    const tmTitle = [...tmCache.entries()]
      .find(([_, t]) => t === n.tm)?.[0];
    if (tmTitle) entry.tmTitle = tmTitle;
  }

  endNodeCache.set(uuid, entry);
}

// --- Raw Cache Accessors (debug/dev purposes) ---
export function rawTMCache(): ReadonlyMap<TMTitle, ThingModel> {
  return tmCache;
}

// --- Cache Clear ---
export function clear(): void {
  manifestCache.clear();
  appCache.clear();
  tmCache.clear();
  tmUrlCache.clear();
  endNodeCache.clear();
}

// --- Export Unified Cache API ---
export default {
  getManifest,
  setManifest,
  getTM,
  setTM,
  getAppContent,
  setAppContent,
  getEndNode,
  insertEndNode,
  updateEndNode,
  rawTMCache,
  clear,
};

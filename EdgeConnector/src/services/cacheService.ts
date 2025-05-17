import { AppManifest, DlContentTypes } from "../models/appManifest.ts";
import { ThingModel } from "../../deps.ts";

// Simple in-memory cache for app manifests, thing models, and files.
// No need for persistent storage or cache timeouts as of now.

const manifestCache = new Map<string, AppManifest>();
const tmCache = new Map<string, ThingModel>();
const fileCache = new Map<string, DlContentTypes>();

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

export function getFile(fileUrl: string): DlContentTypes | undefined {
  return fileCache.get(fileUrl);
}

export function setFile(
  fileUrl: string,
  file: DlContentTypes,
): void {
  fileCache.set(fileUrl, file);
}

export function clear(): void {
  manifestCache.clear();
  tmCache.clear();
  fileCache.clear();
}

export default {
  getManifest,
  setManifest,
  getTM,
  setTM,
  getFile,
  setFile,
  clear,
};

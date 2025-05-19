// src/services/thingModelService.ts
import { ThingModel, ThingModelHelpers } from "../../deps.ts";
import { AppManifest } from "../models/appManifest.ts";
import cache from "./cacheService.ts";

type TmMetadata = AppManifest["wot"]["tm"];

export async function fetchThingModel(
  metadata: TmMetadata,
): Promise<ThingModel | Error> {
  const tmTools = new ThingModelHelpers();

  // before fetching, try the model cache
  const cachedModel = cache.getTM(metadata.href);
  let fetchedModel: ThingModel | undefined;
  if (!cachedModel) {
    fetchedModel = await tmTools.fetchModel(metadata.href);
  }

  if (!fetchedModel && !cachedModel) {
    return new Error(`Failed to fetch Thing Model from ${metadata.href}`);
  }

  const tm = cachedModel ?? fetchedModel!;
  const versionError = validateModelVersion(tm, metadata.version.model);
  if (versionError) {
    return versionError;
  }

  const title = metadata.title ?? tm.title;
  if (!title) {
    return new Error("Model title is missing");
  }

  if (!cachedModel) {
    cache.setTM(tm, title, metadata.href);
  }

  return tm;
}

function validateModelVersion(
  model: ThingModel,
  expected: string,
): Error | null {
  const version = model.version;

  if (!version) {
    return new Error("Model version is missing");
  }

  if (typeof version === "string") {
    return version === expected ? null : new Error(
      `Model version mismatch: expected ${expected}, got ${version}`,
    );
  }

  if (typeof version === "object" && version !== null) {
    const actualVersion = (version as { model?: unknown }).model;
    if (typeof actualVersion !== "string") {
      return new Error("Model version 'model' property must be a string");
    }
    return actualVersion === expected ? null : new Error(
      `Model version mismatch: expected ${expected}, got ${actualVersion}`,
    );
  }

  return new Error(
    "Model version must be a string or an object with a 'model' string",
  );
}

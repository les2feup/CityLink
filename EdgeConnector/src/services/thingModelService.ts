// src/services/thingModelService.ts
import { ThingDescription, ThingModel, ThingModelHelpers } from "../../deps.ts";
import { TmMetadata } from "../models/appManifest.ts";
import type { CompositionOptions } from "../../deps.ts";
import cache from "./cacheService.ts";

/**
 * Generates a Thing Description from the provided Thing Model.
 *
 * This asynchronous function configures composition options using the specified mapping object with self-composition enabled.
 * It then invokes the helper to generate partial Thing Descriptions and returns the first generated description.
 *
 * @param model - The Thing Model to be composed into a Thing Description.
 * @param map - Custom composition mappings to be applied during composition.
 * @returns The first generated Thing Description.
 */
export async function instantiateTDs(
  tmTools: ThingModelHelpers,
  model: ThingModel,
  map: Record<string, unknown>,
): Promise<ThingDescription[]> {
  const options: CompositionOptions = {
    map,
    selfComposition: false,
  };
  const things = await tmTools.getPartialTDs(model, options);
  return things as ThingDescription[];
}

export async function fetchThingModel(
  tmTools: ThingModelHelpers,
  metadata: TmMetadata,
): Promise<ThingModel | Error> {
  // before fetching, try the model cache
  const cachedModel = cache.getTM(metadata.href);
  let fetchedModel: ThingModel | undefined;
  if (!cachedModel) {
    fetchedModel = await tmTools.fetchModel(metadata.href);
  }

  if (!fetchedModel && !cachedModel) {
    return new Error(`Failed to fetch Thing Model from ${metadata.href}`);
  }

  const tm = (cachedModel || fetchedModel) as ThingModel;
  const versionError = validateModelVersion(tm, metadata.version.model);
  if (versionError) {
    return versionError;
  }

  if (!cachedModel) {
    cache.setTM(metadata.href, tm);
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

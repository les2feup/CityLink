// src/services/thingModelService.ts
import { ThingDescription, ThingModel, ThingModelHelpers } from "../../deps.ts";

import type { CompositionOptions } from "../../deps.ts";

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
export async function createThingFromModel(
  tmTools: ThingModelHelpers,
  model: ThingModel,
  map: Record<string, unknown>,
): Promise<ThingDescription> {
  const options: CompositionOptions = {
    map,
    selfComposition: true,
  };
  const [thing] = (await tmTools.getPartialTDs(model, options)) as
    | ThingDescription[]
    | [];
  return thing;
}

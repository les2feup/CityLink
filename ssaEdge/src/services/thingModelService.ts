// src/services/thingModelService.ts
import { assert, ThingModel, ThingModelHelpers, ThingDescription } from "../../deps.ts";
import { THINGS_DIR } from "../config/config.ts";

import type { CompositionOptions } from "../../deps.ts";

/**
 * Loads and validates a Thing Model from a local JSON file.
 *
 * This asynchronous function reads the content of a JSON file located at the provided filePath, parses it into a Thing Model, and validates the model using ThingModelHelpers.validateThingModel. If the file cannot be read, the content is invalid JSON, or the model fails validation, an error is thrown.
 *
 * @param filePath - The path to the JSON file containing the Thing Model.
 * @returns A promise that resolves to the validated Thing Model.
 *
 * @throws {Error} If reading the file, parsing its content, or validating the Thing Model fails.
 */
async function loadLocalThingModel(filePath: string): Promise<ThingModel> {
  try {
    const fileContent = await Deno.readTextFile(filePath);
    const thingModel: ThingModel = JSON.parse(fileContent);
    const validatedModel = ThingModelHelpers.validateThingModel(thingModel);
    if (validatedModel.errors) {
      throw new Error(
        `Thing Model validation errors: ${
          JSON.stringify(validatedModel.errors)
        }`,
      );
    }
    assert(validatedModel.valid, "Thing Model should be valid");
    return thingModel;
  } catch (error) {
    console.error(
      `Failed to load or validate Thing Model '${filePath}':`,
      error,
    );
    throw error;
  }
}

/**
 * Asynchronously loads all Thing Models from JSON files in the designated directory.
 *
 * Iterates through the files in the THINGS_DIR, and for each file with a ".json" extension,
 * derives the model name by removing the ".json" suffix and loads the model via loadLocalThingModel.
 * The resulting models are returned in a Map where each key is the model name.
 *
 * @returns A Promise that resolves to a Map linking model names to their corresponding ThingModel instances.
 */
export async function loadAllThingModels(): Promise<Map<string, ThingModel>> {
  const models = new Map<string, ThingModel>();
  for await (const dirEntry of Deno.readDir(THINGS_DIR)) {
    if (dirEntry.isFile && dirEntry.name.endsWith(".json")) {
      const modelName = dirEntry.name.replace(".json", "");
      const model = await loadLocalThingModel(`${THINGS_DIR}/${dirEntry.name}`);
      models.set(modelName, model);
    }
  }
  return models;
}

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

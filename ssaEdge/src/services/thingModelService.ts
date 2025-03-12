// src/services/thingModelService.ts
import { assert, ThingModel, ThingModelHelpers, ThingDescription } from "../../deps.ts";
import { THINGS_DIR } from "../config/config.ts";

import type { CompositionOptions } from "../../deps.ts";

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

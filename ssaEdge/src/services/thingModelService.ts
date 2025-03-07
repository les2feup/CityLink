// src/services/thingModelService.ts
import { assert, ThingModel, ThingModelHelpers } from "../../deps.ts";
import { THINGS_DIR } from "../config/config.ts";

import type { CompositionOptions } from "../../deps.ts";

export async function loadThingModel(modelName: string): Promise<ThingModel> {
  try {
    const filePath = `${THINGS_DIR}/${modelName}.json`;
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
      `Failed to load or validate Thing Model '${modelName}':`,
      error,
    );
    throw error;
  }
}

export async function createThingFromModel(
  tmTools: ThingModelHelpers,
  model: ThingModel,
  map: Record<string, unknown>,
): Promise<WoT.ThingDescription> {
  const options: CompositionOptions = {
    map,
    selfComposition: false,
  };
  const [thing] = (await tmTools.getPartialTDs(model, options)) as
    | WoT.ThingDescription[]
    | [];
  return thing;
}

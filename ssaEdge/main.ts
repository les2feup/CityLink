import {
  CompositionOptions,
  ThingModelHelpers,
} from "npm:@thingweb/thing-model";

import { ThingModel } from "npm:wot-thing-model-types";

import assert from "node:assert";

function loadThingModel(): ThingModel | undefined {
  const thingModel: ThingModel = JSON.parse(
    Deno.readTextFileSync(
      "./things/base_ssa_thing.json",
    ),
  );
  const validatedModel = ThingModelHelpers.validateThingModel(thingModel);
  if (validatedModel.errors !== undefined) {
    console.error("Thing Model is not valid: ", validatedModel.errors);
    return undefined;
  }
  assert(validatedModel.valid, "Thing Model should be valid");

  return thingModel;
}

function thingHandler(td: WoT.ThingDescription): void {
  console.log(JSON.stringify(td, null, 2));

  //TODO: Expose Thing
}

async function createThingFromModel(
  tmTools: ThingModelHelpers,
  model: ThingModel,
  map: Record<string, unknown>,
): Promise<WoT.ThingDescription> {
  const options: CompositionOptions = {
    map: map,
    selfComposition: false,
  };

  const [thing] = await tmTools.getPartialTDs(
    model,
    options,
  ) as WoT.ThingDescription[];

  return thing;
}

function main(): void {
  const tmTools = new ThingModelHelpers();
  const model = loadThingModel();
  if (model === undefined) {
    console.error("Error loading Thing Model");
    Deno.exit(1);
  }

  const map = {
    THING_MODEL: "base_ssa_thing",
    THING_UUID_V4: `${crypto.randomUUID()}`,
    MQTT_BROKER_ADDR: "192.168.1.26:1883",
  };

  createThingFromModel(tmTools, model, map).then((td) => {
    console.log(`Created TD from model: ${td.title}`);
    thingHandler(td);
  });
}

if (import.meta.main) {
  main();
}

import {
  CompositionOptions,
  ThingModelHelpers,
} from "npm:@thingweb/thing-model";

import { ThingModel } from "npm:wot-thing-model-types";
import mqtt from "npm:mqtt";

import assert from "node:assert";
import { Application } from "jsr:@oak/oak/application";
import { Router } from "jsr:@oak/oak/router";

function loadThingModel(model_name: string): ThingModel | undefined {
  const thingModel: ThingModel = JSON.parse(
    Deno.readTextFileSync(
      `./things/${model_name}.json`,
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
  // 1. Connect to the MQTT broker and listen on the registration topic
  // 2. Parse registration messages and identify the Thing Model
  // 3. Instantiate the Thing Model and create a TD based on the received registration message
  // 4. Expose the TD as a WoT Thing

  // Map<model, Map<uuid, TD>>
  const hostedThings = new Map<string, Map<string, WoT.ThingDescription>>();
  const tmTools = new ThingModelHelpers();

  const client = mqtt.connect("mqtt://localhost:1883");
  client.on("connect", () => {
    client.subscribe("registration/#", (err) => {
      if (err) {
        console.error("Error subscribing to registration topic");
        Deno.exit(1);
      }

      console.log(
        "Connected to MQTT broker and subscribed to registration topic",
      );
    });
  });

  client.on("message", (topic, message) => {
    console.log(`Received message on topic ${topic}: ${message.toString()}`);
    const parts = topic.toString().split("/");
    if (parts.length !== 2) {
      console.error("Invalid topic format");
      return;
    }

    if (parts[0] !== "registration") {
      console.error("Invalid topic format");
      return;
    }

    const uuid = parts[1];
    console.log(`UUID from topic: ${uuid}`);

    const message_str = message.toString();
    console.log(`Message: ${message_str}`);

    const payload = JSON.parse(message_str);
    if (payload === undefined) {
      console.error("Error parsing message");
      return;
    }
    console.log(`Payload: ${JSON.stringify(payload)}`);

    const msg_uuid = payload.uuid;
    if (uuid !== msg_uuid) {
      console.error("UUID from topic and message do not match");
      return;
    }
    console.log(`UUID from message: ${msg_uuid}`);

    const model_name = payload.model;
    if (model_name === undefined) {
      console.error("Model not found in registration message");
      return;
    }
    console.log(`Model from registration message: ${model_name}`);

    const version = payload.version;
    if (version === undefined) {
      console.error("Version not found in registration message");
      return;
    }
    console.log(
      `Version from registration message: ${JSON.stringify(version)}`,
    );

    const map = {
      THING_MODEL: model_name,
      THING_UUID_V4: uuid,
      MQTT_BROKER_ADDR: "localhost:1883",
    };

    const model = loadThingModel(model_name);
    if (model === undefined) {
      console.error("Error loading Thing Model");
      return;
    }

    createThingFromModel(tmTools, model, map).then((td) => {
      console.log(`Created TD from model: ${td.title}`);
      if (hostedThings.has(model_name)) {
        const things = hostedThings.get(model_name);
        if (things !== undefined) {
          things.set(uuid, td);
          console.log(`Added Thing to hostedThings: ${td.title}`);
        } else {
          console.error("Error adding Thing to hostedThings");
        }
      } else {
        const things = new Map<string, WoT.ThingDescription>();
        things.set(uuid, td);
        hostedThings.set(model_name, things);
        console.log(`Added Thing to hostedThings: ${td.title}`);
      }
    });
  });

  const router = new Router();
  router.get("/", (ctx) => {
    ctx.response.body = `<!DOCTYPE html>
    <html>
      <head><title>Hello oak!</title><head>
      <body>
        <h1>Hello oak!</h1>
      </body>
    </html>
  `;
  });

  router.get("/things", (ctx) => {
    ctx.response.body = JSON.stringify([...hostedThings.keys()]);
  });

  router.get("/things/:model", (ctx) => {
    const model = ctx.params.model;
    if (hostedThings.has(model)) {
      const things = hostedThings.get(model);
      if (things !== undefined) {
        ctx.response.body = JSON.stringify([...things.keys()]);
      } else {
        ctx.response.status = 404;
        ctx.response.body = "Things not found";
      }
    } else {
      ctx.response.status = 404;
      ctx.response.body = "Model not found";
    }
  });

  router.get("/things/:model/:uuid", (ctx) => {
    const model = ctx.params.model;
    const uuid = ctx.params.uuid;
    if (hostedThings.has(model)) {
      const things = hostedThings.get(model);
      if (things !== undefined) {
        const thing = things.get(uuid);
        if (thing !== undefined) {
          ctx.response.body = thing;
          ctx.response.type = "application/json";
        } else {
          ctx.response.status = 404;
          ctx.response.body = "Thing not found";
        }
      } else {
        ctx.response.status = 404;
        ctx.response.body = "Things not found";
      }
    } else {
      ctx.response.status = 404;
      ctx.response.body = "Model not found";
    }
  });

  const app = new Application();
  app.use(router.routes());
  app.use(router.allowedMethods());

  app.listen({ port: 8080 });
}

if (import.meta.main) {
  main();
}

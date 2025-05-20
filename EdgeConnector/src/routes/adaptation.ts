import { MqttClientFactory, Router, Servient } from "../../deps.ts";
import { AdaptationSchema } from "../models/adaptationSchema.ts";
import cache from "./../services/cacheService.ts";
import mpyCoreController from "./../controllers/mpyCoreController.ts";

async function adaptEndNode(
  endNodeUUID: string,
  servient: Servient,
) {
  const td = cache.getTDbyUUID(`urn:uuid:${endNodeUUID}`);
  if (!td) {
    return new Error(
      `td for end node with UUID "${endNodeUUID}" not found.`,
    );
  }

  try {
    const WoT = await servient.start();
    const thing = await WoT.consume(td);
  } catch (err) {
    console.error(
      `Error while parsing cleanupList for end node with UUID "${endNodeUUID}": ${err}`,
    );
  }
}

export function createApadationProtocolRouter(): Router {
  const router = new Router();
  // const servient: Servient = new Servient();
  // servient.addClientFactory(new MqttClientFactory());

  router.post("/adaptation", async (ctx) => {
    if (!ctx.request.hasBody) {
      ctx.response.status = 400;
      ctx.response.body = "Bad Request: No body found";
      return;
    }

    const body = await ctx.request.body.json();
    const data = AdaptationSchema.safeParse(body);
    if (!data.success) {
      ctx.response.status = 400;
      ctx.response.body = `Bad Request: ${
        JSON.stringify(data.error.format(), null, 2)
      }`;
      return;
    }

    const schema = data.data;

    // const err = adaptEndNode();
    // if (err) {
    //   ctx.response.status = 500;
    //   ctx.response.body = `Internal Server Error: ${err.message}`;
    //   return;
    // }

    // identify the end node device to be updated
    // fetch the new app manifest
    // fetch the new app source
    // forward everything to the update manager
    //

    ctx.response.status = 201;
    ctx.response.body = { status: "ok", message: "Adaptation started" };
  });

  return router;
}

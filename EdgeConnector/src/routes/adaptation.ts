import { Router } from "../../deps.ts";
import { AdaptationSchema } from "../models/adaptation.ts";

export function createApadationProtocolRouter(): Router {
  const router = new Router();

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

    // identify the end node device to be updated
    // fetch the new app manifest
    // fetch the new app source
    // forward everything to the update manager
  });

  return router;
}

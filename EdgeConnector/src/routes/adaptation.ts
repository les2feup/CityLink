import { Router, UUID } from "../../deps.ts";
import { AdaptationSchema } from "../models/adaptationSchema.ts";
import cache from "./../services/cache.ts";
import { fetchAppManifest } from "../services/appManifestService.ts";

export function createApadationProtocolRouter(): Router {
  const router = new Router();

  router.post("/adaptation", async (ctx) => {
    if (!ctx.request.hasBody) {
      ctx.response.status = 400;
      ctx.response.body = "Bad Request: No body found";
      return;
    }

    try {
      const body = await ctx.request.body.json();
      const data = AdaptationSchema.safeParse(body);
      if (!data.success) {
        throw new Error(
          JSON.stringify(data.error.format(), null, 2),
        );
      }

      const schema = data.data;

      const node = cache.getEndNode(schema.endNodeUUID as UUID);
      if (!node) {
        ctx.response.status = 404;
        ctx.response.body =
          `End node with UUID "${schema.endNodeUUID}" not found`;
        return;
      }

      if (!node.controller) {
        ctx.response.status = 503;
        ctx.response.body =
          `End node with UUID "${schema.endNodeUUID}" is not connected`;

        //TODO: maybe try to find out what happened
        return;
      }

      const appManifest = await fetchAppManifest(schema.manifest);
      if (appManifest instanceof Error) {
        throw appManifest;
      }

      await node.controller.otauInit(appManifest);
      ctx.response.status = 201;
      ctx.response.body = { status: "ok", message: "Adaptation initiated" };
    } catch (err) {
      ctx.response.status = 500;
      if (err instanceof Error) {
        ctx.response.body = `Internal server error: ${err.message}`;
      } else {
        ctx.response.body = `Internal server error: ${err}`;
      }
    }
  });

  return router;
}

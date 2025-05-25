import { Router, UUID } from "../../deps.ts";
import cache from "../services/cache.ts";

export function createManifestRouter(): Router {
  const router = new Router();

  // Display the JSON of a specific Application Manifest
  router.get("/manifests/:uuid", (ctx) => {
    const uuid = ctx.params.uuid! as UUID;
    const node = cache.getEndNode(uuid);
    if (node) {
      ctx.response.type = "application/json";
      ctx.response.body = node.manifest;
    } else {
      ctx.response.status = 404;
      ctx.response.body = "Manifest not found";
    }
  });

  return router;
}

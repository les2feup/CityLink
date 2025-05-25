import { Router, UUID } from "../../deps.ts";
import cache from "../services/cache.ts";

export function createTDRouter(): Router {
  const router = new Router();

  // Display the JSON of a specific Thing Description
  router.get("/tds/:uuid", (ctx) => {
    const uuid = ctx.params.uuid! as UUID;
    const node = cache.getEndNode(uuid);
    if (node) {
      ctx.response.type = "application/json";
      ctx.response.body = node.td;
    } else {
      ctx.response.status = 404;
      ctx.response.body = "Thing Description not found";
    }
  });

  return router;
}

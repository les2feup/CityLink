// src/routes/index.ts
import { Router } from "../../deps.ts";
import { createTDRouter } from "./tdRoutes.ts";
import { createTMRouter } from "./tmRoutes.ts";
import type { ThingModel } from "../../deps.ts";

export function createAppRouter(
  hostedThings: Map<string, Map<string, WoT.ThingDescription>>,
  hostedModels: Map<string, ThingModel>,
): Router {
  const router = new Router();

  // Merge the things routes
  router.use(createTDRouter(hostedThings).routes());

  // Merge the models routes
  router.use(createTMRouter(hostedModels).routes());

  return router;
}

// src/routes/index.ts
import { Router } from "../../deps.ts";
import { createTDRouter } from "./tdRoutes.ts";
import { createTMRouter } from "./tmRoutes.ts";
import type { ThingModel, ThingDescription} from "../../deps.ts";

export function createAppRouter(
  hostedThings: Map<string, Map<string, ThingDescription>>,
  hostedModels: Map<string, ThingModel>,
): Router {
  const router = new Router();

  // Merge the things routes
  router.use(createTDRouter(hostedThings).routes());

  // Merge the models routes
  router.use(createTMRouter(hostedModels).routes());

  router.get("/", (ctx) => {
    ctx.response.type = "text/html";
    ctx.response.body = `
      <html>
        <head>
          <title>Welcome to the WoT Edge Node Demo</title>
        </head>
        <body>
          <h1>Welcome to the WoT Application</h1>
          <p>Navigate to:</p>
          <ul>
            <li><a href="/things">Things</a></li>
            <li><a href="/models">Models</a></li>
          </ul>
        </body>
      </html>
    `;
  });
  return router;
}

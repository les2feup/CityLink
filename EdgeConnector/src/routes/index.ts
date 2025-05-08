// src/routes/index.ts
import { Router } from "../../deps.ts";
import { createTDRouter } from "./tdRoutes.ts";
import { createTMRouter } from "./tmRoutes.ts";
import type { ThingDescription, ThingModel } from "../../deps.ts";

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
          <title>Welcome to the CityLink Edge Node Demo</title>
        </head>
        <body>
          <h1>Welcome to the CityLink Edge Connector home page</h1>
          <p>Navigate to:</p>
          <ul>
            <li><a href="/things">Thing Descriptions</a></li>
            <li><a href="/models">Thing Models</a></li>
          </ul>
        </body>
      </html>
    `;
  });
  return router;
}

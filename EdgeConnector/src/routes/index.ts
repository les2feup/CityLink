// src/routes/index.ts
import { Router } from "../../deps.ts";
import { createTDRouter } from "./tdRoutes.ts";
import { createTMRouter } from "./tmRoutes.ts";
import { createApadationProtocolRouter } from "./adaptation.ts";

export function createRouter(): Router {
  const router = new Router();

  // Merge the things routes
  router.use(createTDRouter().routes());

  // Merge the models routes
  router.use(createTMRouter().routes());

  router.use(createApadationProtocolRouter().routes());

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

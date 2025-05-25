import { Router } from "../../deps.ts";
import cache from "../services/cache.ts";

export function createTMRouter(): Router {
  const router = new Router();

  // List all hosted models with links
  router.get("/models", (ctx) => {
    const modelNames = [...cache.rawTMCache().keys()];
    const links = modelNames
      .map((model) => `<li><a href="/models/${model}">${model}</a></li>`)
      .join("");
    ctx.response.type = "text/html";
    ctx.response.body = `<html>
      <head><title>Hosted Thing Models</title></head>
      <body>
        <h1>Hosted Thing Models</h1>
        <ul>
          ${links}
        </ul>
      </body>
    </html>`;
  });

  // Display the JSON of a specific Thing Model
  router.get("/models/:model", (ctx) => {
    const model = cache.getTM(ctx.params.model!);
    if (model) {
      ctx.response.type = "application/json";
      ctx.response.body = model;
    } else {
      ctx.response.status = 404;
      ctx.response.body = "Model not found";
    }
  });

  return router;
}

import { Router } from "../../deps.ts";
import type { ThingModel } from "../../deps.ts";

export function createTMRouter(
  hostedModels: Map<string, ThingModel>,
): Router {
  const router = new Router();

  // List all hosted models with links
  router.get("/models", (ctx) => {
    const modelNames = [...hostedModels.keys()];
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
// Display the JSON of a specific Thing Model
router.get("/models/:model", (ctx) => {
  const modelName = ctx.params.model;
  if (!modelName) {
    ctx.response.status = 400;
    ctx.response.body = "Model name is required";
  } else {
    const model = hostedModels.get(modelName);
    if (model) {
      ctx.response.type = "application/json";
      ctx.response.body = model;
    } else {
      ctx.response.status = 404;
      ctx.response.body = "Model not found";
    }
  }
});

  return router;
}

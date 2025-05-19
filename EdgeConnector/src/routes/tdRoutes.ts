import { Router } from "../../deps.ts";
import cache from "./../services/cacheService.ts";

export function createTDRouter(): Router {
  const router = new Router();

  // List available Thing models (keys)
  router.get("/things", (ctx) => {
    const models = [...cache.rawTDCache().keys()];
    const links = models
      .map((model) => `<li><a href="/things/${model}">${model}</a></li>`)
      .join("");
    ctx.response.type = "text/html";
    ctx.response.body = `<html>
      <head><title>Thing Models</title></head>
      <body>
        <h1>Thing Models</h1>
        <ul>
          ${links}
        </ul>
      </body>
    </html>`;
  });

  // List things for a given model
  router.get("/things/:model", (ctx) => {
    const model = ctx.params.model;
    const things = cache.getTDMap(model!);
    if (things) {
      const links = [...things.keys()]
        .map((uuid) =>
          `<li><a href="/things/${model}/${uuid}">${uuid}</a></li>`
        )
        .join("");
      ctx.response.type = "text/html";
      ctx.response.body = `<html>
        <head><title>Things for ${model}</title></head>
        <body>
          <h1>Things for Model: ${model}</h1>
          <ul>
            ${links}
          </ul>
        </body>
      </html>`;
    } else {
      ctx.response.status = 404;
      ctx.response.body = "Model not found";
    }
  });

  // Display a specific TD
  router.get("/things/:model/:uuid", (ctx) => {
    const model = ctx.params.model;
    const uuid = ctx.params.uuid;
    const TD = cache.getTD(model!, uuid!);
    if (TD) {
      ctx.response.type = "application/json";
      ctx.response.body = TD;
    } else {
      ctx.response.status = 404;
      ctx.response.body = "Thing not found";
    }
  });

  return router;
}

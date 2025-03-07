import { Router } from "../../deps.ts";

/**
 * Creates a Router instance with the HTTP routes.
 */
export function createRouter(
  hostedThings: Map<string, Map<string, WoT.ThingDescription>>,
): Router {
  const router = new Router();

  router.get("/", (ctx) => {
    ctx.response.body = `<!DOCTYPE html>
<html>
  <head><title>Hello oak!</title></head>
  <body>
   <h1>Hello oak!</h1>
  </body>
</html>`;
  });

  router.get("/things", (ctx) => {
    const models = [...hostedThings.keys()];
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

  router.get("/things/:model", (ctx) => {
    const model = ctx.params.model;
    const things = hostedThings.get(model!);
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

  router.get("/things/:model/:uuid", (ctx) => {
    const model = ctx.params.model;
    const uuid = ctx.params.uuid;
    const things = hostedThings.get(model!);
    if (things) {
      const thing = things.get(uuid!);
      if (thing) {
        ctx.response.type = "application/json";
        ctx.response.body = thing;
      } else {
        ctx.response.status = 404;
        ctx.response.body = "Thing not found";
      }
    } else {
      ctx.response.status = 404;
      ctx.response.body = "Model not found";
    }
  });

  return router;
}

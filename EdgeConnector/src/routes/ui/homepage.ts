// src/routes/ui/homepage.ts

import { Eta, Router } from "../../../deps.ts";

export function createUIHomepageRouter(): Router {
  const router = new Router();

  const viewpath = Deno.cwd() + "/views/";
  const eta = new Eta({ views: viewpath, cache: true });

  router.get("/", async (ctx) => {
    const homepageContent = await eta.renderAsync("homepage", {});
    const html = await eta.renderAsync("layout", {
      title: "Home",
      body: homepageContent,
    });

    ctx.response.type = "text/html";
    ctx.response.body = html;
  });

  return router;
}

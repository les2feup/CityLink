// src/routes/ui/homepage.ts

import { Eta, path, Router } from "../../../deps.ts";

export function createUIHomepageRouter(
  eta: Eta,
  fragmentsDir: string,
): Router {
  const router = new Router();

  router.get("/", async (ctx) => {
    const homepageContent = await Deno.readTextFile(
      path.join(fragmentsDir, "home.html"),
    );
    const html = await eta.renderAsync("layout", {
      title: "Home",
      body: homepageContent,
    });

    ctx.response.type = "text/html";
    ctx.response.body = html;
  });

  return router;
}

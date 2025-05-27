// src/routes/index.ts
import { Router } from "../../deps.ts";
import { createTMRouter } from "./tmRoutes.ts";
import { createEndNodeRouter } from "./endNodeRoutes.ts";
import { createManifestRouter } from "./appManifestRoutes.ts";
import { createTDRouter } from "./tdRoutes.ts";
import { createApadationProtocolRouter } from "./adaptation.ts";
import { createUIHomepageRouter } from "./ui/homepage.ts";

export function createRouter(): Router {
  const router = new Router();

  router.use(createUIHomepageRouter().routes());

  // Merge the endnode routes
  router.use(createEndNodeRouter().routes());

  // Merge the thing model routes
  router.use(createTMRouter().routes());

  // Merge the thing description routes
  router.use(createTDRouter().routes());

  // Merge the app manifest routes
  router.use(createManifestRouter().routes());

  // Merge the adaptation protocol routes
  router.use(createApadationProtocolRouter().routes());

  // router.get("/", (ctx) => {
  //   ctx.response.type = "text/html";
  //   ctx.response.body = `
  //     <html>
  //       <head>
  //         <title>Welcome to the CityLink Edge Node Demo</title>
  //       </head>
  //       <body>
  //         <h1>Welcome to the CityLink Edge Connector home page</h1>
  //         <p>Navigate to:</p>
  //         <ul>
  //         <li><a href="/models">Known Thing Models</a></li>
  //           <li><a href="/endnodes">Registered End Nodes</a></li>
  //         </ul>
  //       </body>
  //     </html>
  //   `;
  // });
  return router;
}

import { Application, ThingModelHelpers } from "../deps.ts";
import { setupMQTT } from "./controllers/mqttController.ts";
import { createRouter } from "./controllers/httpController.ts";
import { HTTP_PORT } from "./config/config.ts";

export function startApp(): void {
  // Shared state: Map<model, Map<uuid, WoT.ThingDescription>>
  const hostedThings = new Map<string, Map<string, WoT.ThingDescription>>();
  const tmTools = new ThingModelHelpers();

  // Initialize MQTT handler
  setupMQTT(tmTools, hostedThings);

  // Initialize HTTP server
  const router = createRouter(hostedThings);
  const app = new Application();
  app.use(router.routes());
  app.use(router.allowedMethods());

  console.log(`HTTP server listening on port ${HTTP_PORT}`);
  app.listen({ port: HTTP_PORT });
}

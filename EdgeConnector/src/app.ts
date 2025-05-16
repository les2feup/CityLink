import {
  Application,
  ThingDescription,
  ThingModel,
  ThingModelHelpers,
} from "../deps.ts";
import * as mqttConnector from "./connectors/mqttConnector.ts";
import { createRouter } from "./routes/index.ts";
import { HTTP_HOSTNAME, HTTP_PORT } from "./config/config.ts";

export function startApp(): void {
  // Shared state: Map<model, Map<uuid, ThingDescription>>
  const hostedTDs = new Map<string, Map<string, ThingDescription>>();
  const hostedTMs = new Map<string, ThingModel>();
  const tmTools = new ThingModelHelpers();

  // Initialize MQTT handler
  mqttConnector.launch(tmTools, hostedTMs, hostedTDs, (error: Error) => {
    console.error("MQTT error:", error);
  });

  // Initialize HTTP server
  const router = createRouter(hostedTDs, hostedTMs);
  const app = new Application();
  app.use(router.routes());
  app.use(router.allowedMethods());

  console.log(`HTTP server listening on port ${HTTP_PORT}`);
  app.listen({ hostname: HTTP_HOSTNAME, port: HTTP_PORT });
}

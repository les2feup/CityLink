import { Application } from "../deps.ts";
import mqttConnector from "./connectors/mqttConnector.ts";
import { createRouter } from "./routes/index.ts";
import { HTTP_HOSTNAME, HTTP_PORT } from "./config/config.ts";

export function startApp(): void {
  // Initialize MQTT handler
  mqttConnector.launch((error: Error) => {
    console.error("MQTT error:", error);
  });

  // Initialize HTTP server
  const router = createRouter();
  const app = new Application();
  app.use(router.routes());
  app.use(router.allowedMethods());

  console.log(`HTTP server listening on port ${HTTP_PORT}`);
  app.listen({ hostname: HTTP_HOSTNAME, port: HTTP_PORT });
}

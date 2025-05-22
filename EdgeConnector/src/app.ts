import { Application } from "../deps.ts";
import { createRouter } from "./routes/index.ts";
import { HTTP_HOSTNAME, HTTP_PORT, MQTT_BROKER_URL } from "./config/config.ts";
import mqttConnector from "./connectors/mqtt/connector.ts";

export function startApp(): void {
  // Initialize MQTT handler
  mqttConnector.init({ url: MQTT_BROKER_URL }, (error: Error) => {
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

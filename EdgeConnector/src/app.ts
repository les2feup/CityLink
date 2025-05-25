import { Application } from "../deps.ts";
import { getLogger, initLogger } from "./utils/log/log.ts";
import { createRouter } from "./routes/index.ts";
import { HTTP_HOSTNAME, HTTP_PORT, MQTT_BROKER_URL } from "./config/config.ts";
import mqttConnector from "./connectors/mqtt/connector.ts";

export function startApp(): void {
  initLogger();
  const logger = getLogger(import.meta.url);

  // Initialize MQTT handler
  mqttConnector.init({ url: MQTT_BROKER_URL }, (error: Error) => {
    logger.error("MQTT connection failed", error);
  });

  // Initialize HTTP server
  const router = createRouter();
  const app = new Application();
  app.use(router.routes());
  app.use(router.allowedMethods());

  logger.info(`HTTP server listening on ${HTTP_HOSTNAME}:${HTTP_PORT}`);
  app.listen({ hostname: HTTP_HOSTNAME, port: HTTP_PORT });
}

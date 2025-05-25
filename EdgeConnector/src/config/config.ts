import { log } from "../../deps.ts";

export const MQTT_BROKER_URL = "mqtt://127.0.0.1:1883";
export const HTTP_HOSTNAME = "127.0.0.1";
export const HTTP_PORT = 8080;

export const loggers: Record<string, log.LoggerConfig> = {
  "citylink": {
    level: "DEBUG",
    handlers: ["console"],
  },
  "citylink.connectors": {
    level: "DEBUG",
    handlers: ["console"],
  },
  "citylink.connectors.mqtt": {
    level: "DEBUG",
    handlers: ["console"],
  },
  "citylink.connectors.mqtt.registration": {
    level: "DEBUG",
    handlers: ["console"],
  },
  "citylink.controllers": {
    level: "DEBUG",
    handlers: ["console"],
  },
  "citylink.controllers.umqttCore": {
    level: "DEBUG",
    handlers: ["console"],
  },
  "citylink.services": {
    level: "DEBUG",
    handlers: ["console"],
  },
  "citylink.services.cache": {
    level: "DEBUG",
    handlers: ["console"],
  },
};

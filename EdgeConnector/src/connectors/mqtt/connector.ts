import { Buffer, mqtt, UUID } from "./../../../deps.ts";
import { registrationHandler } from "./registration.ts";
import cache from "../../services/cacheService.ts";
import umqttCore from "../../controllers/umqttCore.ts";

export type MqttConnectorOpts = {
  url: string;
};

type MessageHandler = (
  client: mqtt.MqttClient,
  message: Buffer,
) => Promise<void>;

//TODO: Maybe receive a TD for the EdgeConnector
//      and use it for the mqtt configuration
export function init(
  opts: MqttConnectorOpts,
  onError?: (error: Error) => void,
): void {
  const client = mqtt.connect(opts.url);

  const cleanup = () => {
    client.end(true, () => {
      console.log("MQTT client disconnected");
    });
  };

  client.on("connect", () => {
    console.log("Connected to the mqtt broker");

    client.subscribe("citylink/+/registration", (err) => {
      if (err) {
        onError?.(new Error("Error subscribing to registration topic"));
        cleanup();
      }

      console.log(
        "Subscribed to `registration` topic",
      );
    });

    client.subscribe("citylink/+/adaptation", (err) => {
      if (err) {
        onError?.(new Error("Error subscribing to adaptation ready topic"));
        cleanup();
      }

      console.log(
        "Subscribed to `adaptation` topic",
      );
    });
  });

  client.on("message", async (topic: string, message: Buffer) => {
    try {
      const handler = getMessageHandler(topic, opts);
      await handler(client, message);
    } catch (error) {
      if (error instanceof Error) {
        console.error(`Error processing message: ${error.message}`);
        onError?.(error);
      } else {
        console.error("Unknown error:", error);
        onError?.(new Error("Unknown error"));
      }
    }
  });

  client.on("error", (error: Error) => {
    onError?.(error);
  });
}

function getMessageHandler(
  topic: string,
  opts: MqttConnectorOpts,
): MessageHandler {
  const parts = topic.split("/");

  if (parts.length < 3 || parts[0] !== "citylink") {
    throw new Error("Malformed topic");
  }

  // action identifier is parts[2] onwards
  const endNodeID = parts[1];
  const actionName = parts.slice(2).join("/");

  switch (actionName) {
    case "registration": {
      return async (client, message) => {
        const res = await registrationHandler(client, endNodeID, message);
        if (res instanceof Error) {
          console.error(
            `Registration failed for end node ${endNodeID}: ${res.message}`,
          );
          return;
        }

        launchNodeController(res, opts);
      };
    }

    case "adaptation": {
      return async (client, message) => {
        console.log(
          `Received adaptation ready message for end node ${endNodeID}: ${message.toString()}`,
        );
      };
    }

    default: {
      throw new Error("Unknown action");
    }
  }
}

function launchNodeController(
  nodeId: UUID,
  opts: MqttConnectorOpts,
) {
  const node = cache.getEndNode(nodeId);
  if (!node) {
    console.error(`Node with ID ${nodeId} not found in cache.`);
    return;
  }
  if (node.controller) {
    console.warn(`Node with ID ${nodeId} already has a controller.`);
    return;
  }

  const controller = new umqttCore(nodeId, node.td, opts.url);
  controller.launch();
  cache.updateEndNode(nodeId, { controller });
  console.log(`Node controller launched for node ID ${nodeId}`);
}

export default {
  init,
};

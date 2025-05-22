import { Buffer, mqtt } from "./../../../deps.ts";
import { registrationHandler } from "./registration.ts";

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

    client.subscribe("citylink/+/adaptation/ready", (err) => {
      if (err) {
        onError?.(new Error("Error subscribing to adaptation ready topic"));
        cleanup();
      }

      console.log(
        "Subscribed to `adaptation/ready` topic",
      );
    });
  });

  client.on("message", async (topic: string, message: Buffer) => {
    try {
      const handler = parseTopic(topic);
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

function parseTopic(
  topic: string,
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
        await registrationHandler(client, endNodeID, message);
      };
    }

    case "adaptation/ready": {
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

export default {
  init,
};

import {
  CompositionOptions,
  ThingDescription,
  ThingModel,
  ThingModelHelpers,
} from "../../deps.ts";
import { createTemplateMapMQTT } from "./../models/templateMaps/mqttTemplateMap.ts";
import { MQTT_BROKER_URL } from "./../config/config.ts";
import cache from "./cacheService.ts";

export type InstantiationOpts = {
  endNodeUUID: string;
  selfComposition?: boolean;
  protocol: "mqtt" | "http" | "coap";
  extra?: {
    [key: string]: string; // custom fields
  };
}[];

export async function instantiateTDs(
  model: ThingModel,
  opts: InstantiationOpts,
): Promise<Error[] | null> {
  const errors: Error[] = [];
  const tmTools = new ThingModelHelpers();

  if (!model.title) {
    return [new Error("Model title is missing")];
  }

  const promises = opts.map(async (opt) => {
    const map = getTemplateMap(opt);
    if (map instanceof Error) {
      errors.push(map);
      return;
    }

    const options: CompositionOptions = {
      map,
      selfComposition: opt.selfComposition,
    };

    try {
      const tds = await tmTools.getPartialTDs(model, options);

      tds.forEach((td, index) => {
        td.id = `${map.CITYLINK_ID}${(index > 0) ? `:submodel:${index}` : ""}`;
        cache.setTD(model.title!, td.id, td as ThingDescription);
        console.log(
          `New Thing Description id "${td.id}" registered for model "${model.title}"`,
        );
      });
    } catch (error) {
      if (error instanceof Error) {
        errors.push(
          new Error(
            `Error during TD instantiation: ${error.message}`,
          ),
        );
      } else {
        errors.push(new Error("Unknown error during TD instantiation"));
      }
    }
  });

  await Promise.all(promises);
  return errors.length > 0 ? errors : null;
}

function getTemplateMap(
  opts: InstantiationOpts[number],
): Record<string, string> | Error {
  switch (opts.protocol) {
    case "mqtt": {
      const baseMap = createTemplateMapMQTT(
        MQTT_BROKER_URL,
        opts.endNodeUUID,
      );
      if (baseMap instanceof Error) {
        return baseMap;
      }

      return {
        ...baseMap,
        ...opts.extra,
      };
    }
    case "http":
      return new Error("HTTP protocol is not supported yet");
    case "coap":
      return new Error("CoAP protocol is not supported yet");
    default:
      return new Error(
        `Unsupported protocol: ${opts.protocol}`,
      );
  }
}

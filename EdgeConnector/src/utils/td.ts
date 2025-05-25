import {
  CompositionOptions,
  ThingDescription,
  ThingModel,
  ThingModelHelpers,
  UUID,
} from "../../deps.ts";
import { createTemplateMapMQTT } from "./../models/templateMaps/mqttTemplateMap.ts";
import { MQTT_BROKER_URL } from "./../config/config.ts";
import { getLogger } from "../utils/log/log.ts";

export type InstantiationOpts = {
  endNodeUUID: UUID;
  protocol: "mqtt" | "http" | "coap";
  extra?: {
    [key: string]: string; // custom fields
  };
};

export async function produceTD(
  model: ThingModel,
  opts: InstantiationOpts,
): Promise<ThingDescription | Error> {
  const logger = getLogger(import.meta.url);
  const tmTools = new ThingModelHelpers();
  if (!model.title) {
    return new Error("Model title is missing");
  }

  const map = getTemplateMap(opts);
  if (map instanceof Error) {
    return map;
  }

  const options: CompositionOptions = {
    map,
    selfComposition: true,
  };

  try {
    const [partialTD] = await tmTools.getPartialTDs(model, options);
    partialTD.id = map.CITYLINK_ID;

    logger.info(
      `New Thing Description id "${partialTD.id}" registered for model "${model.title}"`,
    );

    const td = fillPlatfromForms(partialTD, map);
    return createTopLevelForms(td, map);
  } catch (error) {
    if (error instanceof Error) {
      return new Error(
        `Error during TD instantiation: ${error.message}`,
      );
    } else {
      return new Error("Unknown error during TD instantiation");
    }
  }
}

function getTemplateMap(
  opts: InstantiationOpts,
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

//TODO: These properties should be published to the broker
//      with the retain flag set to true and qos set to 2.
//      Afterwards there is no need to publish them again.
//      Either that or remove the form from the TD since all
//      these properties **should** be read-only constants.
function fillPlatfromForms(
  td: WoT.ExposedThingInit,
  map: Record<string, string>,
): ThingDescription {
  const logger = getLogger(import.meta.url);
  const merge = (prop_name: string) => {
    return {
      readOnly: true,
      writeOnly: false,
      forms: [
        {
          href: map.CITYLINK_HREF,
          "mqv:filter": `${map.CITYLINK_PROPERTY}/platform/${prop_name}`,
          "mqv:qos": 1,
          "mqv:retain": true,
          op: "readproperty",
          contentType: "application/json",
        },
      ],
    };
  };

  const properties = td.properties!;
  const prefix = "citylink:platform_";
  // map over properties that start with the citylink:platfrom prefix
  // citylink:platform_<prop_name> and apply the merge
  for (const key of Object.keys(properties)) {
    if (key.startsWith(prefix) && !properties[key]?.forms) {
      const actualPropName = key.slice(prefix.length);
      const merged = merge(actualPropName);
      const original = properties[key]!;

      // Merge values (non-destructively)
      properties[key] = {
        ...original,
        ...merged,
        forms: [...(original.forms ?? []), ...merged.forms],
      };

      logger.debug("Filled platform form for", actualPropName, "in TD", td.id);
    }
  }

  return td as ThingDescription;
}

function createTopLevelForms(
  td: ThingDescription,
  map: Record<string, string>,
): ThingDescription {
  const logger = getLogger(import.meta.url);
  const topLevel = [
    {
      href: map.CITYLINK_HREF,
      "mqv:filter": `${map.CITYLINK_PROPERTY}/#`,
      op: [
        "observeallproperties",
        "unobserveallproperties",
      ],
      contentType: "application/json",
    },
    {
      href: map.CITYLINK_HREF,
      "mqv:filter": `${map.CITYLINK_EVENT}/#`,
      op: [
        "subscribeallevents",
        "unsubscribeallevents",
      ],
      contentType: "application/json",
    },
  ];

  // add the new top level forms into the forms array
  const prev = (td.forms || []) as NonNullable<ThingDescription["forms"]>;
  td.forms = [...prev, ...topLevel];
  logger.debug(
    `Added top-level forms to Thing Description ${td.id}`,
  );
  return td;
}

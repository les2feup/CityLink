import { z } from "../../../deps.ts";

const uuidPattern =
  /[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/i;

function regexCheckID(): [RegExp, { message: string }] {
  const regex = new RegExp(`^urn:uuid:${uuidPattern.source}$`);
  return [regex, {
    message: "CITYLINK_ID must be in the format urn:uuid:<uuid>",
  }];
}

function regexCheckAffordance(
  affordance: string,
  termination: string,
): [RegExp, { message: string }] {
  const regex = new RegExp(
    `^citylink/${uuidPattern.source}/${affordance}${termination}$`,
  );
  return [regex, {
    message:
      `Affordance must be in the format citylink/<uuid>/${affordance}[<none>|/core|/app]`,
  }];
}

function regexCheckHref(): [RegExp, { message: string }] {
  const regex = new RegExp(`^mqtts?:\/\/[^:\\s]+:\\d{1,5}\\/?$`);
  return [regex, {
    message: "CITYLINK_HREF must be in the format mqtt(s)://ip:port",
  }];
}

// List of fields grouped by affordance type
const affordanceTypes = ["PROPERTY", "ACTION", "EVENT"] as const;
const affordanceTerms = ["properties", "actions", "events"] as const;
const variants = ["", "CORE_", "APP_"] as const;
const terminations = ["", "/core", "/app"] as const;

const affordanceFieldEntries = affordanceTypes.flatMap((type) =>
  variants.map((variant) => {
    const key = `CITYLINK_${variant}${type}` as const;
    const affordance = affordanceTerms[affordanceTypes.indexOf(type)];
    const termination = terminations[variants.indexOf(variant)];
    return [
      key,
      z.string().regex(...regexCheckAffordance(affordance, termination)),
    ] as const;
  })
);

export const TemplateMapMQTT = z
  .object({
    CITYLINK_ID: z.string().regex(...regexCheckID()),
    CITYLINK_HREF: z.string().regex(...regexCheckHref()),

    CITYLINK_PROPERTY: z.string().regex(
      ...regexCheckAffordance("properties", ""),
    ),
    CITYLINK_ACTION: z.string().regex(...regexCheckAffordance("actions", "")),
    CITYLINK_EVENT: z.string().regex(...regexCheckAffordance("events", "")),

    CITYLINK_CORE_PROPERTY: z.string().regex(
      ...regexCheckAffordance("properties", "/core"),
    ),
    CITYLINK_CORE_ACTION: z.string().regex(
      ...regexCheckAffordance("actions", "/core"),
    ),
    CITYLINK_CORE_EVENT: z.string().regex(
      ...regexCheckAffordance("events", "/core"),
    ),

    CITYLINK_APP_PROPERTY: z.string().regex(
      ...regexCheckAffordance("properties", "/app"),
    ),
    CITYLINK_APP_ACTION: z.string().regex(
      ...regexCheckAffordance("actions", "/app"),
    ),
    CITYLINK_APP_EVENT: z.string().regex(
      ...regexCheckAffordance("events", "/app"),
    ),
  }).catchall(z.any())
  .superRefine((data, ctx) => {
    const extractUUID = (value: string): string => {
      const match = value.toLowerCase().match(uuidPattern);
      return match ? match[0] : "";
    };

    const baseUUID = extractUUID(data.CITYLINK_ID);

    const allMatch = affordanceFieldEntries.every(([key]) => {
      const anyData = data as Record<string, string>;
      return extractUUID(anyData[key]) === baseUUID;
    });

    if (!allMatch) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: "All CITYLINK UUIDs must match the one in CITYLINK_ID",
      });
    }
  });

export type TemplateMapMQTT = z.infer<typeof TemplateMapMQTT>;

export function createTemplateMapMQTT(
  brokerURL: string,
  endNodeUUID: string,
  extra?: Record<string, unknown>,
): TemplateMapMQTT | Error {
  const citylink_base = `citylink/${endNodeUUID}`;

  const properties_base = `${citylink_base}/properties`;
  const actions_base = `${citylink_base}/actions`;
  const events_base = `${citylink_base}/events`;

  const map = {
    CITYLINK_ID: `urn:uuid:${endNodeUUID}`,
    CITYLINK_HREF: brokerURL,

    CITYLINK_PROPERTY: properties_base,
    CITYLINK_ACTION: actions_base,
    CITYLINK_EVENT: events_base,

    CITYLINK_CORE_PROPERTY: `${properties_base}/core`,
    CITYLINK_CORE_ACTION: `${actions_base}/core`,
    CITYLINK_CORE_EVENT: `${events_base}/core`,

    CITYLINK_APP_PROPERTY: `${properties_base}/app`,
    CITYLINK_APP_ACTION: `${actions_base}/app`,
    CITYLINK_APP_EVENT: `${events_base}/app`,

    ...extra,
  };

  const parsedMap = TemplateMapMQTT.safeParse(map);
  if (!parsedMap.success) {
    console.error(JSON.stringify(parsedMap.error.format(), null, 2));
    return new Error("Invalid Template Map for MQTT");
  }

  return parsedMap.data;
}

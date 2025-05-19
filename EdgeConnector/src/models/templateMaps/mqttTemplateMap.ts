import { z } from "../../../deps.ts";

const uuidPattern =
  /[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/i;

function regexCheckID(): [RegExp, { message: string }] {
  const regex = new RegExp(String.raw`^urn:uuid:${uuidPattern.source}$`);
  return [regex, {
    message: `CITYLINK_ID must be in the format urn:uuid:<uuid>`,
  }];
}

function regexCheckAffordances(
  keyName: string,
  termination: string,
): [RegExp, { message: string }] {
  const regex = new RegExp(
    String.raw`^citylink\/${uuidPattern.source}\/${termination}$`,
  );

  return [regex, {
    message:
      `CITYLINK_${keyName} must be in the format citylink/<uuid>/${termination}`,
  }];
}

function regexCheckHref(): [RegExp, { message: string }] {
  const regex = new RegExp(
    String.raw`^mqtts?:\/\/[^:\s]+:\d{1,5}\/?$`,
  );
  return [regex, {
    message: "CITYLINK_HREF must be int the format mqtt(s)://ip:port",
  }];
}

export const TemplateMapMQTT = z
  .object({
    CITYLINK_ID: z.string().regex(...regexCheckID()),
    CITYLINK_PROPERTY: z.string().regex(
      ...regexCheckAffordances("PROPERTY", "properties"),
    ),
    CITYLINK_ACTION: z.string().regex(
      ...regexCheckAffordances("ACTION", "actions"),
    ),
    CITYLINK_EVENT: z.string().regex(
      ...regexCheckAffordances("EVENT", "events"),
    ),
    CITYLINK_HREF: z.string().regex(...regexCheckHref()),
  })
  .superRefine((data, ctx) => {
    const extractUUID = (value: string): string => {
      return value.toLowerCase().match(uuidPattern)![0];
    };

    const uuids = [
      extractUUID(data.CITYLINK_ID),
      extractUUID(data.CITYLINK_PROPERTY),
      extractUUID(data.CITYLINK_ACTION),
      extractUUID(data.CITYLINK_EVENT),
    ];

    const referenceUUID = uuids[0];
    const allMatch = uuids.every((uuid) => uuid === referenceUUID);

    if (!allMatch) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message:
          "All UUIDs in CITYLINK_ID, PROPERTY, ACTION, and EVENT must be the same",
      });
    }
  });

export type TemplateMapMQTT = z.infer<typeof TemplateMapMQTT>;

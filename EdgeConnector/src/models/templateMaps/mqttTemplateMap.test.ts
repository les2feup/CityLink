import { TemplateMapMQTT } from "./mqttTemplateMap.ts";
import { assert, randomUUID, z } from "../../../deps.ts";

Deno.test("valid mqtt TemplateMapMQTT passes validation", () => {
  const uuid = randomUUID();
  const validData = {
    CITYLINK_ID: `urn:uuid:${uuid}`,
    CITYLINK_HREF: "mqtt://12.2.3.1:1883",

    CITYLINK_PROPERTY: `citylink/${uuid}/properties`,
    CITYLINK_ACTION: `citylink/${uuid}/actions`,
    CITYLINK_EVENT: `citylink/${uuid}/events`,

    CITYLINK_CORE_PROPERTY: `citylink/${uuid}/properties/core`,
    CITYLINK_CORE_ACTION: `citylink/${uuid}/actions/core`,
    CITYLINK_CORE_EVENT: `citylink/${uuid}/events/core`,

    CITYLINK_APP_PROPERTY: `citylink/${uuid}/properties/app`,
    CITYLINK_APP_ACTION: `citylink/${uuid}/actions/app`,
    CITYLINK_APP_EVENT: `citylink/${uuid}/events/app`,
  };

  const result = TemplateMapMQTT.safeParse(validData);
  if (result.error) {
    console.error(JSON.stringify(result.error!.format(), null, 2));
  }
  assert.deepStrictEqual(validData, result.data);
});

Deno.test("valid mqtt TemplateMapMQTT with extra fields passes validation", () => {
  const uuid = randomUUID();
  const validData = {
    CITYLINK_ID: `urn:uuid:${uuid}`,
    CITYLINK_HREF: "mqtt://12.2.3.1:1883",

    CITYLINK_PROPERTY: `citylink/${uuid}/properties`,
    CITYLINK_ACTION: `citylink/${uuid}/actions`,
    CITYLINK_EVENT: `citylink/${uuid}/events`,

    CITYLINK_CORE_PROPERTY: `citylink/${uuid}/properties/core`,
    CITYLINK_CORE_ACTION: `citylink/${uuid}/actions/core`,
    CITYLINK_CORE_EVENT: `citylink/${uuid}/events/core`,

    CITYLINK_APP_PROPERTY: `citylink/${uuid}/properties/app`,
    CITYLINK_APP_ACTION: `citylink/${uuid}/actions/app`,
    CITYLINK_APP_EVENT: `citylink/${uuid}/events/app`,

    EXTRA_FIELD: "extra_value",
    ANOTHER_FIELD: 42,
    NESTED: {
      FIELD: "nested_value",
      NUMBER: 100,
    },
  };

  const result = TemplateMapMQTT.safeParse(validData);
  if (result.error) {
    console.error(JSON.stringify(result.error!.format(), null, 2));
  }
  assert.deepStrictEqual(validData, result.data);
});

Deno.test("valid mqtts TemplateMapMQTT passes validation", () => {
  const uuid = randomUUID();
  const validData = {
    CITYLINK_ID: `urn:uuid:${uuid}`,
    CITYLINK_HREF: "mqtts://12.2.3.1:1883",

    CITYLINK_PROPERTY: `citylink/${uuid}/properties`,
    CITYLINK_ACTION: `citylink/${uuid}/actions`,
    CITYLINK_EVENT: `citylink/${uuid}/events`,

    CITYLINK_CORE_PROPERTY: `citylink/${uuid}/properties/core`,
    CITYLINK_CORE_ACTION: `citylink/${uuid}/actions/core`,
    CITYLINK_CORE_EVENT: `citylink/${uuid}/events/core`,

    CITYLINK_APP_PROPERTY: `citylink/${uuid}/properties/app`,
    CITYLINK_APP_ACTION: `citylink/${uuid}/actions/app`,
    CITYLINK_APP_EVENT: `citylink/${uuid}/events/app`,
  };

  const result = TemplateMapMQTT.safeParse(validData);
  if (result.error) {
    console.error(JSON.stringify(result.error!.format(), null, 2));
  }
  assert.deepStrictEqual(validData, result.data);
});

Deno.test("throws when UUIDs do not match", () => {
  const uuid = randomUUID();
  const uuid2 = randomUUID();

  const invalidUUIDs = {
    CITYLINK_ID: `urn:uuid:${uuid}`,
    CITYLINK_HREF: "mqtt://localhost:1883",

    CITYLINK_PROPERTY: `citylink/${uuid}/properties`,
    CITYLINK_ACTION: `citylink/${uuid2}/actions`, // mismatch
    CITYLINK_EVENT: `citylink/${uuid}/events`,

    CITYLINK_CORE_PROPERTY: `citylink/${uuid}/properties/core`,
    CITYLINK_CORE_ACTION: `citylink/${uuid}/actions/core`,
    CITYLINK_CORE_EVENT: `citylink/${uuid}/events/core`,

    CITYLINK_APP_PROPERTY: `citylink/${uuid}/properties/app`,
    CITYLINK_APP_ACTION: `citylink/${uuid}/actions/app`,
    CITYLINK_APP_EVENT: `citylink/${uuid}/events/app`,
  };

  assert.throws(
    () => TemplateMapMQTT.parse(invalidUUIDs),
    z.ZodError,
    "All UUIDs in CITYLINK_ID, PROPERTY, ACTION, and EVENT must be the same",
  );
});

Deno.test("throws when CITYLINK_HREF is not a valid MQTT URL", () => {
  const uuid = randomUUID();
  const validFields = {
    CITYLINK_ID: `urn:uuid:${uuid}`,

    CITYLINK_PROPERTY: `citylink/${uuid}/properties`,
    CITYLINK_ACTION: `citylink/${uuid}/actions`,
    CITYLINK_EVENT: `citylink/${uuid}/events`,

    CITYLINK_CORE_PROPERTY: `citylink/${uuid}/properties/core`,
    CITYLINK_CORE_ACTION: `citylink/${uuid}/actions/core`,
    CITYLINK_CORE_EVENT: `citylink/${uuid}/events/core`,

    CITYLINK_APP_PROPERTY: `citylink/${uuid}/properties/app`,
    CITYLINK_APP_ACTION: `citylink/${uuid}/actions/app`,
    CITYLINK_APP_EVENT: `citylink/${uuid}/events/app`,
  };

  const invalidHrefs = [
    "https://broker.local",
    "mqtt://broker.local",
    "mqtts://:8883",
    "mqtts://broker.local:abc",
    "mqtts://broker.local:8883/extra/path",
  ];

  invalidHrefs.forEach((invalidHref) => {
    const invalidData = { ...validFields, CITYLINK_HREF: invalidHref };
    assert.throws(
      () => TemplateMapMQTT.parse(invalidData),
      z.ZodError,
      `${invalidHref} should not be parsed as a valid MQTT URL`,
    );
  });
});

Deno.test("throws when an invalid ID format is provided", () => {
  const uuid = randomUUID();
  const invalidUUID = {
    CITYLINK_ID: `urn:${uuid}`,
    CITYLINK_HREF: "mqtts://localhost:8883",

    CITYLINK_PROPERTY: `citylink/${uuid}/properties`,
    CITYLINK_ACTION: `citylink/${uuid}/actions`,
    CITYLINK_EVENT: `citylink/${uuid}/events`,

    CITYLINK_CORE_PROPERTY: `citylink/${uuid}/properties/core`,
    CITYLINK_CORE_ACTION: `citylink/${uuid}/actions/core`,
    CITYLINK_CORE_EVENT: `citylink/${uuid}/events/core`,

    CITYLINK_APP_PROPERTY: `citylink/${uuid}/properties/app`,
    CITYLINK_APP_ACTION: `citylink/${uuid}/actions/app`,
    CITYLINK_APP_EVENT: `citylink/${uuid}/events/app`,
  };

  assert.throws(
    () => TemplateMapMQTT.parse(invalidUUID),
    z.ZodError,
    "CITYLINK_ID must be in the format urn:uuid:<uuid>",
  );
});

Deno.test("throws when an invalid EVENT format is provided", () => {
  const uuid = randomUUID();
  const invalidUUID = {
    CITYLINK_ID: `urn:uuid:${uuid}`,
    CITYLINK_HREF: "mqtts://localhost:8883",

    CITYLINK_PROPERTY: `citylink/${uuid}/properties`,
    CITYLINK_ACTION: `citylink/${uuid}/actions`,
    CITYLINK_EVENT: `citylink/${uuid}`,

    CITYLINK_CORE_PROPERTY: `citylink/${uuid}/properties/core`,
    CITYLINK_CORE_ACTION: `citylink/${uuid}/actions/core`,
    CITYLINK_CORE_EVENT: `citylink/${uuid}/events/core`,

    CITYLINK_APP_PROPERTY: `citylink/${uuid}/properties/app`,
    CITYLINK_APP_ACTION: `citylink/${uuid}/actions/app`,
    CITYLINK_APP_EVENT: `citylink/${uuid}/events/app`,
  };

  assert.throws(
    () => TemplateMapMQTT.parse(invalidUUID),
    z.ZodError,
    "CITYLINK_EVENT must be in the format urn:uuid:<uuid>",
  );
});

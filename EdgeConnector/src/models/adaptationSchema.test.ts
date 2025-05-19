import { AdaptationSchema } from "./adaptationSchema.ts";
import { assert, randomUUID, z } from "../../deps.ts";

Deno.test("AdaptationSchema should validate a valid object", () => {
  const validObject = {
    endNodeUUID: randomUUID(),
    manifest: "https://example.com/manifest.json",
  };

  const result = AdaptationSchema.safeParse(validObject);
  assert.deepStrictEqual(result.data, validObject);
  assert(result.success, "Expected the object to be valid");
});

Deno.test("throws when endNodeUUID is not a UUID", () => {
  const invalidUUID = {
    endNodeUUID: "not-a-uuid",
    manifest: "https://example.com/manifest.json",
  };

  assert.throws(
    () => AdaptationSchema.parse(invalidUUID),
    z.ZodError,
    "Invalid uuid",
  );
});

Deno.test("throws when manifest is not a valid URL", () => {
  const invalidURL = {
    endNodeUUID: randomUUID(),
    manifest: "not-a-url",
  };

  assert.throws(
    () => AdaptationSchema.parse(invalidURL),
    z.ZodError,
    "Invalid url",
  );
});

import { RegistrationSchema } from "./registration.ts";
import { assert, z } from "../../deps.ts";

Deno.test("valid registration with explicit tmOnly", () => {
  const input = {
    manifest: "https://example.com/manifest.json",
    tmOnly: true,
  };

  const result = RegistrationSchema.parse(input);
  assert.deepStrictEqual(result, input);
});

Deno.test("valid registration with default tmOnly", () => {
  const input = {
    manifest: "https://example.com/manifest.json",
  };

  const result = RegistrationSchema.parse(input);
  assert.deepStrictEqual(result.tmOnly, false);
  assert.deepStrictEqual(result.manifest, input.manifest);
});

Deno.test("throws when manifest is not a URL", () => {
  const input = {
    manifest: "invalid-url",
  };

  assert.throws(
    () => RegistrationSchema.parse(input),
    z.ZodError,
    "Invalid url",
  );
});

Deno.test("throws when tmOnly is not a boolean", () => {
  const input = {
    manifest: "https://example.com/manifest.json",
    tmOnly: "yes",
  };

  assert.throws(
    () => RegistrationSchema.parse(input),
    z.ZodError,
    "Expected boolean, received string",
  );
});

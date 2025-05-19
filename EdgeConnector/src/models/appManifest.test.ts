import { AppContentTypes, AppManifest } from "./appManifest.ts";
import { assert, z } from "../../deps.ts";

Deno.test("AppContentTypes accepts valid types", () => {
  assert.deepStrictEqual(AppContentTypes.parse({ foo: 42 }), { foo: 42 });
  assert.deepStrictEqual(AppContentTypes.parse("some text"), "some text");
  assert.deepStrictEqual(
    AppContentTypes.parse(new Uint8Array([1, 2, 3])),
    new Uint8Array([1, 2, 3]),
  );
});

Deno.test("AppManifest parses valid manifest", () => {
  const manifest: AppManifest = {
    download: [
      {
        name: "firmware.bin",
        url: "https://example.com/fw.bin",
        contentType: "binary",
      },
    ],
    wot: {
      tm: {
        title: "Device TM",
        href: "https://example.com/tm.jsonld",
        version: {
          instance: "1.0.0",
          model: "1.0.0",
        },
      },
    },
  };

  const parsed = AppManifest.parse(manifest);
  assert.deepStrictEqual(parsed, manifest);
});

Deno.test("AppManifest uses default contentType if not specified", () => {
  const manifest = {
    download: [
      {
        name: "firmware.bin",
        url: "https://example.com/fw.bin",
      },
    ],
    wot: {
      tm: {
        href: "https://example.com/tm.jsonld",
        version: {
          instance: "1.0.0",
          model: "1.0.0",
        },
      },
    },
  };

  const parsed = AppManifest.parse(manifest);
  assert.deepStrictEqual(parsed.download[0].contentType, "binary");
});

Deno.test("AppManifest throws when download array is empty", () => {
  const manifest = {
    download: [],
    wot: {
      tm: {
        href: "https://example.com/tm.jsonld",
        version: {
          instance: "1.0.0",
          model: "1.0.0",
        },
      },
    },
  };

  assert.throws(
    () => AppManifest.parse(manifest),
    z.ZodError,
    "At least one download item is required",
  );
});

Deno.test("AppManifest throws on invalid download URL", () => {
  const manifest = {
    download: [
      {
        name: "firmware.bin",
        url: "not-a-url",
      },
    ],
    wot: {
      tm: {
        href: "https://example.com/tm.jsonld",
        version: {
          instance: "1.0.0",
          model: "1.0.0",
        },
      },
    },
  };

  assert.throws(
    () => AppManifest.parse(manifest),
    z.ZodError,
    "Invalid url",
  );
});

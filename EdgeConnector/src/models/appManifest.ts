import { z } from "../../deps.ts";

export const AppContentTypes = z.union(
  [z.instanceof(Uint8Array), z.string(), z.record(z.any())],
);
export type AppContentTypes = z.infer<typeof AppContentTypes>;

export const AppManifest = z.object({
  download: z.array(z.object({
    filename: z.string(),
    url: z.string().url(),
    contentType: z.enum(["json", "text", "binary"]).optional().default(
      "binary",
    ),
    sha256: z.string().regex(/^[a-f0-9]{64}$/),
  })).refine((items) => items.length > 0, {
    message: "At least one download item is required",
  }),
  wot: z.object({
    tm: z.object({
      title: z.string().optional(),
      href: z.string().url(),
      version: z.object({
        instance: z.string(),
        model: z.string(),
      }),
    }),
  }),
});
export type AppManifest = z.infer<typeof AppManifest>;

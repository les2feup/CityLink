import { z } from "../../deps.ts";

export const DlContentTypes = z.union(
  [z.record(z.any()), z.string(), z.instanceof(Uint8Array)],
);
export type DlContentTypes = z.infer<typeof DlContentTypes>;

export const DlMetadataItem = z.object({
  name: z.string(),
  url: z.string().url(),
  contentType: z.enum(["json", "text", "binary"]).optional().default("binary"),
});
export type DlMetadataItem = z.infer<typeof DlMetadataItem>;

export const DlMetadata = z.array(DlMetadataItem).refine(
  (items) => items.length > 0,
  {
    message: "At least one download item is required",
  },
);
export type DlMetadata = z.infer<typeof DlMetadata>;

export const WoTVersion = z.object({
  instance: z.string(),
  model: z.string(),
});
export type WoTVersion = z.infer<typeof WoTVersion>;

export const TmMetadata = z.object({
  title: z.string().optional(),
  href: z.string().url(),
  version: WoTVersion,
});
export type TmMetadata = z.infer<typeof TmMetadata>;

export const AppManifest = z.object({
  download: DlMetadata,
  wot: z.object({
    tm: TmMetadata,
  }),
});
export type AppManifest = z.infer<typeof AppManifest>;

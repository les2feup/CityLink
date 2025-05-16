import { z } from "../../deps.ts";
import { WoTVersion } from "./version.ts";

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

export const AppManifest = z.object({
  strategy: z.enum(["single", "multi"]),
  download: DlMetadata,
  wot: z.object({
    tmHref: z.string().url(),
    version: WoTVersion,
  }),
});
export type AppManifest = z.infer<typeof AppManifest>;

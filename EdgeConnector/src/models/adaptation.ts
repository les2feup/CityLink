import { z } from "../../deps.ts";

export const AdaptationSchema = z.object({
  endNodeUUID: z.string().uuid(),
  manifest: z.string().url(),
});
export type AdaptationSchema = z.infer<typeof AdaptationSchema>;

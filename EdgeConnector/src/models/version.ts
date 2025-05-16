import { z } from "../../deps.ts";

export const WoTVersion = z.object({
  instance: z.string(),
  model: z.string(),
});

export type WoTVersion = z.infer<typeof WoTVersion>;

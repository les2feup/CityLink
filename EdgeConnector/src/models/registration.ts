import { WoTVersion } from "./version.ts";
import { z } from "../../deps.ts";

export const RegistrationPayload = z.object({
  tmTitle: z.string().optional(),
  tmHref: z.string().url(),
  version: WoTVersion,
  pushApplication: z.boolean().optional().default(false),
});
export type RegistrationPayload = z.infer<typeof RegistrationPayload>;

import { z } from "../../deps.ts";

export const RegistrationPayload = z.object({
  manifest: z.string().url(),
  tmOnly: z.boolean().optional().default(false),
});
export type RegistrationPayload = z.infer<typeof RegistrationPayload>;

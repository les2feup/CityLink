import { z } from "../../deps.ts";

export const RegistrationSchema = z.object({
  manifest: z.string().url(),
  tmOnly: z.boolean().optional().default(false),
});
export type RegistrationSchema = z.infer<typeof RegistrationSchema>;

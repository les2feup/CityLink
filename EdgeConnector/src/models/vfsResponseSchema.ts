import { z } from "../../deps.ts";

export const VFSActionResponseSchema = z.object({
  timestamp: z.object({
    epoch_year: z.number().optional().default(1970),
    seconds: z.number().min(0),
  }),
  error: z.boolean(),
  action: z.enum(["write", "delete"]),
  message: z.union([
    z.string(), // Error or Write
    z.array(z.string()), // Delete
  ]),
});

export type VFSActionResponseSchema = z.infer<typeof VFSActionResponseSchema>;

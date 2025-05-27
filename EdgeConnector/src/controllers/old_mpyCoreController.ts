import { VFSActionResponseSchema } from "./../models/vfsResponseSchema.ts";
export type ActionName = "Write" | "Delete";

export type VFSDeleteInput = {
  path: string;
  recursive?: boolean;
};

export type VFSWriteInput = {
  path: string;
  payload: {
    data: string;
    hash: string;
    algo: "crc32";
  };
  append?: boolean;
};

export type VFSActionOutput = Pick<
  VFSActionResponseSchema,
  "timestamp" | "message"
>;

import { AppContentTypes } from "../models/appManifest.ts";
import { AppFetchSuccess } from "../services/appManifestService.ts";
import { VFSActionResponseSchema } from "./../models/vfsResponseSchema.ts";
import { crc32, encodeBase64 } from "../../deps.ts";

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

function responseHandler(
  action: ActionName,
  rawOutput: WoT.DataSchema,
): VFSActionOutput {
  const parsedOutput = VFSActionResponseSchema.safeParse(rawOutput);
  if (!parsedOutput.success) {
    throw new Error(
      `Invalid response for ${action} action: ${
        JSON.stringify(
          parsedOutput.error.format(),
          null,
          2,
        )
      }`,
    );
  }

  const { error, message } = parsedOutput.data;
  if (error) {
    throw new Error(`Error during ${action} action: ${message}`);
  }

  const expected = action.toLowerCase();
  const actual = parsedOutput.data.action;
  if (expected !== actual) {
    throw new Error(
      `Action mismatch: expected ${expected} but got ${actual}.`,
    );
  }

  return {
    timestamp: parsedOutput.data.timestamp,
    message: parsedOutput.data.message,
  };
}

function contentToBin(content: AppContentTypes): Uint8Array {
  switch (typeof content) {
    case "string":
      return new TextEncoder().encode(content);
    case "object": {
      if (content instanceof Uint8Array) {
        return content;
      }
      return new TextEncoder().encode(JSON.stringify(content));
    }
  }
}

export function VFSAction(
  thing: WoT.ConsumedThing,
  action: ActionName,
  input: VFSDeleteInput | VFSWriteInput,
): Promise<VFSActionOutput> {
  return new Promise<VFSActionOutput>((resolve, reject) => {
    const onResponse = (data: WoT.InteractionOutput) => {
      try {
        resolve(responseHandler(action, data.schema!));
      } catch (err) {
        reject(err);
      }
    };

    const onError = (err: Error) => {
      console.error(`Error deleting ${input.path}:`, err);
      reject(err);
    };

    console.log(
      `Subscribing to event citylink:embeddedCore_VFSActionResponse for ${action} action...`,
    );
    thing.subscribeEvent(
      "citylink:embeddedCore_VFSActionResponse",
      onResponse,
      onError,
    ).then(() => {
      console.log(
        `Subscribed to event citylink:embeddedCore_VFSActionResponse for ${action} action.`,
      );
      thing.invokeAction(`citylink:embeddedCore_VFS${action}`, input).then(
        () => {
          console.log(
            `Invoked action citylink:embeddedCore_VFS${action} with input:`,
            input,
          );
        },
      ).catch((err) => {
        console.error(
          `Error invoking action citylink:embeddedCore_VFS${action}:`,
          err,
        );
        reject(err);
      });
    }).catch(reject);
  });
}

export function performAdaptation(
  thing: WoT.ConsumedThing,
  cleanupList: string[],
  inputList: AppFetchSuccess[],
): Error | null {
  try {
    for (const entry of cleanupList) {
      const input: VFSDeleteInput = {
        path: entry,
      };

      VFSAction(thing, "Delete", input).then(() => {
        console.log(`File ${entry} deleted successfully.`);
      }).catch((err) => {
        console.error(`Error deleting file ${entry}:`, err);
        return err;
      });
    }

    for (const { name: path, content } of inputList) {
      const data = encodeBase64(contentToBin(content));
      const hash = `0x${(crc32(data) >>> 0).toString(16)}`;

      // convert contents to base64 data
      // compute crc32 of base64 data
      const input: VFSWriteInput = {
        path,
        payload: { data, hash, algo: "crc32" },
        append: false,
      };

      VFSAction(thing, "Write", input).then(() => {
        console.log(`File ${path} written successfully.`);
      }).catch((err) => {
        console.error(`Error writing file ${path}:`, err);
      });
    }
  } catch (err) {
    console.error("Error during adaptation:", err);
    return new Error(`Error during adaptation: ${err}`);
  }

  return null;
}

export default {
  VFSAction,
  performAdaptation,
};

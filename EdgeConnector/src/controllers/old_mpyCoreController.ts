import { AppContentTypes } from "../models/appManifest.ts";
import { AppFetchSuccess } from "../services/appManifestService.ts";
import { VFSActionResponseSchema } from "./../models/vfsResponseSchema.ts";
import { Buffer, crc32, encodeBase64, ThingDescription } from "../../deps.ts";
import { invokeAction, subscribeEvent } from "../services/tdService.ts";
import { getLogger } from "../utils/log/log.ts";
const logger = getLogger(import.meta.url);

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

export function VFSAction(
  td: ThingDescription,
  action: ActionName,
  input: VFSDeleteInput | VFSWriteInput,
): Promise<VFSActionOutput> {
  return new Promise<VFSActionOutput>((resolve, reject) => {
    let cancelSubscription: (() => void) | null = null;
    let isSettled = false;

    const cleanup = () => {
      if (cancelSubscription) {
        cancelSubscription();
        cancelSubscription = null;
      }
    };

    const onEvent = (_topic: string, data: Buffer) => {
      cleanup();
      try {
        const output = responseHandler(action, data);
        if (!isSettled) {
          isSettled = true;
          resolve(output);
        }
      } catch (err) {
        if (!isSettled) {
          isSettled = true;
          reject(err);
        }
      }
    };

    const onError = (err: Error) => {
      cleanup();
      if (!isSettled) {
        isSettled = true;
        reject(err);
      }
    };

    const onPublish = (_topic: string) => {};

    const onSubscribe = (_topic: string) => {
      logger.debug("Invoking VFS action:", action);
      const ret = invokeAction(
        td,
        `citylink:embeddedCore_VFS${action}`,
        JSON.stringify(input),
        onPublish,
        onError,
      );
      if (ret instanceof Error) {
        cleanup();
        reject(ret);
      }
    };

    const result = subscribeEvent(
      td,
      "citylink:embeddedCore_VFSActionResponse",
      onEvent,
      onSubscribe,
      onError,
    );

    if (result instanceof Error) {
      reject(result);
    } else {
      cancelSubscription = result;
    }

    setTimeout(() => {
      cleanup();
      if (!isSettled) {
        isSettled = true;
        reject(new Error("Timeout waiting for VFS action response."));
      }
    }, 60000); // 1 minute timeout
  });
}

export function performAdaptation(
  td: ThingDescription,
  cleanupList: string[],
  inputList: AppFetchSuccess[],
): Error | null {
  if (!td) {
    return new Error("ThingDescription is null or undefined.");
  }

  if (!Array.isArray(cleanupList)) {
    logger.error("cleanupList is not an array:", cleanupList);
  }

  if (!Array.isArray(inputList)) {
    logger.error("inputList is not an array:", inputList);
  }

  try {
    logger.info("Cleaning up files...");

    for (const entry of cleanupList) {
      const input: VFSDeleteInput = {
        path: entry,
      };

      VFSAction(td, "Delete", input).then(() => {
        logger.info(`File ${entry} deleted successfully.`);
      }).catch((err) => {
        logger.error(`Error deleting file ${entry}:`, err);
        return err;
      });

      logger.info(`File ${entry} deleted successfully.`);
    }

    logger.info("Writing files...");
    logger.info("inputList has", inputList.length, "items");

    for (const { path, url, content } of inputList) {
      logger.info("Handling file:", path, url);
      const data = encodeContent(content);
      const hash = `0x${(crc32(data) >>> 0).toString(16)}`;

      logger.info(`File ${path} has hash: ${hash}`);

      // convert contents to base64 data
      // compute crc32 of base64 data
      const writeInput: VFSWriteInput = {
        path,
        payload: { data, hash, algo: "crc32" },
        append: false,
      };

      logger.info(`Writing file ${path} with data:`, data);

      VFSAction(td, "Write", writeInput).then(() => {
        logger.info(`File ${path} written successfully.`);
      }).catch((err) => {
        logger.error(`VFSWrite action error during upload of ${path}:`, err);
      });
    }

    const res = invokeAction(td, "citylink:embeddedCore_reload", "");
    if (res instanceof Error) {
      logger.error("Failed to issue device reload:", res);
      return res;
    }
  } catch (err) {
    logger.error("Error during adaptation:", err);
    return new Error(`Error during adaptation: ${err}`);
  }

  return null;
}

function responseHandler(
  action: ActionName,
  rawOutput: Buffer,
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

function encodeContent(content: AppContentTypes): string {
  switch (typeof content) {
    case "string":
      return encodeBase64(content);
    case "object": {
      if (content instanceof Uint8Array) {
        return encodeBase64(content);
      }
      return encodeBase64(JSON.stringify(content));
    }
  }
}

export default {
  VFSAction,
  performAdaptation,
};

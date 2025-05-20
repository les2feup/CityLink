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

    thing.subscribeEvent(
      "citylink:embeddedCore_VFSActionResponse",
      onResponse,
      onError,
    ).then(() => {
      return thing.invokeAction(`citylink:embeddedCore_VFS${action}`, input);
    }).catch(reject);
  });
}

export function performAdaptation(
  thing: WoT.ConsumedThing,
  _cleanupList: string[],
  inputList: { path: string; content: string }[],
): void {
  for (const entry of inputList) {
    const { path, content } = entry;
    // convert contents to base64 data
    // compute crc32 of base64 data
    const input: VFSWriteInput = {
      path,
      payload: {
        data: "foo", // TODO: replace with base64 encoded content
        hash: "bar", // TODO: replace with crc32 hash of base64 encoded content
        algo: "crc32",
      },
      append: false,
    };

    VFSAction(thing, "Write", input).then(() => {
      console.log(`File ${path} written successfully.`);
    }).catch((err) => {
      console.error(`Error writing file ${path}:`, err);
    });
  }
}

export default {
  VFSAction,
  performAdaptation,
};

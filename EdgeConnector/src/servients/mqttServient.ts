import { AppContentTypes } from "./../models/appManifest.ts";
import cache from "./../services/cacheService.ts";
import { MqttClientFactory, Servient, ThingDescription } from "../../deps.ts";

async function init(
  endNodeUUID: string,
) {
  const servient: Servient = new Servient();
  servient.addClientFactory(new MqttClientFactory());

  const td = cache.getTDbyUUID(`urn:uuid:${endNodeUUID}`);
  if (!td) {
    return new Error(
      `td for end node with UUID "${endNodeUUID}" not found.`,
    );
  }

  try {
    const cleanupList: string[] = [];
    const WoT = await servient.start();
    const thing = await WoT.consume(td);
    const adaptCB = adaptWrapper(thing, cleanupList);

    return {
      servient,
      adaptCB,
    };
  } catch (err) {
    console.error(
      `Error while parsing cleanupList for end node with UUID "${endNodeUUID}": ${err}`,
    );
  }
}

type VFSWriteInput = {
  path: string;
  payload: {
    data: string;
    hash: string;
    algo: "crc32";
  };
  append?: boolean;
};

function adaptWrapper(thing: WoT.ConsumedThing, cleanupList: string[]) {
  return async (
    source: VFSWriteInput[],
  ) => {
    const error = await adapt(thing, cleanupList, source);
    if (error) {
      console.error(
        `Adaptation error for ${thing.getThingDescription().id}: ${error}`,
      );
    }
  };
}

async function adapt(
  thing: WoT.ConsumedThing,
  _cleanupList: string[],
  _source: VFSWriteInput[],
): Promise<Error | null> {
  await deleteEndNodeFiles(thing, ["main.py"]);

  return null;
}

// Deletes files from the end node, based on the cleanupList data
// deletion requests are done with the citylink:embeddedCore_VFSDelete action
// the action output is received via citylink:embeddedCore_VFSActionResponse event
// Requests must be done sequentially and the process must be aborted in case of an error
async function deleteEndNodeFiles(
  thing: WoT.ConsumedThing,
  cleanupList: string[],
): Promise<void> {
  const deleteFile = (filename: string): Promise<boolean> => {
    return new Promise<boolean>((resolve, reject) => {
      const onResponse = (data: WoT.InteractionOutput) => {
        try {
          // You might want to validate or coerce schema here
          data.value().then((val) => {
            console.log(
              `Received response for ${filename}:`,
              JSON.stringify(val, null, 2),
            );
          });
          resolve(true);
        } catch (err) {
          reject(err);
        } finally {
          // thing.unsubscribeEvent("citylink:embeddedCore_VFSActionResponse", onResponse);
        }
      };

      const onError = (err: Error) => {
        console.error(`Error deleting file ${filename}:`, err);
        reject(err);
        // thing.unsubscribeEvent( "citylink:embeddedCore_VFSActionResponse", onError,);
      };

      thing.subscribeEvent(
        "citylink:embeddedCore_VFSActionResponse",
        onResponse,
        onError,
      ).then(() => {
        return thing.invokeAction("citylink:embeddedCore_VFSDelete", {
          path: filename,
        });
      }).catch(reject);
    });
  };

  for (const file of cleanupList) {
    const sucess = await deleteFile(file);
    if (!sucess) {
      break;
    }
  }
}

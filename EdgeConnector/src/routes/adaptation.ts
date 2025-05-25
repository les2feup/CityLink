import { Router } from "../../deps.ts";
import { AdaptationSchema } from "../models/adaptationSchema.ts";
import cache from "./../services/cache.ts";
import mpyCoreController from "./../controllers/mpyCoreController.ts";
import {
  AppFetchSuccess,
  fetchAppManifest,
  fetchAppSrc,
  filterAppFetchErrors,
} from "../services/appManifestService.ts";

function adaptEndNode(
  endNodeUUID: string,
  appSrc: AppFetchSuccess[],
): Error | null {
  const td = cache.getTDbyUUID(`urn:uuid:${endNodeUUID}`);
  if (!td) {
    return new Error(
      `td for end node with UUID "${endNodeUUID}" not found.`,
    );
  }

  try {
    return mpyCoreController.performAdaptation(td, [], appSrc);
  } catch (err) {
    return new Error(
      `Error while adapting end node with UUID "${endNodeUUID}": ${err}`,
    );
  }
}

export function createApadationProtocolRouter(): Router {
  const router = new Router();

  router.post("/adaptation", async (ctx) => {
    if (!ctx.request.hasBody) {
      ctx.response.status = 400;
      ctx.response.body = "Bad Request: No body found";
      return;
    }

    try {
      const body = await ctx.request.body.json();
      const data = AdaptationSchema.safeParse(body);
      if (!data.success) {
        throw new Error(
          JSON.stringify(data.error.format(), null, 2),
        );
      }

      const schema = data.data;
      const appManifest = await fetchAppManifest(schema.manifest);
      if (appManifest instanceof Error) {
        throw appManifest;
      }

      const fetchResult = await fetchAppSrc(appManifest.download);
      const fetchErrors = filterAppFetchErrors(fetchResult);
      if (fetchErrors.length > 0) {
        throw new Error(
          `${
            fetchErrors
              .map((e) => e.error)
              .join(", ")
          }`,
        );
      }

      const appSource = fetchResult as AppFetchSuccess[];
      const res = adaptEndNode(schema.endNodeUUID, appSource);
      if (res instanceof Error) {
        throw res;
      }

      ctx.response.status = 201;
      ctx.response.body = { status: "ok", message: "Adaptation successful" };
    } catch (err) {
      ctx.response.status = 500;
      if (err instanceof Error) {
        ctx.response.body = `Internal server error: ${err.message}`;
      } else {
        ctx.response.body = `Internal server error: ${err}`;
      }
    }
  });

  return router;
}

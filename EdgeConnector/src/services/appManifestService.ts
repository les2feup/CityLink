import { AppContentTypes, AppManifest } from "../models/appManifest.ts";
import { createHash } from "../../deps.ts";
import cache from "./cacheService.ts";

type DownloadMetadata = AppManifest["download"];
type DownloadMetadataItem = DownloadMetadata[number];

export type FetchSuccess = {
  name: string;
  url: string;
  content: AppContentTypes;
};

export type FetchError = {
  url: string;
  error: Error;
};

export type FetchResult = FetchSuccess | FetchError;

export async function fetchAppManifest(
  url: string,
): Promise<AppManifest | Error> {
  // before fetching, try the manifest cache
  const cachedManifest = cache.getManifest(url);
  if (cachedManifest) {
    return cachedManifest;
  }

  try {
    const response = await fetch(url);
    if (!response.ok) {
      return new Error(`Failed to fetch app manifest: ${response.statusText}`);
    }
    const json = await response.json();
    const parsed = AppManifest.safeParse(json);
    if (!parsed.success) {
      return new Error(
        `Invalid app manifest: ${
          JSON.stringify(parsed.error.format(), null, 2)
        }`,
      );
    }

    cache.setManifest(url, parsed.data);
    return parsed.data;
  } catch (error) {
    return new Error(`Error fetching app manifest: ${error}`);
  }
}

export async function fetchAppSrc(
  download: DownloadMetadata,
): Promise<FetchResult[]> {
  const results: FetchResult[] = [];
  const fetchPromises = download.map(async (mdata) => {
    const result = await fetchSingleFile(mdata);
    results.push(result);
  });

  await Promise.all(fetchPromises);
  return results;
}

async function fetchSingleFile(
  mdata: DownloadMetadataItem,
): Promise<FetchSuccess | FetchError> {
  // before fetching, try the file cache
  const cachedFile = cache.getAppContent(mdata.url);
  if (cachedFile) {
    return { name: mdata.filename, url: mdata.url, content: cachedFile };
  }

  try {
    const response = await fetch(mdata.url);
    if (!response.ok) {
      return {
        url: mdata.url,
        error: new Error(`Failed to fetch file: ${response.statusText}`),
      };
    }

    let content: AppContentTypes;
    let hashable: Uint8Array;
    switch (mdata.contentType) {
      case "json": {
        content = await response.json();
        hashable = new TextEncoder().encode(JSON.stringify(content));
        break;
      }
      case "text": {
        content = await response.text();
        hashable = new TextEncoder().encode(content);
        break;
      }
      case "binary": {
        content = await response.bytes();
        hashable = content as Uint8Array;
        break;
      }

      default: {
        return {
          url: mdata.url,
          error: new Error(`Unsupported content type: ${mdata.contentType}`),
        };
      }
    }

    const sha256 = createHash("sha256");
    sha256.update(hashable);
    const digested = sha256.digest("hex");
    if (digested !== mdata.sha256) {
      return {
        url: mdata.url,
        error: new Error(
          `SHA256 mismatch for ${mdata.filename}: expected ${mdata.sha256}, got ${digested}`,
        ),
      };
    }

    cache.setAppContent(mdata.url, content);
    return { name: mdata.filename, url: mdata.url, content };
  } catch (error) {
    return {
      url: mdata.url,
      error: new Error(`Error fetching file: ${error}`),
    };
  }
}

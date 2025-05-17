import {
  AppManifest,
  DlContentTypes,
  DlMetadata,
  DlMetadataItem,
} from "../models/appManifest.ts";

import cache from "./cacheService.ts";

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

type FetchSuccess = {
  name: string;
  url: string;
  content: DlContentTypes;
};

type FetchError = {
  url: string;
  error: Error;
};

type FetchResult = FetchSuccess | FetchError;

export async function fetchAppSrc(
  download: DlMetadata,
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
  mdata: DlMetadataItem,
): Promise<FetchSuccess | FetchError> {
  // before fetching, try the file cache
  const cachedFile = cache.getFile(mdata.url);
  if (cachedFile) {
    return { name: mdata.name, url: mdata.url, content: cachedFile };
  }

  try {
    const response = await fetch(mdata.url);
    if (!response.ok) {
      return {
        url: mdata.url,
        error: new Error(`Failed to fetch file: ${response.statusText}`),
      };
    }

    let content: DlContentTypes;
    switch (mdata.contentType) {
      case "json": {
        content = await response.json();
        break;
      }
      case "text": {
        content = await response.text();
        break;
      }
      case "binary": {
        content = await response.bytes();
        break;
      }

      default: {
        return {
          url: mdata.url,
          error: new Error(`Unsupported content type: ${mdata.contentType}`),
        };
      }
    }
    cache.setFile(mdata.url, content);
    return { name: mdata.name, url: mdata.url, content };
  } catch (error) {
    return {
      url: mdata.url,
      error: new Error(`Error fetching file: ${error}`),
    };
  }
}

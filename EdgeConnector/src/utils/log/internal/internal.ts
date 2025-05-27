import { log, path } from "../../../../deps.ts";

export function getLoggerName(
  moduleUrl: string,
  conf: log.LogConfig,
  baseDir: string = Deno.cwd(),
): string {
  const filePath = path.fromFileUrl(moduleUrl);
  const relativePath = path.relative(baseDir, filePath);

  // If the relative path goes up to the root, return "default"
  if (relativePath.startsWith("..")) {
    return "default";
  }

  const clean = relativePath
    .replace(/\.(ts|js|tsx|jsx)$/, "") // remove file extension
    .replace(new RegExp(`\\${path.SEPARATOR}`, "g"), "."); // path -> dotted

  const candidate = (() => {
    if (clean.startsWith("src")) {
      return clean.replace(/^src\./, "citylink.");
    }
    return `citylink.${clean}`;
  })();

  // Check if the candidate logger exists in logConfig
  if (conf.loggers![candidate]) {
    return candidate;
  }

  // iterativelly strip the last segment, checking if the candidate logger exists
  // until we reach the root or find a match
  // Ex: "src/controllers/exampleController.ts"
  // first try: "citylink.controllers.exampleController"
  // second try: "citylink.controllers"
  // third try: "citylink"
  // final: "default"
  const segments = candidate.split(".");
  while (segments.length > 0) {
    segments.pop(); // remove last segment
    const candidate = segments.join(".");
    if (conf.loggers![candidate]) {
      return candidate;
    }
  }

  // If no matching logger found, return "default"
  return "default";
}

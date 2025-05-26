import { bold, dim, log, white } from "../../../deps.ts";
import { getLoggerName } from "./internal/internal.ts";
import { loggers } from "../../config/config.ts";

function hasContext(arg: unknown): arg is { $context: Record<string, string> } {
  return typeof arg === "object" && arg !== null && "$context" in arg;
}

function customFormatter(record: log.LogRecord): string {
  const timestamp = dim(white(new Date(record.datetime).toISOString())); // or customize format
  const levelTag = bold(record.levelName);
  const loggerTag = bold(`[${record.loggerName}]`);

  let contextStr = "";

  for (const arg of record.args) {
    if (hasContext(arg)) {
      const context = arg.$context;
      contextStr = Object.entries(context)
        .map(([k, v]) => `${k}=${v}`)
        .join(" ");
      break; // Only use the first `$context` found
    }
  }

  const contextfmt = contextStr ? ` ${dim(contextStr)} ` : " ";

  const lines: string[] = [
    `${timestamp} | ${levelTag} ${loggerTag}${contextfmt}${record.msg}`
      .trim(),
  ];

  for (const arg of record.args) {
    if (hasContext(arg)) continue;

    let nextLine = "";
    if (typeof arg === "object") {
      nextLine = Deno.inspect(arg, { colors: true });
    } else if (arg instanceof Error) {
      nextLine = arg.stack ?? arg.toString();
    } else {
      nextLine = String(arg);
    }

    lines.push(dim(white(nextLine)));
  }

  return lines.join(" ");
}

const logConfig: log.LogConfig = {
  handlers: {
    console: new log.ConsoleHandler("DEBUG", {
      formatter: customFormatter,
    }),
  },
  loggers: {
    default: {
      level: "INFO",
      handlers: ["console"],
    },
    ...loggers,
  },
};

export function initLogger(
  config: log.LogConfig = logConfig,
): void {
  log.setup(config);
  log.info("Logger initialized.");
}

// Based on the current module's import meta, get the closest matching logger
// from the loggers defined in the logConfig.
// If there are not matches, return the default logger.
export function getLogger(
  metaUrl: string,
  baseDir: string = Deno.cwd(),
): log.Logger {
  const loggerName = getLoggerName(metaUrl, logConfig, baseDir);
  return log.getLogger(loggerName) || log.getLogger("default");
}

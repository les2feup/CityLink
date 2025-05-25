import { bold, dim, log, white } from "../../../deps.ts";
import { getLoggerName } from "./internal/internal.ts";

function coloredFormatter(record: log.LogRecord): string {
  const levelTag = bold(record.levelName);
  const loggerTag = bold(`[${record.loggerName}]`);

  const lines: string[] = [`${levelTag} ${loggerTag} ${record.msg}`];
  for (const arg of record.args) {
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

export const logConfig: log.LogConfig = {
  handlers: {
    console: new log.ConsoleHandler("DEBUG", {
      formatter: coloredFormatter,
    }),
  },
  loggers: {
    default: {
      level: "INFO",
      handlers: ["console"],
    },
    "citylink": {
      level: "INFO",
      handlers: ["console"],
    },
    "citylink.connectors": {
      level: "INFO",
      handlers: ["console"],
    },
    "citylink.connectors.mqtt": {
      level: "INFO",
      handlers: ["console"],
    },
    "citylink.controllers": {
      level: "INFO",
      handlers: ["console"],
    },
    "citylink.controllers.umqttCore": {
      level: "INFO",
      handlers: ["console"],
    },
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
  metaUrl: string = import.meta.url,
  baseDir: string = Deno.cwd(),
): log.Logger {
  const loggerName = getLoggerName(metaUrl, logConfig, baseDir);
  return log.getLogger(loggerName) || log.getLogger("default");
}

import { assert, log } from "../../../../deps.ts";
import { getLoggerName } from "./internal.ts";

Deno.test("getLoggerName returns default logger for unknown module", () => {
  const config: log.LogConfig = {
    loggers: {
      default: {
        level: "INFO",
        handlers: ["console"],
      },
    },
  };
  const loggerName = getLoggerName("file:///unknown/module.ts", config);
  assert.strictEqual(loggerName, "default");
});

Deno.test("getLoggerName returns correct logger for known module", () => {
  const moduleUrl = `file://${Deno.cwd()}/src/controllers/exampleController.ts`;
  const config: log.LogConfig = {
    loggers: {
      "citylink.controllers.exampleController": {
        level: "INFO",
        handlers: ["console"],
      },
      default: {
        level: "INFO",
        handlers: ["console"],
      },
    },
  };
  const loggerName = getLoggerName(moduleUrl, config);
  assert.strictEqual(loggerName, "citylink.controllers.exampleController");
});

Deno.test("getLoggerName return the closest matching logger", () => {
  const moduleUrl =
    `file://${Deno.cwd()}/src/controllers/nested/exampleController.ts`;

  const moduleUrl2 =
    `file://${Deno.cwd()}/src/controllers/nested/somethingElse.ts`;

  const config: log.LogConfig = {
    loggers: {
      "citylink.controllers.nested.exampleController": {
        level: "INFO",
        handlers: ["console"],
      },
      "citylink.controllers.nested": {
        level: "DEBUG",
        handlers: ["console"],
      },
      default: {
        level: "INFO",
        handlers: ["console"],
      },
    },
  };
  const loggerName = getLoggerName(moduleUrl, config);
  assert.strictEqual(
    loggerName,
    "citylink.controllers.nested.exampleController",
  );

  const loggerName2 = getLoggerName(moduleUrl2, config);
  assert.strictEqual(loggerName2, "citylink.controllers.nested");
});

import { log } from "../../../deps.ts";

export class ContextualLogger {
  constructor(
    private logger: log.Logger,
    private context: Record<string, string>,
  ) {}

  private wrapArgs(msg: unknown, args: unknown[]): [unknown, ...unknown[]] {
    return [msg, { $context: this.context }, ...args];
  }

  setContext(context: Record<string, string>) {
    this.context = { ...this.context, ...context };
  }

  debug(msg: unknown, ...args: unknown[]) {
    this.logger.debug(...this.wrapArgs(msg, args));
  }

  info(msg: unknown, ...args: unknown[]) {
    this.logger.info(...this.wrapArgs(msg, args));
  }

  warn(msg: unknown, ...args: unknown[]) {
    this.logger.warn(...this.wrapArgs(msg, args));
  }

  error(msg: unknown, ...args: unknown[]) {
    this.logger.error(...this.wrapArgs(msg, args));
  }

  critical(msg: unknown, ...args: unknown[]) {
    this.logger.critical(...this.wrapArgs(msg, args));
  }
}

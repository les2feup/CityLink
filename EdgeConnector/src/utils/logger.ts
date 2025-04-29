// src/utils/logger.ts
export function logInfo(message: string, ...params: unknown[]) {
  console.log("[INFO]", message, ...params);
}

export function logError(message: string, ...params: unknown[]) {
  console.error("[ERROR]", message, ...params);
}

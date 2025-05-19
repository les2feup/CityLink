import { z } from "../../deps.ts";
import { TemplateMapMQTT } from "./templateMaps/mqttTemplateMap.ts";

export const TemplateMaps = z.object({ mqtt: TemplateMapMQTT.optional() });
export type TemplateMaps = z.infer<typeof TemplateMaps>;

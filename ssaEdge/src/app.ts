import { Application, ThingModel, ThingDescription, ThingModelHelpers } from "../deps.ts";
import { loadAllThingModels } from "./services/thingModelService.ts";
import { setupMQTT } from "./controllers/mqttController.ts";
import { createAppRouter} from "./routes/index.ts";
import { HTTP_PORT, HTTP_HOSTNAME } from "./config/config.ts";

export function startApp(): void {
  // Shared state: Map<model, Map<uuid, ThingDescription>>
  const hostedThings = new Map<string, Map<string, ThingDescription>>();
  const hostedModels = new Map<string, ThingModel>();
  const tmTools = new ThingModelHelpers();

  loadAllThingModels().then((models) => {
    for (const [name, model] of models) {
      hostedModels.set(name, model);
    }
  });

  // Initialize MQTT handler
  setupMQTT(tmTools, hostedThings);

  // Initialize HTTP server
  const router = createAppRouter(hostedThings, hostedModels);
  const app = new Application();
  app.use(router.routes());
  app.use(router.allowedMethods());

  console.log(`HTTP server listening on port ${HTTP_PORT}`);
  app.listen({ hostname: HTTP_HOSTNAME, port: HTTP_PORT });
}

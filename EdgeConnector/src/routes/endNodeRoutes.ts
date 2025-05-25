import { Router, ThingModel } from "../../deps.ts";
import cache, { EndNode } from "../services/cache.ts";

export function createEndNodeRouter(): Router {
  const router = new Router();

  router.get("/endnodes", (ctx) => {
    const url = new URL(ctx.request.url);
    const selectedTM = url.searchParams.get("model");

    // --- Utilities ---
    const getTMTitleByInstance = (tm: ThingModel): string | undefined =>
      [...cache.rawTMCache().entries()].find(([_, model]) => model === tm)?.[0];

    const allNodeEntries: [string, EndNode][] = Array.from(
      cache.rawEndNodeCache().entries(),
    ).flatMap(([uuid]) => {
      const node = cache.getEndNode(uuid);
      return node ? [[uuid, node]] : [];
    });

    const filteredNodes = selectedTM
      ? allNodeEntries.filter(([, node]) =>
        getTMTitleByInstance(node.tm) === selectedTM
      )
      : allNodeEntries;

    const uniqueTMTitles = Array.from(
      new Set(
        cache.getEndNode(() => true)
          .map((n) => getTMTitleByInstance(n.tm))
          .filter((x): x is string => !!x),
      ),
    );

    const optionsHTML = uniqueTMTitles.map((tm) =>
      `<option value="${tm}" ${
        tm === selectedTM ? "selected" : ""
      }>${tm}</option>`
    ).join("");

    const listItemsHTML = filteredNodes.map(([uuid, node], index) => {
      const tmTitle = getTMTitleByInstance(node.tm);
      const name = node.manifest.wot.tm.title ?? "Unnamed";
      const tmLink = tmTitle ? `/models/${encodeURIComponent(tmTitle)}` : "#";
      const tdLink = `/tds/${uuid}`;
      const manifestLink = `/manifests/${uuid}`;

      return `
        <li>
          Node ${index + 1} — ${name}
          <ul>
            <li><a href="${tmLink}">Thing Model</a></li>
            <li><a href="${tdLink}">Thing Description</a></li>
            <li><a href="${manifestLink}">Application Manifest</a></li>
          </ul>
        </li>`;
    }).join("");

    // --- HTML Template ---
    const html = `
      <html>
        <head><title>Registered End Nodes</title></head>
        <body>
          <h1>Registered End Nodes</h1>
          <form method="GET" action="/endnodes">
            <label for="model">Filter by Thing Model:</label>
            <select name="model" id="model" onchange="this.form.submit()">
              <option value="">-- All --</option>
              ${optionsHTML}
            </select>
          </form>
          <ul>
            ${listItemsHTML || "<li>No end nodes found for this model.</li>"}
          </ul>
        </body>
      </html>`;

    ctx.response.type = "text/html";
    ctx.response.body = html;
  });

  return router;
}

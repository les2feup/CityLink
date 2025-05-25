import { Router } from "../../deps.ts";
import cache from "../services/cache.ts";

export function createEndNodeRouter(): Router {
  const router = new Router();

  router.get("/endnodes", (ctx) => {
    const url = new URL(ctx.request.url);
    const selectedTM = url.searchParams.get("model");

    const allNodes = cache.getEndNode(() => true);

    const filteredNodes = selectedTM
      ? allNodes.filter((node) => {
        const tmTitle = [...cache.rawTMCache().entries()]
          .find(([_, tm]) => tm === node.tm)?.[0];
        return tmTitle === selectedTM;
      })
      : allNodes;

    const uniqueTMTitles = Array.from(
      new Set(
        allNodes.map((n) =>
          [...cache.rawTMCache().entries()].find(([_, tm]) => tm === n.tm)?.[0]
        ).filter((x): x is string => !!x),
      ),
    );

    const options = uniqueTMTitles.map((tm) =>
      `<option value="${tm}" ${
        tm === selectedTM ? "selected" : ""
      }>${tm}</option>`
    ).join("");

    const listItems = filteredNodes.map((node, index) =>
      `<li>Node ${index + 1} — ${
        node.tm.title ?? node.manifest.wot.tm.title ?? "Unnamed"
      } (Model: ${
        [...cache.rawTMCache().entries()].find(([_, tm]) => tm === node.tm)?.[0]
      })</li>`
    ).join("");

    ctx.response.type = "text/html";
    ctx.response.body = `
    <html>
    <head><title>Registered End Nodes</title></head>
    <body>
      <h1>Registered End Nodes</h1>
      <form method="GET" action="/endnodes">
        <label for="model">Filter by Thing Model:</label>
        <select name="model" id="model" onchange="this.form.submit()">
          <option value="">-- All --</option>
          ${options}
        </select>
      </form>
      <ul>
        ${listItems || "<li>No end nodes found for this model.</li>"}
      </ul>
    </body>
    </html>`;
  });

  return router;
}

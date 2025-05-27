import { Eta, Router } from "../../deps.ts";
import cache, { EndNode } from "../services/cache.ts";

export function createEndNodeRouter(): Router {
  const router = new Router();
  const viewpath = Deno.cwd() + "/views/";
  const eta = new Eta({ views: viewpath, cache: true });

  router.get("/endnodes", async (ctx) => {
    const url = new URL(ctx.request.url);
    const selectedTM = url.searchParams.get("model");

    const getTMTitleByInstance = (tm: unknown): string | undefined =>
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

    const formattedNodes = filteredNodes.map(([uuid, node]) => ({
      uuid,
      name: node.manifest?.wot?.tm?.title ?? "Unnamed",
      tmLink: `/models/${
        encodeURIComponent(
          getTMTitleByInstance(node.tm) ?? "#",
        )
      }`,
      tdLink: `/tds/${uuid}`,
      manifestLink: `/manifests/${uuid}`,
    }));

    const html = await eta.renderAsync("endnodes", {
      selectedTM,
      models: uniqueTMTitles,
      nodes: formattedNodes,
    });

    ctx.response.headers.set("Content-Type", "text/html");
    ctx.response.body = html;
  });

  return router;
}

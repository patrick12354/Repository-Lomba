// Inlines shared SVG art into scenes so their parts can be animated.
// In a composition write:  <!-- art:compressor:s01 --><!-- /art -->  (name, id prefix); rerun after editing assets/art/*.svgfrag.
// Usage: node scripts/inline-art.mjs
import { readFileSync, writeFileSync, readdirSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
const root = fileURLToPath(new URL("..", import.meta.url));
const dir = join(root, "compositions");
for (const f of readdirSync(dir).filter((f) => f.endsWith(".html"))) {
  const p = join(dir, f);
  const html = readFileSync(p, "utf8");
  const out = html.replace(/<!-- art:([\w-]+):([\w-]+) -->[\s\S]*?<!-- \/art -->/g, (_, name, pre) =>
    `<!-- art:${name}:${pre} -->\n${readFileSync(join(root, `assets/art/${name}.svgfrag`), "utf8").replaceAll("{P}", pre)}<!-- /art -->`);
  if (out !== html) { writeFileSync(p, out); console.log("art ->", f); }
}

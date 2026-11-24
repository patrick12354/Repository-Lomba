// Captures every workspace page (viewport + full page) into capture/ at 2x. Usage: node scripts/capture-pages.mjs [page ...]
import { open, go } from "./capture-lib.mjs";
import { fileURLToPath } from "node:url";
const out = fileURLToPath(new URL("../capture/", import.meta.url));
const pages = {
  landing: "", overview: "#/overview/KO-3201", queue: "#/queue/KO-3201", investigation: "#/investigation/KO-3201",
  actions: "#/actions/KO-3201", foundation: "#/foundation/KO-3201", aiquality: "#/aiquality/KO-3201",
  audit: "#/audit/KO-3201", backlog: "#/backlog/KO-3201", patterns: "#/patterns/KO-3201", business: "#/business/KO-3201",
};
const want = process.argv.slice(2);
const { browser, page } = await open();
for (const [name, hash] of Object.entries(pages)) {
  if (want.length && !want.includes(name)) continue;
  await go(page, hash, 4500);
  await page.screenshot({ path: `${out}${name}.png` });
  await page.screenshot({ path: `${out}${name}-full.png`, fullPage: true });
  console.log("ok", name);
}
await browser.close();

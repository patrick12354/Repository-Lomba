// One-off explorer: dumps the clickable text of a page so capture steps can target real labels.
import { open, go } from "./capture-lib.mjs";
const { browser, page } = await open({ scale: 1 });
await go(page, process.argv[2] ?? "#/investigation/KO-3201");
const items = await page.$$eval("button, a, [role=tab], [role=button]", (els) => els.map((e) => (e.innerText || e.getAttribute("aria-label") || "").trim().replace(/\s+/g, " ")).filter(Boolean));
console.log([...new Set(items)].join("\n"));
await browser.close();

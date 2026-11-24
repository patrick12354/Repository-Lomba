// Prints page-coordinate boxes (CSS px, scroll 0) for elements on a page, to place callouts and clips on captures.
// Usage: node scripts/measure.mjs "#/investigation/KO-3201" "canvas" "text=Checkup" ...
import { open, go } from "./capture-lib.mjs";
const [hash, ...sels] = process.argv.slice(2);
const { browser, page } = await open({ scale: 1 });
await go(page, hash);
for (const s of sels) {
  const els = await page.locator(s).all();
  for (const [i, el] of els.slice(0, 4).entries()) {
    const b = await el.evaluate((e) => { const r = e.getBoundingClientRect(); return [r.x + scrollX, r.y + scrollY, r.width, r.height].map(Math.round); });
    console.log(s, i, b.join(","));
  }
}
await browser.close();

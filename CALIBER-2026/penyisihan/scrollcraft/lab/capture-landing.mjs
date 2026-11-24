// Captures the four workspace screens the landing shows, at 1440x900 @1.5x (2160x1350), offline snapshot.
import { chromium } from "@playwright/test";
const base = process.argv[2] ?? "http://localhost:5174";
const out = process.argv[3];
const shots = [["overview", "overview/KO-3201"], ["queue", "queue/KO-3201"], ["investigation", "investigation/KO-3201"], ["actions", "actions/KO-3201"]];
const browser = await chromium.launch({ channel: process.env.PW_CHANNEL ?? "chrome" });
const page = await browser.newPage({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1.5, reducedMotion: "reduce" });
for (const [name, route] of shots) {
  await page.goto(`${base}/?offline=1#/${route}`, { waitUntil: "networkidle" });
  await page.evaluate(() => { try { localStorage.removeItem("plantpulse.overview.v2"); } catch {} });
  await page.waitForTimeout(2500);
  await page.screenshot({ path: `${out}/${name}.jpg`, type: "jpeg", quality: 86 });
  console.log("shot", name);
}
await browser.close();

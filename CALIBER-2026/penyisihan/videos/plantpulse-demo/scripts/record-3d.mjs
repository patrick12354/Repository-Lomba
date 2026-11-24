// Records the live three.js views as frame-exact 30 fps clips into assets/clips/ by driving
// Playwright's fake clock (rAF + timers) one frame at a time and screenshotting the canvas region.
// Usage: node scripts/record-3d.mjs [machine|replay|site]
import { open, go } from "./capture-lib.mjs";
import { mkdirSync, rmSync } from "node:fs";
import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";
const root = fileURLToPath(new URL("..", import.meta.url));
const FPS = 30;
const jobs = {
  machine: { hash: "#/investigation/KO-3201", seconds: 7, canvas: 0, pad: 0 },
  replay: { hash: "#/investigation/KO-3201", seconds: 9, canvas: 0, pad: 0, before: async (p) => p.getByRole("button", { name: "Replay", exact: true }).first().click() },
  site: { hash: "#/overview/KO-3201", seconds: 7, canvas: 0, pad: 0 },
};
const want = process.argv.slice(2).length ? process.argv.slice(2) : Object.keys(jobs);
for (const name of want) {
  const j = jobs[name];
  const { browser, page } = await open({ scale: 2 });
  await page.clock.install({ time: new Date("2026-10-02T09:00:00Z") });
  await go(page, j.hash, 0);
  await page.clock.runFor(5000); // let data, fonts and the scene settle
  const cv = page.locator("canvas").nth(j.canvas);
  await cv.scrollIntoViewIfNeeded();
  await page.clock.runFor(1500);
  if (j.before) { await j.before(page); await page.clock.runFor(300); }
  const box = await cv.boundingBox();
  const dir = `${root}.hyperframes/frames-${name}`;
  rmSync(dir, { recursive: true, force: true }); mkdirSync(dir, { recursive: true });
  for (let f = 0; f < j.seconds * FPS; f++) {
    await page.screenshot({ path: `${dir}/${String(f).padStart(4, "0")}.png`, clip: box });
    await page.clock.runFor(1000 / FPS);
  }
  await browser.close();
  mkdirSync(`${root}assets/clips`, { recursive: true });
  execFileSync("ffmpeg", ["-loglevel", "error", "-y", "-framerate", String(FPS), "-i", `${dir}/%04d.png`, "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2", "-c:v", "libx264", "-crf", "16", "-preset", "slow", "-pix_fmt", "yuv420p", `${root}assets/clips/${name}.mp4`]);
  console.log("ok", name, Math.round(box.width), "x", Math.round(box.height));
}

// Shared Playwright setup for capturing the PlantPulse app (1920x1080 @2x).
// PP_URL picks the app (default: local dev server), PP_THEME the theme (default: light, the film's look).
// Uses the Playwright package + cached Chromium from scripts/node_modules (run `npm i` in scripts/ once).
import { chromium } from "playwright";
import { existsSync, readdirSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";

export const BASE = process.env.PP_URL ?? "http://localhost:5173/";
export const THEME = process.env.PP_THEME ?? "light";

function chromePath() {
  if (process.env.CHROME) return process.env.CHROME;
  const cache = join(homedir(), "Library/Caches/ms-playwright");
  if (!existsSync(cache)) return undefined;
  for (const d of readdirSync(cache).filter((d) => /^chromium-\d+$/.test(d)).sort().reverse()) {
    const p = join(cache, d, "chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing");
    if (existsSync(p)) return p;
  }
}

export async function open({ scale = 2, video } = {}) {
  const browser = await chromium.launch({ executablePath: chromePath() });
  const ctx = await browser.newContext({
    viewport: { width: 1920, height: 1080 }, deviceScaleFactor: scale, colorScheme: THEME,
    ...(video ? { recordVideo: { dir: video, size: { width: 1920, height: 1080 } } } : {}),
  });
  await ctx.addInitScript((t) => { try { localStorage.setItem("plantpulse.theme", t); } catch {} }, THEME);
  const page = await ctx.newPage();
  return { browser, ctx, page };
}

export async function go(page, hash, wait = 3500) {
  await page.goto(BASE + hash, { waitUntil: "networkidle" }).catch(() => {});
  await page.waitForTimeout(wait);
}

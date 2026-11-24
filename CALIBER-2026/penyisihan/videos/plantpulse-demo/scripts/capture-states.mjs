// Captures the interactive states the film needs into capture/states/ (viewport shots at 2x).
// Usage: node scripts/capture-states.mjs [shotName ...]
import { open, go } from "./capture-lib.mjs";
import { mkdirSync } from "node:fs";
import { fileURLToPath } from "node:url";
const out = fileURLToPath(new URL("../capture/states/", import.meta.url));
mkdirSync(out, { recursive: true });

const click = (p, name, opts = {}) => p.getByRole(opts.role ?? "button", { name, exact: opts.exact ?? false }).first().click();
const shots = {
  "inv-causes": async (p) => { await go(p, "#/investigation/KO-3201"); await click(p, "Causes & AI investigator", { role: "tab" }).catch(() => click(p, "Causes & AI investigator")); await p.waitForTimeout(1500); await p.locator("text=Causes & AI investigator").last().scrollIntoViewIfNeeded(); await p.mouse.wheel(0, 500); await p.waitForTimeout(1200); },
  "inv-brief": async (p) => { await go(p, "#/investigation/KO-3201"); await click(p, "AI brief", { role: "tab" }).catch(() => click(p, "AI brief")); await p.waitForTimeout(1500); await p.mouse.wheel(0, 900); await p.waitForTimeout(1200); },
  "inv-similar": async (p) => { await go(p, "#/investigation/KO-3201"); await click(p, "Similar records", { role: "tab" }).catch(() => click(p, "Similar records")); await p.waitForTimeout(1500); await p.mouse.wheel(0, 900); await p.waitForTimeout(1200); },
  "inv-window": async (p) => { await go(p, "#/investigation/KO-3201"); await click(p, "Window to act", { role: "tab" }).catch(() => click(p, "Window to act")); await p.waitForTimeout(1500); await p.mouse.wheel(0, 900); await p.waitForTimeout(1200); },
  "inv-openbrief": async (p) => { await go(p, "#/investigation/KO-3201"); await click(p, "Open AI brief"); await p.waitForTimeout(2500); },
  "queue-evidence": async (p) => { await go(p, "#/queue/KO-3201"); await p.mouse.wheel(0, 1000); await p.waitForTimeout(1500); },
  "queue-conflicts": async (p) => { await go(p, "#/queue/KO-3201"); await click(p, "Sources & conflicts").catch(() => {}); await p.waitForTimeout(800); await p.locator("text=Sources & conflicts").first().scrollIntoViewIfNeeded(); await p.mouse.wheel(0, 300); await p.waitForTimeout(1200); },
  "queue-conflicts-tab": async (p) => { await go(p, "#/queue/KO-3201"); const t = p.getByRole("tab", { name: /Sources/ }).first(); await t.scrollIntoViewIfNeeded(); await t.click({ force: true }); await p.waitForTimeout(1200);
    // Park the CF-01 card where the film's callouts expect it (its title at y = 314 CSS px).
    const b = await p.getByText("Vibration alert threshold version").first().boundingBox(); await p.evaluate((d) => window.scrollBy(0, d), b.y - 314); await p.waitForTimeout(1200); },
  "queue-conflicts-tab2": async (p) => { await p.mouse.wheel(0, 700); await p.waitForTimeout(1000); },
  "inv-withheld": async (p) => { await go(p, "#/investigation/KO-3201"); await p.getByRole("tab", { name: /AI brief/ }).first().click({ force: true }); await p.waitForTimeout(1200);
    await p.getByRole("button", { name: "Try it", exact: true }).first().click({ force: true }); await p.waitForTimeout(600);
    await p.locator("label.chk", { hasText: "EV-03" }).first().click({ force: true }); await p.waitForTimeout(800);
    await p.getByText("What the available evidence shows").first().scrollIntoViewIfNeeded(); await p.mouse.wheel(0, -120); await p.waitForTimeout(1000); },
  // Same page and scroll as inv-withheld, captured just before the source is withheld (toggle on, off).
  "inv-unwithheld": async (p) => {
    await go(p, "#/investigation/KO-3201"); await p.getByRole("tab", { name: /AI brief/ }).first().click({ force: true }); await p.waitForTimeout(1200);
    const tryIt = p.getByRole("button", { name: "Try it", exact: true }).first(); if (await tryIt.count()) await tryIt.click({ force: true }); await p.waitForTimeout(600);
    const box = p.locator("label.chk", { hasText: "EV-03" }).first().locator("input");
    if (!(await box.isChecked())) { await box.click({ force: true }); await p.waitForTimeout(500); }
    await p.getByText("What the available evidence shows").first().scrollIntoViewIfNeeded(); await p.mouse.wheel(0, -120); await p.waitForTimeout(800);
    await box.click({ force: true }); await p.waitForTimeout(800); },
  "queue-drawer": async (p) => { await go(p, "#/queue/KO-3201"); await click(p, "E2", { exact: true }); await p.waitForTimeout(2000); },
  "queue-conflict-tile": async (p) => { await go(p, "#/queue/KO-3201"); await p.getByText("Unresolved source conflicts").first().click(); await p.waitForTimeout(2000); },
  "copilot": async (p) => { await go(p, "#/investigation/KO-3201"); await click(p, "Ask PlantPulse"); await p.waitForTimeout(2500); },
  "actions-card": async (p) => { await go(p, "?offline=1#/actions/KO-3201"); await p.mouse.wheel(0, 500); await p.waitForTimeout(1200); },
  "actions-close-refused": async (p) => { await go(p, "?offline=1#/actions/KO-3201"); await p.mouse.wheel(0, 500); await p.waitForTimeout(800); await click(p, "Mark complete now"); await p.waitForTimeout(1500); },
  "actions-followthrough": async (p) => { await go(p, "?offline=1#/actions/KO-3201"); await click(p, "Follow-through", { role: "tab" }).catch(() => click(p, "Follow-through")); await p.waitForTimeout(1200); await p.mouse.wheel(0, 500); await p.waitForTimeout(1200); },
  "actions-reviewlog": async (p) => { await go(p, "?offline=1#/actions/KO-3201"); await click(p, "Review log", { role: "tab" }).catch(() => click(p, "Review log")); await p.waitForTimeout(1200); await p.mouse.wheel(0, 500); await p.waitForTimeout(1200); },
  "actions-reminders": async (p) => { await go(p, "?offline=1#/actions/KO-3201"); await click(p, "Reminders", { role: "tab" }).catch(() => click(p, "Reminders")); await p.waitForTimeout(1200); await p.mouse.wheel(0, 500); await p.waitForTimeout(1200); },
  "foundation-checks": async (p) => { await go(p, "#/foundation/KO-3201"); await click(p, "Reproduction checks", { role: "tab" }).catch(() => click(p, "Reproduction checks")); await p.waitForTimeout(1000); await p.mouse.wheel(0, 900); await p.waitForTimeout(1200); },
  "audit": async (p) => { await go(p, "#/audit/KO-3201"); await p.mouse.wheel(0, 400); await p.waitForTimeout(1200); },
};
const want = process.argv.slice(2);
const { browser, page } = await open();
for (const [name, fn] of Object.entries(shots)) {
  if (want.length && !want.includes(name)) continue;
  try { await fn(page); await page.screenshot({ path: `${out}${name}.png` }); console.log("ok", name); }
  catch (e) { console.log("FAIL", name, e.message.split("\n")[0]); }
}
await browser.close();

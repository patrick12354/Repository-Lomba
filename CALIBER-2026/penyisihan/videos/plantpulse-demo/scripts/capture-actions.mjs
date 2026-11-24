// Walks the real closure gate in offline mode (?offline=1, browser-local simulation, nothing written to the server)
// and saves each state to capture/actions/. Usage: node scripts/capture-actions.mjs
import { open, go } from "./capture-lib.mjs";
import { mkdirSync } from "node:fs";
import { fileURLToPath } from "node:url";
const out = fileURLToPath(new URL("../capture/actions/", import.meta.url));
mkdirSync(out, { recursive: true });
const { browser, page: p } = await open();
const btn = (name) => ({ click: () => card().getByRole("button", { name, exact: true }).first().dispatchEvent("click") });
const pageBtn = (name) => p.getByRole("button", { name, exact: true }).first();
let cardLabel = null; // pinned after creation: the carousel re-measures and flips data-centre while we type
const card = () => cardLabel ? p.locator(`article[aria-label='${cardLabel}']`) : p.locator("article[aria-label^='Simulated action']").first();
const shot = async (name, focus) => {
  if (focus) await focus.scrollIntoViewIfNeeded().catch(() => {});
  await p.waitForTimeout(700);
  await p.screenshot({ path: `${out}${name}.png` });
  // The floating "Ask PlantPulse" button sits over the card's corner; hide it for the card-only shot.
  await p.addStyleTag({ content: ".copilot-fab{visibility:hidden!important}" }).then((h) => card().screenshot({ path: `${out}${name}-card.png` }).finally(() => h.evaluate((el) => el.remove()))).catch(() => {});
  console.log("ok", name);
};
const field = (label) => {
  const el = card().locator("label.field", { hasText: label }).locator("input, textarea").first();
  const fill = el.fill.bind(el);
  return Object.assign(el, { fill: (v) => fill(v, { force: true }) });
};
const gate = () => card().getByText(/Closure blocked|Evidence complete|Closed with evidence/).first();

await go(p, "?offline=1#/actions/KO-3201");
await pageBtn("Create as simulated action").click();
await p.waitForTimeout(1500);
cardLabel = await card().getAttribute("aria-label");
await shot("01-draft", card());
await field("Owner").fill("REL-05");
await field("Due date").fill("2026-10-16");
await field("Scope").fill("KO-3201 lube-oil system: online water-in-oil sensor");
await field("Dependencies").fill("none");
await shot("02-filled", field("Owner"));
await btn("Mark complete now").click();
await shot("03-refused", gate());
for (const step of ["Mark reviewed", "Assign", "Start work"]) { await btn(step).click(); await p.waitForTimeout(500); }
await p.waitForTimeout(600);
await card().locator("details").evaluateAll((ds) => ds.forEach((d) => (d.open = true))); // "Plan · locked after review" holds the execution note
await p.waitForTimeout(600);
await field("Execution note").fill("Sensor installed and commissioned 9 Oct 2026 (simulated)");
if (process.env.DEBUG) console.log("before report:", (await card().innerText()).slice(0, 1500));
await btn("Report execution").click(); await p.waitForTimeout(500);
if (process.env.DEBUG) console.log("after report:", (await card().innerText()).slice(0, 2500));
await shot("04-evidence-stage", card().getByText("Evidence needed to close"));
// Attach one dated simulated document for every required evidence kind still marked missing.
const select = card().locator("select[aria-label='Evidence type']");
const kinds = await select.locator("option").allTextContents();
const missing = await card().locator("li", { hasText: /missing$/i }).allTextContents();
for (const k of kinds) {
  if (!missing.some((m) => m.toLowerCase().includes(k.toLowerCase()))) continue;
  await select.selectOption({ label: k });
  await card().locator("input[aria-label='Evidence date']").fill("2026-10-09");
  await btn("Attach").click(); await p.waitForTimeout(400);
}
await shot("05-attached", card().getByText("Evidence needed to close"));
await btn("Submit evidence").click(); await p.waitForTimeout(500);
await btn("Send for verification").click(); await p.waitForTimeout(500);
await shot("06-ready", gate());
await field("Reviewer").fill("REL-05");
await btn("Verify (reviewer)").click(); await p.waitForTimeout(500);
await shot("07-reviewer-is-owner", gate());
await field("Reviewer").fill("QA-07 (independent reviewer)");
await p.waitForTimeout(300);
await shot("08-reviewer-named", gate());
await p.getByRole("button", { name: /Review log/ }).first().click().catch(() => {});
await p.waitForTimeout(1000);
await p.mouse.wheel(0, 600);
await p.waitForTimeout(800);
await p.screenshot({ path: `${out}09-log.png` }); console.log("ok 09-log");
await browser.close();

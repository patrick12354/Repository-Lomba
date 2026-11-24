import { withLang } from "@/lib/i18n-server";
import type { NextRequest } from "next/server";
import { memo, type MemoInput } from "@/lib/ai";
import { replayProof, scenario } from "@/lib/data";
import { meta } from "@/lib/db";
import { t } from "@/lib/i18n";

/** The client sends the English plan name as a key; the memo names it in the reader's language. */
const PLAN_ID: Record<string, string> = { Recommended: "Disarankan", "Lowest total cost": "Total biaya terendah", "Stay as we are": "Tetap seperti sekarang", "Pick a budget": "Pilih anggaran" };

const clamp = (v: unknown, lo: number, hi: number, d: number) => {
  const n = Number(v);
  return Number.isFinite(n) ? Math.min(hi, Math.max(lo, n)) : d;
};

function replayFacts() {
  const r = replayProof();
  return r ? { fill: r.sparekit.fill_units, fillToday: r.today.fill_units, stockCut: 1 - r.sparekit.avg_inv_idr / r.today.avg_inv_idr } : null;
}

/** The client names a point on the frontier and two assumptions; every other number is read back from the engine. */
async function handlePOST(req: NextRequest) {
  const b = (await req.json().catch(() => ({}))) as { policy?: unknown; budget?: unknown; holding?: unknown; rate?: unknown };
  const holding = clamp(b.holding, 0.05, 0.5, Number(meta().holding_rate));
  const rate = clamp(b.rate, 0, 1e9, 5e6);
  const s = scenario(clamp(b.budget, 0, 1e13, 0), holding);
  const policy = b.policy === "Recommended" ? s.optimized : b.policy === "Stay as we are" ? s.current : s.pick;
  const key = typeof b.policy === "string" ? b.policy.slice(0, 40) : null;
  const name = key ? t(key, PLAN_ID[key] ?? key) : t("Custom budget", "Anggaran pilihan");
  const days = (v: number) => (v / 100) * rate;
  const dHold = (policy.budget_idr - s.current.budget_idr) * holding;
  const dRisk = (s.current.exp_risk_cost - policy.exp_risk_cost) / 100;
  const input: MemoInput = {
    policy: name,
    budget: policy.budget_idr,
    today: s.current.budget_idr,
    risk: policy.exp_risk_cost / s.current.exp_risk_cost,
    holding,
    rate,
    exposure: days(policy.exp_risk_cost),
    exposureToday: days(s.current.exp_risk_cost),
    holdCost: policy.budget_idr * holding,
    holdCostToday: s.current.budget_idr * holding,
    breakEven: dHold > 0 && dRisk > 0 ? dHold / dRisk : null,
    replay: b.policy === "Recommended" ? replayFacts() : null,
  };
  return Response.json(await memo(input));
}

// Each handler runs in the caller's language, so any text it builds matches the page.
export const POST = (...a: Parameters<typeof handlePOST>) => withLang(() => handlePOST(...a));

import { withLang } from "@/lib/i18n-server";
import type { NextRequest } from "next/server";
import { connection } from "next/server";
import { moveToStock, mrpChanges, taskFor } from "@/lib/data";
import { listDecisions } from "@/lib/decisions-db";

const cell = (v: unknown) => {
  const s = v == null ? "" : String(v);
  return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
};
const csv = (head: string[], rows: unknown[][]) => [head, ...rows].map((r) => r.map(cell).join(",")).join("\r\n");
const file = (name: string, body: string) => new Response(`﻿${body}`, { headers: { "content-type": "text/csv; charset=utf-8", "content-disposition": `attachment; filename="${name}"` } });

/** The only plant in the PR PO file. */
const PLANT = "1000";

/** GET /api/export?type=mm17 → new MRP parameters for SAP mass maintenance. ?type=pr → draft requisitions for approved tasks. ?type=stock → Non Stock parts on the buying list. */
async function handleGET(req: NextRequest) {
  await connection();
  if (req.nextUrl.searchParams.get("type") === "pr") {
    const rows = listDecisions()
      .filter((d) => d.decision === "approved" || d.decision === "in_progress")
      .flatMap((d) => {
        const t = taskFor(Number(d.id));
        if (!t || (t.kind !== "order" && t.kind !== "expedite")) return [];
        return [[t.material_no, t.description, t.qty, t.unit, t.criticality, t.kind === "expedite" ? "Expedite" : "Normal", t.order_by ?? "", Math.round(t.lead_time), t.value == null ? "" : Math.round(t.value), d.decided_at]];
      });
    return file("sparekit-draft-pr.csv", csv(["MATNR", "Description", "Quantity", "Unit", "Criticality", "Priority", "Order by", "Lead time P90 (days)", "Estimated value (IDR)", "Approved at"], rows));
  }
  if (req.nextUrl.searchParams.get("type") === "stock") {
    const rows = moveToStock().map((m) => [m.material_no, PLANT, "Non Stock", m.basis === "ahead" ? "Stock Item" : "Decide: bought for the turnaround", Math.round(m.min_new), Math.round(m.max_new), m.qty, m.unit, m.criticality, m.value == null ? "" : Math.round(m.value), m.description]);
    return file("sparekit-move-to-stock.csv", csv(["MATNR", "WERKS", "MRP type today", "Suggested MRP type", "MINBE reorder point", "MABST max stock", "Quantity to buy", "Unit", "Criticality", "Estimated value (IDR)", "Description"], rows));
  }
  const rows = mrpChanges().map((m) => [m.material_no, PLANT, Math.round(m.safety_stock), Math.round(m.min_new), Math.round(m.max_new), Math.round(m.min_cur), Math.round(m.max_cur), m.criticality, m.action, m.description]);
  return file("sparekit-mm17-mrp-parameters.csv", csv(["MATNR", "WERKS", "EISBE safety stock", "MINBE reorder point", "MABST max stock", "Current Min", "Current Max", "Criticality", "Action", "Description"], rows));
}

// Each handler runs in the caller's language, so any text it builds matches the page.
export const GET = (...a: Parameters<typeof handleGET>) => withLang(() => handleGET(...a));

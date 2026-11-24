import { t } from "@/lib/i18n";
import { withLang } from "@/lib/i18n-server";
import { REASON_CODES } from "@/lib/reasons";
import type { NextRequest } from "next/server";
import { connection } from "next/server";
import { currentUser, signInFirst } from "@/lib/auth";
import { taskFor } from "@/lib/data";
import { decisionOf, deleteDecision, emailedIds, listDecisions, resetDecisions, saveDecision, type DecisionState } from "@/lib/decisions-db";
import { canMove, type Person, type Stage } from "@/lib/people";

/** GET /api/decisions → every task status in this demo session, newest first. */
async function handleGET() {
  await connection();
  return Response.json({ rows: listDecisions(), emailed: emailedIds(), storage: "sqlite-temp" });
}

/** The same rule the board shows, checked again here. A part with no open task is the planner's call. */
function allowed(me: Person, id: string, to: Stage) {
  const t = taskFor(Number(id));
  const from = (decisionOf(id) ?? "todo") as Stage;
  return t ? canMove(me, t, from, to) : me.role === "planner";
}

const refuse = () => Response.json({ error: t("This step belongs to someone else.", "Langkah ini menjadi tugas orang lain.") }, { status: 403 });

/** POST /api/decisions {id, decision: "approved"|"in_progress"|"done"|"rejected", material_no?, action?, note?} */
async function handlePOST(req: NextRequest) {
  const me = await currentUser();
  if (!me) return signInFirst();
  let body: { id?: unknown; decision?: unknown; material_no?: unknown; action?: unknown; note?: unknown; reason?: unknown; reason_source?: unknown };
  try {
    body = await req.json();
  } catch {
    return Response.json({ error: t("Send a JSON body.", "Kirim body JSON.") }, { status: 400 });
  }
  if (typeof body.id !== "string" || !body.id || body.id.length > 64) {
    return Response.json({ error: "id is required." }, { status: 400 });
  }
  const decision = body.decision;
  if (decision !== "approved" && decision !== "in_progress" && decision !== "done" && decision !== "rejected") {
    return Response.json({ error: 'decision must be "approved", "in_progress", "done" or "rejected".' }, { status: 400 });
  }
  if (!allowed(me, body.id, decision)) return refuse();
  saveDecision(
    {
      id: body.id,
      decision: decision as DecisionState,
      material_no: typeof body.material_no === "number" ? body.material_no : null,
      action: typeof body.action === "string" ? body.action.slice(0, 32) : null,
      note: typeof body.note === "string" ? body.note.slice(0, 280) : null,
      reason: decision === "rejected" && typeof body.reason === "string" && REASON_CODES.includes(body.reason) ? body.reason : null,
      reason_source: body.reason_source === "ai" || body.reason_source === "keywords" || body.reason_source === "planner" ? body.reason_source : null,
    },
    me,
  );
  return Response.json({ ok: true });
}

/** DELETE /api/decisions?id=… moves one back to To decide; ?all=1 resets the demo, for the planner. */
async function handleDELETE(req: NextRequest) {
  const me = await currentUser();
  if (!me) return signInFirst();
  const sp = req.nextUrl.searchParams;
  const id = sp.get("id");
  if (sp.get("all") === "1") {
    if (me.role !== "planner") return refuse();
    resetDecisions();
  } else if (id) {
    if (!allowed(me, id, "todo")) return refuse();
    deleteDecision(id, me);
  } else return Response.json({ error: "Pass id or all=1." }, { status: 400 });
  return Response.json({ ok: true });
}

// Each handler runs in the caller's language, so any text it builds matches the page.
export const GET = (...a: Parameters<typeof handleGET>) => withLang(() => handleGET(...a));
export const POST = (...a: Parameters<typeof handlePOST>) => withLang(() => handlePOST(...a));
export const DELETE = (...a: Parameters<typeof handleDELETE>) => withLang(() => handleDELETE(...a));

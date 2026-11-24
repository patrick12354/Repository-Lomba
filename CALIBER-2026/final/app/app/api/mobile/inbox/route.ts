import { t as tx } from "@/lib/i18n";
import { withLang } from "@/lib/i18n-server";
import type { NextRequest } from "next/server";
import { connection } from "next/server";
import { currentUser, signInFirst } from "@/lib/auth";
import { tasks, type Task } from "@/lib/data";
import { listDecisions } from "@/lib/decisions-db";
import { canMove, isMine, ownerOf, type Stage } from "@/lib/people";
import { REASONS } from "@/lib/reasons";

const NEXT: Partial<Record<Stage, Stage>> = { todo: "approved", approved: "in_progress", in_progress: "done" };
const DEFAULT_LIMIT = 150;
const MAX_LIMIT = 500;

/** Only what a phone shows on a card, so the list stays light on a weak signal. */
function card(task: Task, stage: Stage, nextTo: Stage | null, actionable: boolean, canReject: boolean) {
  return {
    id: task.id,
    material_no: task.material_no,
    description: task.description,
    unit: task.unit,
    criticality: task.criticality,
    kind: task.kind,
    urgency: task.urgency,
    stock: task.stock,
    target: task.target,
    qty: task.qty,
    order_by: task.order_by,
    days_left: task.days_left,
    value: task.value,
    machines: task.machines,
    twin: task.twin,
    owner: ownerOf(task).name,
    stage,
    next_to: nextTo,
    actionable,
    can_reject: canReject,
  };
}

/**
 * GET /api/mobile/inbox?limit=150 → the signed-in person's open tasks, split into what they can act on
 * and what they only follow. The rules stay in lib/people.ts; POST /api/decisions checks them again on every move.
 */
async function handleGET(req: NextRequest) {
  await connection();
  const me = await currentUser();
  if (!me) return signInFirst();

  const asked = Number(req.nextUrl.searchParams.get("limit"));
  const limit = Number.isInteger(asked) && asked > 0 ? Math.min(asked, MAX_LIMIT) : DEFAULT_LIMIT;
  const stages = new Map(listDecisions().map((d) => [d.id, d.decision as Stage]));

  const act: ReturnType<typeof card>[] = [];
  const follow: ReturnType<typeof card>[] = [];
  let urgent = 0;
  let late = 0;

  for (const task of tasks()) {
    const stage = stages.get(task.id) ?? "todo";
    if (stage === "done" || stage === "rejected" || !isMine(me, task, stage)) continue;
    const nextTo = NEXT[stage] ?? null;
    const actionable = !!nextTo && canMove(me, task, stage, nextTo);
    const row = card(task, stage, nextTo, actionable, canMove(me, task, stage, "rejected"));
    if (!actionable) {
      follow.push(row);
      continue;
    }
    act.push(row);
    if (task.urgency === "late") late++;
    if (task.urgency === "late" || task.urgency === "now") urgent++;
  }

  return Response.json({
    me: { id: me.id, name: me.name, title: me.title, role: me.role, does: me.does },
    counts: { act: act.length, follow: follow.length, urgent, late },
    act: act.slice(0, limit),
    follow: follow.slice(0, limit),
    reasons: REASONS.map((r) => ({ code: r.code, label: r.label, hint: r.hint })),
    message: act.length ? null : tx("Nothing waiting on you right now.", "Tidak ada yang menunggu Anda saat ini."),
  });
}

// Each handler runs in the caller's language, so any text it builds matches the page.
export const GET = (...a: Parameters<typeof handleGET>) => withLang(() => handleGET(...a));

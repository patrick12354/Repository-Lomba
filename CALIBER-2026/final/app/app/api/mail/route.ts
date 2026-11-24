import { t } from "@/lib/i18n";
import { withLang } from "@/lib/i18n-server";
import type { NextRequest } from "next/server";
import { currentUser, signInFirst } from "@/lib/auth";
import { part, taskFor } from "@/lib/data";
import { decisionOf, logActivity, saveDecision } from "@/lib/decisions-db";
import { mailConfigured, sendMail } from "@/lib/mail";
import { canMove, DEMO_INBOX, personById, SUPPLIER } from "@/lib/people";

/**
 * POST /api/mail {toId, subject, body, materialNo?}. The client names a person in the directory, never an
 * address, so this route cannot be used to write to anyone outside the demo inbox.
 */
async function handlePOST(req: NextRequest) {
  const me = await currentUser();
  if (!me) return signInFirst();
  const b = (await req.json().catch(() => ({}))) as { toId?: unknown; subject?: unknown; body?: unknown; materialNo?: unknown; advance?: unknown };
  const subject = typeof b.subject === "string" ? b.subject.replace(/[\r\n]+/g, " ").trim().slice(0, 200) : "";
  const body = typeof b.body === "string" ? b.body.trim().slice(0, 5000) : "";
  if (!subject || !body) return Response.json({ error: t("Write a subject and a message first.", "Tulis subjek dan pesannya terlebih dahulu.") }, { status: 400 });
  const task = typeof b.materialNo === "number" ? taskFor(b.materialNo) : null;
  const supplier = b.toId === SUPPLIER && task ? String(part(task.material_no)?.m.main_supplier ?? "Supplier") : null;
  const person = personById(typeof b.toId === "string" ? b.toId : null);
  const toName = supplier ?? person?.name;
  if (!toName) return Response.json({ error: t("Pick someone from the list.", "Pilih penerima dari daftar.") }, { status: 400 });
  if (!mailConfigured()) return Response.json({ error: t("Gmail is not connected yet.", "Gmail belum terhubung."), fallback: true }, { status: 503 });

  try {
    await sendMail({ from: me, toName, toEmail: person?.email ?? DEMO_INBOX, subject, body });
  } catch (e) {
    console.error("Gmail send failed", e);
    return Response.json({ error: t("Gmail did not accept the message. Check the App Password.", "Gmail menolak pesan ini. Periksa Sandi Aplikasi."), fallback: true }, { status: 502 });
  }

  let moved: string | null = null;
  if (task) {
    logActivity(task.id, me, "email", `Emailed ${toName}: ${subject}`);
    const from = decisionOf(task.id) ?? "todo";
    // Only the button that said so moves the task. A plain email never changes its status.
    const next = from === "todo" ? "approved" : from === "approved" ? "in_progress" : null;
    const to = b.advance === next ? next : null;
    if (to && canMove(me, task, from, to)) {
      saveDecision({ id: task.id, material_no: task.material_no, action: task.kind, decision: to }, me);
      moved = to;
    }
  }
  return Response.json({ ok: true, to: toName, moved });
}

// Each handler runs in the caller's language, so any text it builds matches the page.
export const POST = (...a: Parameters<typeof handlePOST>) => withLang(() => handlePOST(...a));

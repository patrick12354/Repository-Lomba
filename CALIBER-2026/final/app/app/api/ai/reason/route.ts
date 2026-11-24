import { withLang } from "@/lib/i18n-server";
import type { NextRequest } from "next/server";
import { sortReason } from "@/lib/reason-ai";
import { currentUser, signInFirst } from "@/lib/auth";
import { taskFor } from "@/lib/data";

/** POST {note, material_no} → the reason to record for this rejection, sorted by AI (keywords when AI is off). */
async function handlePOST(req: NextRequest) {
  if (!(await currentUser())) return signInFirst();
  const b = (await req.json().catch(() => ({}))) as { note?: unknown; material_no?: unknown };
  const note = typeof b.note === "string" ? b.note : "";
  const t = typeof b.material_no === "number" ? taskFor(b.material_no) : null;
  return Response.json(await sortReason(note, t ? { kind: t.kind, description: t.description } : null));
}

// Each handler runs in the caller's language, so any text it builds matches the page.
export const POST = (...a: Parameters<typeof handlePOST>) => withLang(() => handlePOST(...a));

import { t } from "@/lib/i18n";
import { withLang } from "@/lib/i18n-server";
import type { NextRequest } from "next/server";
import { draft } from "@/lib/ai";
import { currentUser, signInFirst } from "@/lib/auth";

/** POST {id, to}: the email for this task, from the signed-in person to someone in the directory or the supplier. */
async function handlePOST(req: NextRequest) {
  const me = await currentUser();
  if (!me) return signInFirst();
  const { id, to } = (await req.json().catch(() => ({}))) as { id?: unknown; to?: unknown };
  const out = await draft(Number(id), me, typeof to === "string" ? to : null);
  return out ? Response.json(out) : Response.json({ error: t("No task for that part.", "Tidak ada tugas untuk suku cadang itu.") }, { status: 404 });
}

// Each handler runs in the caller's language, so any text it builds matches the page.
export const POST = (...a: Parameters<typeof handlePOST>) => withLang(() => handlePOST(...a));

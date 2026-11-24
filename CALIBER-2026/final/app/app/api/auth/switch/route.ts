import { t } from "@/lib/i18n";
import { withLang } from "@/lib/i18n-server";
import type { NextRequest } from "next/server";
import { currentUser, signInFirst } from "@/lib/auth";
import { personById } from "@/lib/people";
import { SESSION_COOKIE, SESSION_HOURS, signSession } from "@/lib/session";

/** POST {id}: a signed-in demo user takes on another demo role. Only people in the directory can be chosen. */
async function handlePOST(req: NextRequest) {
  if (!(await currentUser())) return signInFirst();
  const { id } = (await req.json().catch(() => ({}))) as { id?: unknown };
  const person = personById(typeof id === "string" ? id : null);
  if (!person) return Response.json({ error: t("Pick a role from the list.", "Pilih peran dari daftar.") }, { status: 400 });
  const res = Response.json({ ok: true });
  const secure = process.env.NODE_ENV === "production" ? "; Secure" : "";
  res.headers.append("set-cookie", `${SESSION_COOKIE}=${await signSession(person.id)}; Path=/; HttpOnly; SameSite=Lax; Max-Age=${SESSION_HOURS * 3600}${secure}`);
  return res;
}

// Each handler runs in the caller's language, so any text it builds matches the page.
export const POST = (...a: Parameters<typeof handlePOST>) => withLang(() => handlePOST(...a));

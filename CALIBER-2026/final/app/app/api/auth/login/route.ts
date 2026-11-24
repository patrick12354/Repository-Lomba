import { t } from "@/lib/i18n";
import { withLang } from "@/lib/i18n-server";
import type { NextRequest } from "next/server";
import { checkPassword } from "@/lib/decisions-db";
import { SESSION_COOKIE, SESSION_HOURS, signSession } from "@/lib/session";

async function handlePOST(req: NextRequest) {
  const b = (await req.json().catch(() => ({}))) as { login?: unknown; password?: unknown };
  if (typeof b.login !== "string" || typeof b.password !== "string") return Response.json({ error: t("Enter your email and password.", "Masukkan surel dan kata sandi Anda.") }, { status: 400 });
  const id = checkPassword(b.login.slice(0, 120), b.password.slice(0, 120));
  if (!id) return Response.json({ error: t("That email and password do not match.", "Surel dan kata sandi tidak cocok.") }, { status: 401 });
  const res = Response.json({ ok: true });
  const secure = process.env.NODE_ENV === "production" ? "; Secure" : "";
  res.headers.append("set-cookie", `${SESSION_COOKIE}=${await signSession(id)}; Path=/; HttpOnly; SameSite=Lax; Max-Age=${SESSION_HOURS * 3600}${secure}`);
  return res;
}

// Each handler runs in the caller's language, so any text it builds matches the page.
export const POST = (...a: Parameters<typeof handlePOST>) => withLang(() => handlePOST(...a));

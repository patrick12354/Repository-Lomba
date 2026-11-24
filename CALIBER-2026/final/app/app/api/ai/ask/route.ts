import { t } from "@/lib/i18n";
import { withLang } from "@/lib/i18n-server";
import type { NextRequest } from "next/server";
import { ask } from "@/lib/ai";

async function handlePOST(req: NextRequest) {
  const { q } = (await req.json().catch(() => ({}))) as { q?: unknown };
  if (typeof q !== "string" || !q.trim()) return Response.json({ error: t("Type a request.", "Ketik permintaan Anda.") }, { status: 400 });
  return Response.json(await ask(q.trim().slice(0, 200)));
}

// Each handler runs in the caller's language, so any text it builds matches the page.
export const POST = (...a: Parameters<typeof handlePOST>) => withLang(() => handlePOST(...a));

import { t } from "@/lib/i18n";
import { withLang } from "@/lib/i18n-server";
import type { NextRequest } from "next/server";
import { explain } from "@/lib/ai";

async function handlePOST(req: NextRequest) {
  const { id } = (await req.json().catch(() => ({}))) as { id?: unknown };
  const out = await explain(Number(id));
  return out ? Response.json(out) : Response.json({ error: t("No task for that part.", "Tidak ada tugas untuk suku cadang itu.") }, { status: 404 });
}

// Each handler runs in the caller's language, so any text it builds matches the page.
export const POST = (...a: Parameters<typeof handlePOST>) => withLang(() => handlePOST(...a));

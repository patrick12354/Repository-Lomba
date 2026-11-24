import { t } from "@/lib/i18n";
import { withLang } from "@/lib/i18n-server";
import type { NextRequest } from "next/server";
import { part, partAnswer } from "@/lib/data";

async function handleGET(_req: NextRequest, ctx: { params: Promise<{ id: string }> }) {
  const { id } = await ctx.params;
  const p = part(Number(id));
  if (!p) return Response.json({ error: t("No part with that number.", "Tidak ada suku cadang dengan nomor itu.") }, { status: 404 });
  return Response.json({ ...p, answer: partAnswer(Number(id)) });
}

// Each handler runs in the caller's language, so any text it builds matches the page.
export const GET = (...a: Parameters<typeof handleGET>) => withLang(() => handleGET(...a));

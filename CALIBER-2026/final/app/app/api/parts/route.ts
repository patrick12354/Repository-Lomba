import { withLang } from "@/lib/i18n-server";
import type { NextRequest } from "next/server";
import { parts, actionSummary } from "@/lib/data";

async function handleGET(req: NextRequest) {
  const sp = req.nextUrl.searchParams;
  const res = parts({
    category: sp.get("category") ?? undefined,
    action: sp.get("action") ?? undefined,
    crit: sp.get("crit") ?? undefined,
    health: sp.get("health") ?? undefined,
    q: sp.get("q") ?? undefined,
    twin: sp.get("twin") === "1",
    limit: Number(sp.get("limit") ?? 40),
    offset: Number(sp.get("offset") ?? 0),
  });
  return Response.json({ ...res, summary: sp.get("summary") ? actionSummary() : undefined });
}

// Each handler runs in the caller's language, so any text it builds matches the page.
export const GET = (...a: Parameters<typeof handleGET>) => withLang(() => handleGET(...a));

import { withLang } from "@/lib/i18n-server";
import type { NextRequest } from "next/server";
import { searchParts } from "@/lib/data";

async function handleGET(req: NextRequest) {
  const q = req.nextUrl.searchParams.get("q") ?? "";
  if (q.trim().length < 2) return Response.json({ results: [] });
  return Response.json({ results: searchParts(q, 8) });
}

// Each handler runs in the caller's language, so any text it builds matches the page.
export const GET = (...a: Parameters<typeof handleGET>) => withLang(() => handleGET(...a));

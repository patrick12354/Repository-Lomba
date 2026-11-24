import { withLang } from "@/lib/i18n-server";
import type { NextRequest } from "next/server";
import { readiness } from "@/lib/data";

async function handleGET(req: NextRequest) {
  const sp = req.nextUrl.searchParams;
  const r = readiness(sp.get("date") ?? undefined, Number(sp.get("scale") ?? 1), Number(sp.get("shock") ?? 0));
  return Response.json(r);
}

// Each handler runs in the caller's language, so any text it builds matches the page.
export const GET = (...a: Parameters<typeof handleGET>) => withLang(() => handleGET(...a));

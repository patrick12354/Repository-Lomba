import { withLang } from "@/lib/i18n-server";
import type { NextRequest } from "next/server";
import { scenario } from "@/lib/data";

/** GET /api/scenario?budget=<IDR>&holding=<0.05..0.5> → the nearest point on the engine's frontier. */
async function handleGET(req: NextRequest) {
  const sp = req.nextUrl.searchParams;
  const budget = sp.get("budget") !== null ? Number(sp.get("budget")) : undefined;
  const h = sp.get("holding") !== null ? Math.min(0.5, Math.max(0.05, Number(sp.get("holding")))) : undefined;
  return Response.json(scenario(budget, h));
}

// Each handler runs in the caller's language, so any text it builds matches the page.
export const GET = (...a: Parameters<typeof handleGET>) => withLang(() => handleGET(...a));

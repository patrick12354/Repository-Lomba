import { withLang } from "@/lib/i18n-server";
import type { NextRequest } from "next/server";
import { health, readiness, actionSummary } from "@/lib/data";

async function handleGET(req: NextRequest) {
  void req.nextUrl;
  const r = readiness();
  return Response.json({
    health: health(),
    actions: actionSummary(),
    turnaround: { taDate: r.taDate, daysToTa: r.daysToTa, byCrit: r.byCrit, counts: r.counts },
  });
}

// Each handler runs in the caller's language, so any text it builds matches the page.
export const GET = (...a: Parameters<typeof handleGET>) => withLang(() => handleGET(...a));

import { withLang } from "@/lib/i18n-server";
import type { NextRequest } from "next/server";
import { activityFor } from "@/lib/decisions-db";

/** GET /api/activity?id=… → who did what on this task, newest first. */
async function handleGET(req: NextRequest) {
  return Response.json({ rows: activityFor(req.nextUrl.searchParams.get("id") ?? "") });
}

// Each handler runs in the caller's language, so any text it builds matches the page.
export const GET = (...a: Parameters<typeof handleGET>) => withLang(() => handleGET(...a));

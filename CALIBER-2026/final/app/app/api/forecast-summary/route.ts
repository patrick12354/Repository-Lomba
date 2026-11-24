import { withLang } from "@/lib/i18n-server";
import type { NextRequest } from "next/server";
import { outlook } from "@/lib/data";

async function handleGET(req: NextRequest) {
  void req.nextUrl;
  return Response.json(outlook());
}

// Each handler runs in the caller's language, so any text it builds matches the page.
export const GET = (...a: Parameters<typeof handleGET>) => withLang(() => handleGET(...a));

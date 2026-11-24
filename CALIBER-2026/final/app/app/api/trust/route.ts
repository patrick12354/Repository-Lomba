import { withLang } from "@/lib/i18n-server";
import type { NextRequest } from "next/server";
import { trust } from "@/lib/data";

async function handleGET(req: NextRequest) {
  void req.nextUrl;
  return Response.json(trust());
}

// Each handler runs in the caller's language, so any text it builds matches the page.
export const GET = (...a: Parameters<typeof handleGET>) => withLang(() => handleGET(...a));

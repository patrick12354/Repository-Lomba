import { t } from "@/lib/i18n";
import { withLang } from "@/lib/i18n-server";
import type { NextRequest } from "next/server";
import { brief, type BriefPage } from "@/lib/assistant";
import { currentUser, signInFirst } from "@/lib/auth";

const PAGES: BriefPage[] = ["todo", "stock", "forecast", "whatif", "check", "plant", "replay"];

async function handlePOST(req: NextRequest) {
  const me = await currentUser();
  if (!me) return signInFirst();
  const { page } = (await req.json().catch(() => ({}))) as { page?: BriefPage };
  if (!page || !PAGES.includes(page)) return Response.json({ error: t("Unknown page.", "Halaman tidak dikenal.") }, { status: 400 });
  return Response.json(await brief(page, me));
}

// Each handler runs in the caller's language, so any text it builds matches the page.
export const POST = (...a: Parameters<typeof handlePOST>) => withLang(() => handlePOST(...a));

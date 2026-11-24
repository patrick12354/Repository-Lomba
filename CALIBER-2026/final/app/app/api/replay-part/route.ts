import { connection } from "next/server";
import type { NextRequest } from "next/server";
import { replayPart } from "@/lib/data";
import { t } from "@/lib/i18n";
import { withLang } from "@/lib/i18n-server";

/** GET ?id= → one part's month-by-month replay. */
async function handleGET(req: NextRequest) {
  await connection();
  const part = replayPart(Number(req.nextUrl.searchParams.get("id")));
  return part ? Response.json(part) : Response.json({ error: t("That part is not in the replay.", "Suku cadang itu tidak ada dalam simulasi ulang.") }, { status: 404 });
}

// Each handler runs in the caller's language, so any text it builds matches the page.
export const GET = (...a: Parameters<typeof handleGET>) => withLang(() => handleGET(...a));

import { withLang } from "@/lib/i18n-server";
import { connection } from "next/server";
import { learning } from "@/lib/decisions-db";

/** GET → what planners have decided and why (live, from the demo SQLite). The engine does not read this yet. */
async function handleGET() {
  await connection();
  return Response.json(learning());
}

// Each handler runs in the caller's language, so any text it builds matches the page.
export const GET = (...a: Parameters<typeof handleGET>) => withLang(() => handleGET(...a));

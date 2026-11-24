import { withLang } from "@/lib/i18n-server";
import { connection } from "next/server";
import { currentUser, signInFirst } from "@/lib/auth";
import { mailConfigured } from "@/lib/mail";

async function handleGET() {
  await connection();
  const me = await currentUser();
  return me ? Response.json({ me, mail: mailConfigured() }) : signInFirst();
}

// Each handler runs in the caller's language, so any text it builds matches the page.
export const GET = (...a: Parameters<typeof handleGET>) => withLang(() => handleGET(...a));

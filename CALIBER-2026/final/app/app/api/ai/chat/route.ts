import { t } from "@/lib/i18n";
import { withLang } from "@/lib/i18n-server";
import type { NextRequest } from "next/server";
import { assistant, type ChatTurn } from "@/lib/assistant";
import { currentUser, signInFirst } from "@/lib/auth";

/** POST {messages, page}. Only the last few plain user and assistant turns reach the model. */
async function handlePOST(req: NextRequest) {
  const me = await currentUser();
  if (!me) return signInFirst();
  const b = (await req.json().catch(() => ({}))) as { messages?: unknown; page?: unknown };
  const history: ChatTurn[] = (Array.isArray(b.messages) ? b.messages : [])
    .filter((m): m is ChatTurn => !!m && (m.role === "user" || m.role === "assistant") && typeof m.content === "string")
    .slice(-10)
    .map((m) => ({ role: m.role, content: m.content.slice(0, 1200) }));
  if (history.at(-1)?.role !== "user") return Response.json({ error: t("Ask a question first.", "Ajukan pertanyaan terlebih dahulu.") }, { status: 400 });
  return Response.json(await assistant(history, me, typeof b.page === "string" ? b.page.slice(0, 40) : "app"));
}

// Each handler runs in the caller's language, so any text it builds matches the page.
export const POST = (...a: Parameters<typeof handlePOST>) => withLang(() => handlePOST(...a));

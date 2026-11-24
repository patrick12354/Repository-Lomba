import { withLang } from "@/lib/i18n-server";
import { tasks } from "@/lib/data";

/** GET /api/alerts → only the tasks that cannot wait: too late to buy, or to be ordered this week. */
async function handleGET() {
  return Response.json({ items: tasks().filter((t) => t.urgency === "late" || t.urgency === "now") });
}

// Each handler runs in the caller's language, so any text it builds matches the page.
export const GET = (...a: Parameters<typeof handleGET>) => withLang(() => handleGET(...a));

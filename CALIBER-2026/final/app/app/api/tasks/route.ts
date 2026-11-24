import { withLang } from "@/lib/i18n-server";
import { tasks } from "@/lib/data";

/** GET /api/tasks → every open task, one per part. Workflow status lives in /api/decisions. */
async function handleGET() {
  return Response.json({ tasks: tasks() });
}

// Each handler runs in the caller's language, so any text it builds matches the page.
export const GET = (...a: Parameters<typeof handleGET>) => withLang(() => handleGET(...a));

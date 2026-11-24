import "server-only";
import { chat } from "./ai";
import { guessReason, REASON_CODES, REASONS, type ReasonCode } from "./reasons";
import { isId, t } from "./i18n";

/**
 * Sort a planner's own words for a rejection into one of the recorded reasons.
 * The AI reads the note with the task; the keyword sorter runs when AI is off or answers outside the list.
 */
export async function sortReason(note: string, task: { kind: string; description: string } | null): Promise<{ reason: ReasonCode | null; why: string; source: "ai" | "keywords" }> {
  const text = note.trim().slice(0, 280);
  const raw = text
    ? await chat(
        `You sort why a spare-parts planner rejected a suggestion. Pick the one reason that fits best, or "none" if none fits. Reasons: ${REASONS.map((r) => `${r.code} = ${r.label} (${r.hint})`).join("; ")}. The note may be written in English or Indonesian. Reply with the code and a short clause in ${isId() ? "formal, natural Bahasa Indonesia" : "plain English"} saying what in the note points to it.`,
        `SUGGESTION: ${task ? `${task.kind} for ${task.description}` : "unknown"}\nPLANNER NOTE: ${text}`,
        { name: "reason", schema: { type: "object", additionalProperties: false, required: ["code", "why"], properties: { code: { type: "string", enum: [...REASON_CODES, "none"] }, why: { type: "string" } } } },
      )
    : null;
  if (raw) {
    try {
      const j = JSON.parse(raw) as { code: string; why: string };
      if (REASON_CODES.includes(j.code)) return { reason: j.code as ReasonCode, why: j.why.slice(0, 160), source: "ai" };
      if (j.code === "none") return { reason: null, why: j.why.slice(0, 160), source: "ai" };
    } catch {
      /* fall through to keywords */
    }
  }
  const g = guessReason(text);
  return { reason: g, why: g ? t("Matched on words in the note.", "Dicocokkan dari kata-kata dalam catatan.") : t("No reason recognised in the note.", "Tidak ada alasan yang dikenali dalam catatan."), source: "keywords" };
}

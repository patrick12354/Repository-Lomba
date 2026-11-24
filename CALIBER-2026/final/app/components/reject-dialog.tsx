"use client";

import { useEffect, useState } from "react";
import { Loader2, Sparkles, X } from "lucide-react";
import type { Task } from "@/lib/data";
import { cn, partName } from "@/lib/format";
import { REASONS, reasonOf, type ReasonCode } from "@/lib/reasons";
import { t } from "@/lib/i18n";

export type RejectWhy = { reason?: string; note?: string; reason_source?: string };

/**
 * Rejecting asks why, in one press. The reason is recorded for the rule the engine will apply later;
 * a note in the planner's own words is sorted into a reason by AI.
 */
export function RejectDialog({ task, onCancel, onReject }: { task: Task; onCancel: () => void; onReject: (why: RejectWhy) => void }) {
  const [pick, setPick] = useState<ReasonCode | null>(null);
  const [note, setNote] = useState("");
  const [sorting, setSorting] = useState(false);
  const [sorted, setSorted] = useState<{ reason: ReasonCode | null; why: string; source: "ai" | "keywords" } | null>(null);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onCancel();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onCancel]);

  const sort = () => {
    if (!note.trim()) return;
    setSorting(true);
    fetch("/api/ai/reason", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ note, material_no: task.material_no }) })
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(String(r.status)))))
      .then((j: { reason: ReasonCode | null; why: string; source: "ai" | "keywords" }) => {
        setSorted(j);
        if (j.reason) setPick(j.reason);
      })
      .catch(() => setSorted({ reason: null, why: t("Could not sort the note. Pick a reason above.", "Catatan gagal dikelompokkan. Pilih alasan di atas."), source: "keywords" }))
      .finally(() => setSorting(false));
  };

  const chosen = reasonOf(pick);
  const fromAi = !!sorted?.reason && sorted.reason === pick;

  return (
    <div className="fixed inset-0 z-[60] grid place-items-center p-4" role="dialog" aria-modal="true" aria-label={t("Why reject this?", "Mengapa ditolak?")}>
      <button type="button" aria-label={t("Close", "Tutup")} onClick={onCancel} className="absolute inset-0 bg-ink/30" />
      <div className="relative flex max-h-[92dvh] w-[min(520px,100%)] flex-col overflow-hidden rounded-[18px] border border-line bg-panel shadow-float">
        <header className="flex h-12 shrink-0 items-center gap-2 border-b border-line px-4">
          <h2 className="m-0 min-w-0 truncate text-[14px] font-semibold">{t(`Why not ${partName(task.description)}?`, `Mengapa ${partName(task.description)} ditolak?`)}</h2>
          <button type="button" onClick={onCancel} aria-label={t("Close", "Tutup")} className="ml-auto grid h-8 w-8 place-items-center rounded-[8px] text-ink-3 transition-colors hover:bg-ink/[0.05] hover:text-ink"><X aria-hidden className="h-4 w-4" /></button>
        </header>
        <div className="min-h-0 flex-1 space-y-3 overflow-y-auto p-4">
          <p className="m-0 text-[13px] leading-[1.5] text-ink-2">{t("Your reason is recorded. Each one has a planned rule for the engine, which starts reading them in the plant-wide phase. ", "Alasan Anda dicatat. Setiap alasan memiliki aturan yang direncanakan untuk mesin hitung, yang mulai membacanya pada fase seluruh kilang. ")}<a href="/check#learning" className="underline underline-offset-2">{t("See what has been recorded", "Lihat yang sudah tercatat")}</a>.</p>
          <div role="radiogroup" aria-label={t("Reason", "Alasan")} className="space-y-1.5">
            {REASONS.map((r) => (
              <button key={r.code} type="button" role="radio" aria-checked={pick === r.code} onClick={() => setPick(r.code)} className={cn("flex w-full flex-col rounded-[12px] border px-3 py-2 text-left transition-colors duration-150", pick === r.code ? "border-ink bg-panel-2" : "border-line hover:border-line-2")}>
                <span className="text-[13.5px] font-medium">{r.label}</span>
                <span className="text-[12px] text-ink-3">{r.hint}</span>
              </button>
            ))}
          </div>
          <label className="block">
            <span className="text-[12.5px] font-medium text-ink-2">{t("Or say it in your own words", "Atau tulis dengan kata-kata Anda sendiri")}</span>
            <span className="mt-1 flex gap-2">
              <input value={note} maxLength={280} onChange={(e) => { setNote(e.target.value); setSorted(null); }} onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), sort())} placeholder={t("e.g. the central store already has 4 of these", "misalnya: gudang pusat sudah punya 4 buah")} className="h-9 min-w-0 flex-1 rounded-[9px] border border-line-2 bg-panel px-3 text-[13px] outline-none focus:border-ink" />
              <button type="button" onClick={sort} disabled={!note.trim() || sorting} className="inline-flex h-9 shrink-0 items-center gap-1.5 rounded-[9px] border border-line-2 px-3 text-[12.5px] font-medium transition-colors hover:bg-ink/[0.04] disabled:opacity-50">
                {sorting ? <Loader2 aria-hidden className="h-3.5 w-3.5 animate-spin" /> : <Sparkles aria-hidden className="h-3.5 w-3.5" />}
                {t("Sort it", "Kelompokkan")}
              </button>
            </span>
            {sorted && <span className="mt-1.5 block text-[12px] leading-snug text-ink-3">{sorted.reason ? t(`${sorted.source === "ai" ? "AI" : "Keywords"} chose “${reasonOf(sorted.reason)!.label}”: ${sorted.why}`, `${sorted.source === "ai" ? "AI" : "Kata kunci"} memilih “${reasonOf(sorted.reason)!.label}”: ${sorted.why}`) : sorted.why}</span>}
          </label>
          {chosen && <p className="m-0 rounded-[10px] bg-panel-2 px-3 py-2 text-[12.5px] leading-[1.5] text-ink-2"><b className="font-semibold text-ink">{t("Planned rule: ", "Aturan yang direncanakan: ")}</b>{chosen.rule}</p>}
        </div>
        <footer className="flex shrink-0 items-center justify-end gap-2 border-t border-line px-4 py-3">
          <button type="button" onClick={() => onReject({ note: note.trim() || undefined })} className="mr-auto text-[12.5px] text-ink-3 underline underline-offset-2 hover:text-ink">{t("Reject without a reason", "Tolak tanpa alasan")}</button>
          <button type="button" onClick={onCancel} className="inline-flex h-9 items-center rounded-[10px] px-3 text-[13px] font-medium text-ink-2 transition-colors hover:bg-ink/[0.05]">{t("Cancel", "Batal")}</button>
          <button type="button" disabled={!pick} onClick={() => onReject({ reason: pick ?? undefined, note: note.trim() || undefined, reason_source: fromAi ? (sorted!.source === "ai" ? "ai" : "keywords") : "planner" })} className="inline-flex h-9 items-center rounded-[10px] bg-ink px-3.5 text-[13px] font-medium text-white transition-colors hover:bg-ink-2 disabled:opacity-40">{t("Reject", "Tolak")}</button>
        </footer>
      </div>
    </div>
  );
}

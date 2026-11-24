"use client";

import { useState } from "react";
import * as Popover from "@radix-ui/react-popover";
import { Loader2 } from "lucide-react";
import { Lightbulb } from "@/components/icons";
import { Glossary } from "./glossary";
import { t } from "@/lib/i18n";

type Brief = { headline: string; points: string[]; source: "openai" | "template" };

/** Opens the assistant from anywhere on the page, with a question already asked. */
export function askAssistant(question: string) {
  window.dispatchEvent(new CustomEvent("sk-ask", { detail: question }));
}

/** One press for what matters on this page, written for the person signed in. */
export function AiBrief({ page }: { page: "todo" | "stock" | "forecast" | "whatif" | "check" | "plant" | "replay" }) {
  const [brief, setBrief] = useState<Brief | null>(null);
  const [failed, setFailed] = useState(false);

  const load = (open: boolean) => {
    if (!open || brief) return;
    setFailed(false);
    fetch("/api/ai/brief", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ page }) })
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(String(r.status)))))
      .then(setBrief)
      .catch(() => setFailed(true));
  };

  return (
    <>
    <Glossary />
    <Popover.Root onOpenChange={load}>
      <Popover.Trigger asChild>
        <button type="button" data-tour="ai-overview" className="inline-flex h-9 shrink-0 items-center gap-2 rounded-[10px] border border-line bg-panel px-3 text-[13px] font-medium transition-colors hover:border-line-2">
          <Lightbulb aria-hidden className="h-4 w-4" />{t("AI overview", "Ringkasan AI")}
        </button>
      </Popover.Trigger>
      <Popover.Portal>
        <Popover.Content align="end" sideOffset={6} className="z-40 w-[380px] max-w-[92vw] rounded-[14px] border border-line bg-panel p-4 shadow-float">
          {failed ? (
            <p className="m-0 text-[13px] text-ink-3">{t("Could not write the overview. Try again.", "Ringkasan gagal dibuat. Coba lagi.")}</p>
          ) : !brief ? (
            <div className="flex items-center gap-2 text-[13px] text-ink-3"><Loader2 aria-hidden className="h-4 w-4 animate-spin" />{t("Reading this page…", "Membaca halaman ini…")}</div>
          ) : (
            <>
              <p className="m-0 text-[14px] font-semibold leading-snug">{brief.headline}</p>
              <ul className="m-0 mt-2 list-disc space-y-1.5 pl-4 text-[13px] leading-[1.5] text-ink-2">
                {brief.points.map((p) => <li key={p}>{p}</li>)}
              </ul>
              <div className="mt-3 flex items-center justify-between gap-2">
                <span className="text-[11.5px] text-ink-4">{brief.source === "openai" ? t("Written by AI · numbers from the engine", "Ditulis oleh AI · angka dari mesin hitung") : t("Template text · AI is off", "Teks templat · AI tidak aktif")}</span>
                <button type="button" onClick={() => askAssistant(t(`Tell me more about this: ${brief.headline}`, `Jelaskan lebih lanjut: ${brief.headline}`))} className="shrink-0 text-[12.5px] font-medium text-ink-2 underline underline-offset-2 hover:text-ink">{t("Ask a follow-up", "Tanya lebih lanjut")}</button>
              </div>
            </>
          )}
        </Popover.Content>
      </Popover.Portal>
    </Popover.Root>
    </>
  );
}

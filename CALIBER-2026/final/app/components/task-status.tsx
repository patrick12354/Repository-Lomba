"use client";

import Link from "next/link";
import { ArrowRight } from "lucide-react";
import type { TaskKind } from "@/lib/data";
import { useDecisions } from "@/lib/decisions";
import { firstName, ownerOf, type Section } from "@/lib/people";
import { bi, t } from "@/lib/i18n";

const STAGE: Record<string, string> = bi({ todo: ["To decide", "Perlu diputuskan"], approved: ["Approved", "Disetujui"], in_progress: ["In progress", "Sedang berjalan"], done: ["Done", "Selesai"], rejected: ["Rejected", "Ditolak"] });

/** Where the task stands, who holds it, and the one way to act on it: the To do board. */
export function ReviewInTodo({ id }: { id: number }) {
  return (
    <Link href={`/todo?open=${id}`} className="inline-flex h-10 shrink-0 items-center gap-1.5 rounded-[10px] bg-ink px-3.5 text-[13.5px] font-medium text-white transition-colors hover:bg-ink-2">
      {t("Review in To do", "Tinjau di Tugas")}
      <ArrowRight aria-hidden className="h-4 w-4" />
    </Link>
  );
}

export function TaskStatus({ id, kind, section }: { id: number; kind: TaskKind; section: Section }) {
  const d = useDecisions();
  const stage: string = d.get(id) ?? "todo";
  const owner = ownerOf({ kind, section, urgency: "later" });
  const o = firstName(owner);
  const buys = kind === "order" || kind === "expedite";
  const who =
    kind === "watch"
      ? t(`${o} watches it`, `${o} memantaunya`)
      : stage === "todo"
        ? t(`Nadia decides, then ${o} ${buys ? "buys" : "runs it"}`, `Nadia memutuskan, lalu ${o} ${buys ? "membelinya" : "menjalankannya"}`)
        : stage === "rejected"
          ? t("Not going ahead", "Tidak dilanjutkan")
          : stage === "done"
            ? t("Closed", "Ditutup")
            : t(`${o} is handling it`, `${o} sedang menanganinya`);
  return (
    <p className="m-0 text-[12.5px] text-ink-3">
      Status: <b className="font-medium text-ink">{STAGE[stage]}</b> · {who}
      {d.emailed[String(id)] ? t(" · Email sent", " · Surel terkirim") : t(" · No email yet", " · Belum ada surel")}
    </p>
  );
}

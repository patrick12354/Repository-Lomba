"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { BrainCircuit, CalendarSync, Check, Users, Wrench, X } from "lucide-react";
import { partName, pct, shortDate } from "@/lib/format";
import { reasonOf } from "@/lib/reasons";
import { noteText } from "./todo-shared";
import { Panel, PanelHead } from "./ui";
import { bi, t } from "@/lib/i18n";

type Learned = {
  decided: number;
  rejected: number;
  reasons: { code: string; n: number; parts: { material_no: number | null; description: string; note: string | null; source: string | null }[] }[];
  acceptance: { kind: string; yes: number; no: number; rate: number }[];
};

const KIND_NAME: Record<string, string> = bi({ expedite: ["rush orders", "pesanan percepatan"], order: ["orders", "pesanan"], twin: ["use a duplicate part", "pemakaian suku cadang kembar"], reduce: ["cut stock", "pengurangan stok"], dispose: ["disposal reviews", "tinjauan penghapusan"], watch: ["watch items", "item pantauan"] });

const MIN_SAMPLE = 5;

/** The three ways the system is meant to get better, how far each has got, and the live record of planner decisions. */
export function LearningLoop({ monthly, taDate }: { monthly: number[]; taDate: string }) {
  const [learned, setLearned] = useState<Learned>({ decided: 0, rejected: 0, reasons: [], acceptance: [] });
  const [ready, setReady] = useState(false);
  useEffect(() => {
    const ctl = new AbortController();
    fetch("/api/learning", { cache: "no-store", signal: ctl.signal })
      .then((r) => (r.ok ? r.json() : null))
      .then((j: Learned | null) => {
        if (j) setLearned(j);
        setReady(true);
      })
      .catch(() => setReady(true));
    return () => ctl.abort();
  }, []);
  // Only the kinds someone has turned down: those are the ones a rule would adjust.
  // A rate from a handful of decisions reads as a verdict it cannot support, so it waits for a real sample.
  const kinds = learned.acceptance.filter((a) => a.no > 0 && a.yes + a.no >= MIN_SAMPLE);
  return (
    <Panel tour="c-learn">
      <span id="learning" className="block scroll-mt-24" />
      <PanelHead title={t("How Sparekit keeps learning", "Cara Sparekit terus belajar")} icon={BrainCircuit} />
      <p className="m-0 px-5 pt-1 text-[13px] leading-[1.5] text-ink-2">{t("A fixed Min and Max goes stale. Sparekit is built around three loops, each on its own clock. Each one says how far it has got in this prototype.", "Min dan Max yang tetap lama-lama menjadi usang. Sparekit dibangun di atas tiga putaran, masing-masing dengan jadwalnya sendiri. Setiap putaran menyebutkan sejauh mana penerapannya pada prototipe ini.")}</p>
      <div className="grid grid-cols-1 gap-4 p-5 lg:grid-cols-3">
        <Loop icon={CalendarSync} when={t("Every month", "Setiap bulan")} status={t("Tested on past months. A schedule starts with the pilot", "Diuji pada bulan-bulan lalu. Jadwal rutin dimulai saat uji coba")} title={t("It checks its own forecast", "Memeriksa prakiraannya sendiri")} body={t("Retrain on the newest use, score the forecast against what really happened, then set new limits. We ran this over past months, and the Replay page plays the result back.", "Latih ulang dengan pemakaian terbaru, nilai prakiraan terhadap kejadian yang sebenarnya, lalu tetapkan batas baru. Kami menjalankannya pada bulan-bulan lalu, dan halaman Simulasi ulang memutar hasilnya.")}>
          <p className="m-0 text-[12.5px] text-ink-2">
            {t("Scores so far, out of 100: ", "Skor sejauh ini, dari 100: ")}<b className="font-semibold tabular-nums text-ink">{monthly.map((v) => Math.round(v * 100)).join(", ")}</b>{t(". Each month was predicted with only the data before it.", ". Setiap bulan diprakirakan hanya dengan data sebelum bulan itu.")}
          </p>
        </Loop>

        <Loop icon={Users} when={t("Every decision", "Setiap keputusan")} status={t("Reasons are recorded now. The engine reads them from the plant-wide phase", "Alasan sudah tercatat. Mesin hitung membacanya mulai fase seluruh kilang")} title={t("It learns from the planner", "Belajar dari perencana")} body={t("Every rejection carries a reason. A note in the planner's own words is sorted into a reason by AI. Each reason has a planned rule for the engine, and in this prototype the engine does not read them yet.", "Setiap penolakan disertai alasan. Catatan yang ditulis perencana dengan kata-katanya sendiri dikelompokkan ke salah satu alasan oleh AI. Setiap alasan memiliki aturan yang direncanakan untuk mesin hitung, dan pada prototipe ini mesin hitung belum membacanya.")}>
          {!ready ? (
            <div className="h-24 animate-pulse rounded-[10px] bg-ink/[0.05]" />
          ) : learned.reasons.length ? (
            <ul className="m-0 list-none space-y-2 p-0">
              {learned.reasons.slice(0, 4).map((r) => {
                const info = reasonOf(r.code);
                const ex = r.parts[0];
                return (
                  <li key={r.code} className="text-[12.5px] leading-snug">
                    <div className="font-medium text-ink">{info ? info.label : t("No reason given", "Tanpa alasan")} <span className="font-normal text-ink-3">· {r.n} {t(r.n === 1 ? "part" : "parts", "suku cadang")}</span></div>
                    {info && <div className="text-ink-2">{t("Planned rule: ", "Aturan yang direncanakan: ")}{info.rule}</div>}
                    {ex?.note && <div className="mt-0.5 truncate text-ink-3" title={noteText(ex.note)}>“{noteText(ex.note)}” {ex.material_no != null && <Link href={`/parts/${ex.material_no}`} className="underline underline-offset-2">{partName(ex.description)}</Link>}{ex.source === "ai" && t(" · sorted by AI", " · dikelompokkan oleh AI")}</div>}
                  </li>
                );
              })}
            </ul>
          ) : (
            <p className="m-0 text-[12.5px] text-ink-3">{t("No rejections yet. Reject a task on the To do board to see it here.", "Belum ada penolakan. Tolak sebuah tugas di papan Tugas untuk melihatnya di sini.")}</p>
          )}
          {kinds.length > 0 && (
            <p className="m-0 mt-2 border-t border-line pt-2 text-[12px] leading-snug text-ink-3">
              {learned.reasons.length > 0 && <span className="block pb-1">{t("The demo starts with a few example decisions, so these are not real planner records.", "Demo dimulai dengan beberapa keputusan contoh, jadi ini bukan catatan perencana yang sebenarnya.")}</span>}
              {t("In this demo, the planner agrees with ", "Dalam demo ini, perencana menyetujui ")}{kinds.map((k, i) => <span key={k.kind}>{i > 0 && (i === kinds.length - 1 ? t(" and ", " dan ") : ", ")}<b className="font-semibold text-ink">{pct(k.rate)}</b> {t("of", "dari")} {KIND_NAME[k.kind] ?? k.kind} ({k.yes}/{k.yes + k.no})</span>)}{t(". The roadmap uses this rate as a gate before going plant-wide.", ". Peta jalan memakai angka ini sebagai syarat sebelum diterapkan di seluruh kilang.")}
            </p>
          )}
        </Loop>

        <Loop icon={Wrench} when={t("Every turnaround", "Setiap turnaround")} status={t("Starting kit is built. The update comes after the next turnaround", "Paket awal sudah dibuat. Pembaruan dilakukan setelah turnaround berikutnya")} title={t("It remembers each turnaround", "Mengingat setiap turnaround")} body={t("The kit for the next turnaround starts from what the last one really used, scaled to its size. Afterwards, real use will replace the plan part by part, so each kit starts closer than the last.", "Paket untuk turnaround berikutnya dimulai dari pemakaian riil turnaround sebelumnya, disesuaikan dengan skalanya. Setelah itu, pemakaian riil akan menggantikan rencana suku cadang demi suku cadang, sehingga setiap paket berangkat lebih akurat daripada sebelumnya.")}>
          <p className="m-0 text-[12.5px] text-ink-2">{t(`The data holds one turnaround, Nov 2025 to Jan 2026, which is today's starting kit. The first update comes after the one planned for ${shortDate(taDate, true)}.`, `Data memuat satu turnaround, Nov 2025 sampai Jan 2026, yang menjadi paket awal saat ini. Pembaruan pertama dilakukan setelah turnaround yang direncanakan pada ${shortDate(taDate, true)}.`)}</p>
        </Loop>
      </div>

      <div className="grid grid-cols-1 gap-x-8 border-t border-line px-5 py-4 md:grid-cols-2">
        <div>
          <h3 className="m-0 text-[13px] font-semibold">{t("What the AI does", "Yang dilakukan AI")}</h3>
          <ul className="m-0 mt-1.5 list-none space-y-1 p-0 text-[12.5px] leading-snug text-ink-2">
            {t([
              "Predicts which parts will be used, including parts never used before",
              "Simulates many possible futures to set Min and Max at each part's target",
              "Explains each suggestion and drafts the email to the next person",
              "Sorts a planner's note into one of five reasons",
            ], [
              "Memprakirakan suku cadang yang akan terpakai, termasuk yang belum pernah dipakai",
              "Menyimulasikan berbagai kemungkinan masa depan untuk menetapkan Min dan Max sesuai target tiap suku cadang",
              "Menjelaskan setiap saran dan menyusun draf surel untuk orang berikutnya",
              "Mengelompokkan catatan perencana ke dalam salah satu dari lima alasan",
            ]).map((x) => <li key={x} className="flex gap-2"><Check aria-hidden className="mt-0.5 h-3.5 w-3.5 shrink-0 text-ready-ink" />{x}</li>)}
          </ul>
        </div>
        <div>
          <h3 className="m-0 text-[13px] font-semibold">{t("What it does not do", "Yang tidak dilakukannya")}</h3>
          <ul className="m-0 mt-1.5 list-none space-y-1 p-0 text-[12.5px] leading-snug text-ink-2">
            {t([
              "Place an order or change SAP by itself: a person approves every step",
              "Make up a number: every figure in its text comes from the engine",
              "Send an email unread: each one opens for the sender to check first",
              "Override criticality: that stays the plant's own call",
            ], [
              "Memesan atau mengubah SAP sendiri: setiap langkah disetujui oleh manusia",
              "Mengarang angka: setiap angka dalam teksnya berasal dari mesin hitung",
              "Mengirim surel tanpa dibaca: setiap surel dibuka dulu agar pengirim bisa memeriksanya",
              "Mengubah kekritisan: keputusan itu tetap menjadi wewenang kilang",
            ]).map((x) => <li key={x} className="flex gap-2"><X aria-hidden className="mt-0.5 h-3.5 w-3.5 shrink-0 text-act-ink" />{x}</li>)}
          </ul>
        </div>
      </div>
    </Panel>
  );
}

function Loop({ icon: Icon, when, status, title, body, children }: { icon: typeof Check; when: string; status: string; title: string; body: string; children: React.ReactNode }) {
  return (
    <div className="flex flex-col rounded-[14px] bg-panel-2 p-4">
      <div className="flex items-center gap-2">
        <span className="grid h-8 w-8 place-items-center rounded-[10px] bg-panel text-ink-2 shadow-card"><Icon aria-hidden className="h-4 w-4" /></span>
        <span className="text-[11.5px] font-semibold uppercase tracking-[0.04em] text-ink-3">{when}</span>
      </div>
      <h3 className="m-0 mt-2.5 text-[14px] font-semibold">{title}</h3>
      <p className="m-0 mt-1 text-[12.5px] leading-[1.5] text-ink-2">{body}</p>
      <p className="m-0 mt-2 rounded-[8px] bg-panel px-2.5 py-1.5 text-[12px] font-medium leading-snug text-ink-2">{status}</p>
      <div className="mt-3 border-t border-line pt-3">{children}</div>
    </div>
  );
}

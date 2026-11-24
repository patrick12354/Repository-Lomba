"use client";

import { useState } from "react";
import { Wrench } from "@/components/icons";
import type { NotifCode, PmMajor, PmMonth } from "@/lib/data";
import { cn, monthLabel, num, shortDate } from "@/lib/format";
import { CODE_NAME } from "@/lib/people";
import { Panel, PanelHead } from "./ui";
import { Hint } from "./hint";
import { t } from "@/lib/i18n";

/** A month strip of planned jobs until the turnaround. Pressing a month lists its long-cycle jobs. */
export function MaintenanceAhead({ months, major, notices, taDate }: { months: PmMonth[]; major: PmMajor[]; notices: NotifCode[]; taDate: string }) {
  const busiest = months.reduce((b, m, i) => (m.major > months[b].major ? i : b), 0);
  const [idx, setIdx] = useState(busiest);
  const month = months[idx];
  const top = Math.max(1, ...months.map((m) => m.jobs));
  const list = major.filter((m) => m.month === month.month).slice(0, 5);
  const totalJobs = months.reduce((a, m) => a + m.jobs, 0);
  const totalMajor = months.reduce((a, m) => a + m.major, 0);

  return (
    <Panel tour="f-maint">
      <PanelHead
        title={
          <span className="flex items-center gap-1">
            {t("Maintenance work ahead", "Pekerjaan pemeliharaan ke depan")}
            <Hint>{t("From the maintenance plans: each plan's start date and cycle give the dates it falls due. The maintenance files list no parts, so this shows the parts fitted on that equipment, not a parts list for the job. In this data the dates did not improve the forecast, so they are here for the planner, not in the score.", "Dari rencana pemeliharaan: tanggal mulai dan siklus tiap rencana menghasilkan tanggal jatuh temponya. Berkas pemeliharaan tidak mencantumkan suku cadang, jadi yang ditampilkan adalah suku cadang yang terpasang pada peralatan itu, bukan daftar kebutuhan pekerjaannya. Pada data ini tanggal tersebut tidak memperbaiki prakiraan, jadi ditampilkan untuk perencana, bukan untuk skor.")}</Hint>
          </span>
        }
        icon={Wrench}
        aside={<span className="text-[12px] tabular-nums text-ink-3">{t(`${num(totalJobs)} jobs until ${shortDate(taDate, true)}, ${num(totalMajor)} on a cycle of 2 years or more`, `${num(totalJobs)} pekerjaan sampai ${shortDate(taDate, true)}, ${num(totalMajor)} bersiklus 2 tahun atau lebih`)}</span>}
      />
      <div className="grid grid-cols-1 gap-5 px-5 pb-5 pt-3 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.25fr)]">
        <div className="min-w-0">
          <ul className="m-0 flex list-none items-end gap-1.5 p-0">
            {months.map((m, i) => (
              <li key={m.month} className="min-w-0 flex-1">
                <button type="button" onClick={() => setIdx(i)} aria-pressed={i === idx} className={cn("w-full rounded-[10px] px-1 py-2 transition-colors", i === idx ? "bg-panel-2 ring-1 ring-line-2" : "hover:bg-ink/[0.03]")}>
                  <span className="block text-center text-[12px] font-semibold tabular-nums">{num(m.major)}</span>
                  <span className="mt-1 flex h-[84px] items-end justify-center">
                    <span className="w-full max-w-[28px] rounded-t-[4px] bg-ink-2/25" style={{ height: `${Math.max(4, (m.jobs / top) * 100)}%` }} />
                  </span>
                  <span className={cn("mt-1 block whitespace-nowrap text-center text-[11px]", i === idx ? "font-semibold text-ink" : "text-ink-3")}>{monthLabel(m.month)}</span>
                </button>
              </li>
            ))}
          </ul>
          <p className="m-0 mt-2 text-[12px] leading-snug text-ink-3">{t("Bar: all planned jobs that month. Number: jobs on a cycle of 2 years or more.", "Batang: semua pekerjaan terencana bulan itu. Angka: pekerjaan bersiklus 2 tahun atau lebih.")}</p>
          <h3 className="m-0 mt-4 text-[13px] font-semibold">{t("Breakdown notices, last 90 days", "Laporan kerusakan, 90 hari terakhir")}</h3>
          <ul className="m-0 mt-1.5 grid list-none grid-cols-2 gap-x-4 gap-y-1 p-0 text-[12.5px] tabular-nums text-ink-2">
            {notices.map((n) => (
              <li key={n.code} className="flex justify-between gap-2">
                <span className="truncate">{CODE_NAME[n.code] ?? n.code}</span>
                <span className="shrink-0"><b className="font-semibold text-ink">{num(n.notices)}</b>{n.emergency > 0 && <span className="text-act-ink"> · {t(`${num(n.emergency)} emergency`, `${num(n.emergency)} darurat`)}</span>}</span>
              </li>
            ))}
          </ul>
        </div>
        <div className="min-w-0">
          <h3 className="m-0 text-[13px] font-semibold">{t(`Long-cycle jobs in ${monthLabel(month.month)}, most exposed first`, `Pekerjaan bersiklus panjang pada ${monthLabel(month.month)}, yang paling rawan lebih dulu`)}</h3>
          {list.length ? (
            <ul className="m-0 mt-1 list-none divide-y divide-line p-0">
              {list.map((m) => (
                <li key={`${m.fl}-${m.task}-${m.due}`} className="py-2 text-[13px]">
                  <div className="flex items-baseline justify-between gap-3">
                    <span className="min-w-0 truncate font-medium">{m.task}</span>
                    <span className="shrink-0 text-[12px] tabular-nums text-ink-3">{shortDate(m.due, true)}</span>
                  </div>
                  <div className="mt-0.5 flex items-baseline justify-between gap-3 text-[12px] text-ink-3">
                    <span className="min-w-0 truncate">{m.fl_desc} · {m.cycle_text.toLowerCase()}</span>
                    <span className="shrink-0 tabular-nums">{t(`${num(m.parts)} parts fitted`, `${num(m.parts)} suku cadang terpasang`)}{m.parts_low > 0 && <b className="font-semibold text-act-ink"> · {t(`${num(m.parts_low)} low`, `${num(m.parts_low)} menipis`)}</b>}</span>
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <p className="m-0 mt-2 text-[13px] text-ink-3">{t("None this month.", "Tidak ada pada bulan ini.")}</p>
          )}
          <p className="m-0 mt-2 text-[12px] leading-snug text-ink-3">{t("Low means a stocked part that is empty or below its Min in SAP.", "Menipis berarti suku cadang stok yang kosong atau di bawah Min di SAP.")}</p>
        </div>
      </div>
    </Panel>
  );
}

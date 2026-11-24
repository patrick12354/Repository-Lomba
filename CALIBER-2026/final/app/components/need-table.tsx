"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { ChevronRight } from "lucide-react";
import { Search } from "@/components/icons";
import type { NeedRow } from "@/lib/data";
import { amount, categoryName, cn, num, partName, shortDate, shortPartName, subtypeName, subtypeOf } from "@/lib/format";
import { Panel, SevBar, sevOf, type Severity } from "./ui";
import { Hint } from "./hint";
import { t } from "@/lib/i18n";

type View = "short" | "bad" | "ta" | "new" | "all";

const COLS = "grid-cols-[minmax(0,2.2fr)_minmax(0,0.9fr)_minmax(0,1.1fr)_minmax(0,1.1fr)_minmax(0,1.2fr)]";
const PAGE = 12;

const shortOf = (r: NeedRow) => r.gap > 0 || r.likely6 > r.have;
const sev = (r: NeedRow): Severity => sevOf({ short: shortOf(r), late: r.late, critical: r.criticality === "A" || r.criticality === "B", empty: r.have <= 0 });

function Counts({ items }: { items: NeedRow[] }) {
  const bad = items.filter((r) => sev(r) === "bad").length;
  const warn = items.filter((r) => sev(r) === "warn").length;
  const ok = items.length - bad - warn;
  return (
    <span className="flex shrink-0 items-center gap-1.5 text-[12px] font-medium tabular-nums">
      {bad > 0 && <span className="rounded-[6px] bg-act-soft px-1.5 py-0.5 text-act-ink" title={t("Too late, or critical and empty", "Terlambat, atau kritis dan kosong")}>{bad} {t("urgent", "mendesak")}</span>}
      {warn > 0 && <span className="rounded-[6px] bg-plan-soft px-1.5 py-0.5 text-plan-ink" title={t("Short, still time to order", "Kurang, masih sempat dipesan")}>{warn} {t("to order", "perlu dipesan")}</span>}
      {ok > 0 && <span className="rounded-[6px] bg-ready-soft px-1.5 py-0.5 text-ready-ink" title={t("Enough stock", "Stok cukup")}>{ok} {t("enough", "cukup")}</span>}
    </span>
  );
}

function Row({ r, subtype, indent }: { r: NeedRow; subtype: string | null; indent: string }) {
  const shortNow = r.likely6 > r.have;
  const s = sev(r);
  return (
    <li>
      <Link href={`/parts/${r.material_no}`} className={cn("relative grid items-center gap-3 py-2.5 pr-5 text-[12.5px] tabular-nums transition-colors hover:bg-ink/[0.03]", indent, COLS)}>
        <SevBar sev={s} className="left-[calc(var(--bar)-12px)]" />
        <span className="flex min-w-0 items-center gap-2">
          <span className="min-w-0 truncate text-[13px] font-medium" title={`${partName(r.description)} · ${t("criticality", "kekritisan")} ${r.criticality}`}>{shortPartName(r.description, subtype)}</span>
        </span>
        <span className="font-semibold">{amount(r.have, r.unit)}</span>
        <span className={cn(shortNow && "font-medium text-act-ink")}>{amount(r.likely6, r.unit)}<span className="block text-[11.5px] font-normal text-ink-3">{t("bad case", "terburuk")} {amount(r.bad6, r.unit)}</span></span>
        <span className={cn(r.gap > 0 && "font-medium text-act-ink")}>{r.total > 0 ? amount(r.total, r.unit) : <span className="text-ink-4">{t("Not in the turnaround", "Tidak masuk turnaround")}</span>}</span>
        <span className={cn(s === "bad" ? "font-medium text-act-ink" : s === "warn" ? "text-plan-ink" : "text-ready-ink")}>
          {r.gap > 0 ? <>{r.late ? t("Too late, rush ", "Terlambat, percepat ") : t("Order ", "Pesan ")}{amount(r.order_qty, r.unit)}<span className="block text-[11.5px] text-ink-3">{r.late || !r.order_by ? "" : r.order_now ? t("now", "sekarang") : t(`by ${shortDate(r.order_by, true)}`, `paling lambat ${shortDate(r.order_by, true)}`)}</span></> : shortNow ? <>{t("Order ", "Pesan ")}{amount(r.order_qty > 0 ? r.order_qty : r.likely6 - r.have, r.unit)}{r.order_qty > 0 && r.order_by && <span className="block text-[11.5px] text-ink-3">{r.order_now ? t("now", "sekarang") : t(`by ${shortDate(r.order_by, true)}`, `paling lambat ${shortDate(r.order_by, true)}`)}</span>}</> : t("Enough for now", "Cukup untuk saat ini")}
        </span>
      </Link>
    </li>
  );
}

/** The forecast's real answer, grouped by part type and sub-type: what we have against what we will need, and by when. */
export function NeedTable({ rows, forecastEnds, taDate }: { rows: NeedRow[]; forecastEnds: string; taDate: string }) {
  const [view, setView] = useState<View>("short");
  const [q, setQ] = useState("");
  const [limit, setLimit] = useState(PAGE);
  const [open, setOpen] = useState<string[] | null>(null);

  const likely = useMemo(() => rows.filter((r) => r.chance >= 0.5), [rows]);
  const views: { key: View; label: string; list: NeedRow[] }[] = useMemo(
    () => [
      { key: "short", label: t("Runs short in normal use", "Kurang pada pemakaian normal"), list: likely.filter((r) => r.likely6 > r.have) },
      { key: "bad", label: t("Short only in the bad case", "Kurang hanya pada skenario terburuk"), list: likely.filter((r) => r.bad6 > r.have && r.likely6 <= r.have) },
      { key: "ta", label: t("Short for the turnaround", "Kurang untuk turnaround"), list: rows.filter((r) => r.gap > 0) },
      { key: "new", label: t("No use on record", "Tanpa catatan pemakaian"), list: likely.filter((r) => r.no_history) },
      { key: "all", label: t("All expected parts", "Semua suku cadang yang diperkirakan"), list: rows },
    ],
    [rows, likely],
  );
  const words = q.trim().toLowerCase().split(/\s+/).filter(Boolean);
  const list = (views.find((v) => v.key === view)?.list ?? rows).filter((r) => {
    const hay = `${r.description} ${r.material_no}`.toLowerCase();
    return words.every((w) => hay.includes(w));
  });

  const groups = useMemo(() => {
    const rank = (r: NeedRow) => ({ bad: 0, warn: 1, ok: 2, none: 3 })[sev(r)];
    const m = new Map<string, NeedRow[]>();
    for (const r of list) m.set(r.category, [...(m.get(r.category) ?? []), r]);
    return Array.from(m, ([category, items]) => {
      const sorted = [...items].sort((a, b) => rank(a) - rank(b));
      const subs = new Map<string, NeedRow[]>();
      for (const r of sorted) subs.set(subtypeOf(r.description), [...(subs.get(subtypeOf(r.description)) ?? []), r]);
      const subtypes = subs.size > 1 ? Array.from(subs, ([name, its]) => ({ name, items: its })).sort((a, b) => b.items.filter(shortOf).length - a.items.filter(shortOf).length || b.items.length - a.items.length) : null;
      return { category, items: sorted, subtypes, score: items.filter((r) => sev(r) === "bad").length * 1000 + items.filter(shortOf).length };
    }).sort((a, b) => b.score - a.score || b.items.length - a.items.length);
  }, [list]);

  // The two most urgent groups start open, with their first sub-type; a search opens everything it touches.
  const first = groups.slice(0, 2).flatMap((g) => [g.category, ...(g.subtypes ? [`${g.category}/${g.subtypes[0].name}`] : [])]);
  const openSet = new Set(words.length ? groups.flatMap((g) => [g.category, ...(g.subtypes ?? []).map((s) => `${g.category}/${s.name}`)]) : open ?? first);
  const toggle = (k: string) => setOpen(() => (openSet.has(k) ? [...openSet].filter((x) => x !== k) : [...openSet, k]));

  return (
    <Panel className="overflow-hidden">
      <div className="flex flex-wrap items-center gap-2 px-5 pb-3 pt-4">
        <div className="no-scrollbar flex min-w-0 flex-1 gap-1 overflow-x-auto">
          {views.map((v) => (
            <button key={v.key} type="button" aria-pressed={view === v.key} onClick={() => { setView(v.key); setLimit(PAGE); setOpen(null); }} className={cn("h-8 shrink-0 whitespace-nowrap rounded-full px-3 text-[12.5px] transition-colors", view === v.key ? "bg-ink font-medium text-white" : "text-ink-2 hover:bg-ink/[0.05]")}>
              {v.label} <span className={cn("tabular-nums", view === v.key ? "text-white/70" : "text-ink-4")}>{num(v.list.length)}</span>
            </button>
          ))}
        </div>
        <label className="flex h-8 w-[200px] shrink-0 items-center gap-2 rounded-[10px] border border-line bg-panel px-2.5 text-[13px]">
          <Search aria-hidden className="h-4 w-4 shrink-0 text-ink-3" />
          <span className="sr-only">{t("Find a part in this list", "Cari suku cadang di daftar ini")}</span>
          <input value={q} onChange={(e) => { setQ(e.target.value); setLimit(PAGE); }} placeholder={t("Part name or number", "Nama atau nomor suku cadang")} className="min-w-0 flex-1 bg-transparent outline-none placeholder:text-ink-4" />
        </label>
      </div>
      <div className={cn("grid items-end gap-3 border-y border-line bg-panel-2 py-2 pl-5 pr-5 text-[12px] font-medium leading-snug text-ink-3", COLS)}>
        <span className="flex items-center gap-1">{t("Part", "Suku cadang")}<Hint>{t("Grouped by part type, then sub-type. Row colour: Red: too late, or a critical (A or B) part with nothing on the shelf. Orange: short, still time to order. Green: enough.", "Dikelompokkan menurut jenis suku cadang, lalu subjenisnya. Warna baris: merah berarti terlambat, atau suku cadang kritis (A atau B) yang raknya kosong; oranye berarti kurang, tetapi masih sempat dipesan; hijau berarti cukup.")}</Hint></span>
        <span>{t("We have", "Stok kita")}</span>
        <span className="flex items-center gap-1">{t(`Normal use to ${shortDate(forecastEnds)}`, `Pemakaian normal s.d. ${shortDate(forecastEnds)}`)}<Hint>{t(`Most likely use from today until ${shortDate(forecastEnds, true)}, the end of the 6-month forecast. The small number is the bad case.`, `Pemakaian yang paling mungkin dari hari ini sampai ${shortDate(forecastEnds, true)}, akhir prakiraan 6 bulan. Angka kecil adalah skenario terburuk.`)}</Hint></span>
        <span className="flex items-center gap-1">{t(`Needed by ${shortDate(taDate)}`, `Dibutuhkan s.d. ${shortDate(taDate)}`)}<Hint>{t(`For parts the last turnaround used: what the turnaround job used last time, plus normal use from today until ${shortDate(taDate, true)}.`, `Untuk suku cadang yang dipakai pada turnaround sebelumnya: pemakaian pekerjaan turnaround terakhir, ditambah pemakaian normal dari hari ini sampai ${shortDate(taDate, true)}.`)}</Hint></span>
        <span>{t("What to do", "Tindakan")}</span>
      </div>
      <ul className="m-0 list-none divide-y divide-line p-0">
        {groups.length === 0 && <li className="px-5 py-10 text-center text-[13.5px] text-ink-3">{t("No part matches. Clear the search or pick another list.", "Tidak ada suku cadang yang cocok. Hapus pencarian atau pilih daftar lain.")}</li>}
        {groups.slice(0, limit).map((g) => {
          const on = openSet.has(g.category);
          return (
            <li key={g.category}>
              <button type="button" aria-expanded={on} onClick={() => toggle(g.category)} className="flex w-full items-center gap-2.5 px-5 py-2.5 text-left transition-colors hover:bg-ink/[0.02]">
                <ChevronRight aria-hidden className={cn("h-4 w-4 shrink-0 text-ink-3 transition-transform duration-150", on && "rotate-90")} />
                <span className="min-w-0 flex-1 truncate text-[13.5px] font-semibold">{categoryName(g.category)} <span className="font-normal text-ink-3">· {num(g.items.length)} {t(g.items.length === 1 ? "part" : "parts", "suku cadang")}</span></span>
                <Counts items={g.items} />
              </button>
              {on && (
                <ul className="m-0 list-none divide-y divide-line border-t border-line bg-panel-2/40 p-0">
                  {g.subtypes
                    ? g.subtypes.map((st) => {
                        const k = `${g.category}/${st.name}`;
                        const sOn = openSet.has(k);
                        return (
                          <li key={k}>
                            <button type="button" aria-expanded={sOn} onClick={() => toggle(k)} className="flex w-full items-center gap-2 py-2 pl-11 pr-5 text-left transition-colors hover:bg-ink/[0.02]">
                              <ChevronRight aria-hidden className={cn("h-3.5 w-3.5 shrink-0 text-ink-3 transition-transform duration-150", sOn && "rotate-90")} />
                              <span className="min-w-0 flex-1 truncate text-[13px] font-medium">{subtypeName(st.name)} <span className="font-normal text-ink-3">· {num(st.items.length)}</span></span>
                              <Counts items={st.items} />
                            </button>
                            {sOn && (
                              <ul className="m-0 list-none divide-y divide-line border-t border-line p-0 [--bar:68px]">
                                {st.items.map((r) => <Row key={r.material_no} r={r} subtype={st.name} indent="pl-[68px]" />)}
                              </ul>
                            )}
                          </li>
                        );
                      })
                    : <li><ul className="m-0 list-none divide-y divide-line p-0 [--bar:44px]">{g.items.map((r) => <Row key={r.material_no} r={r} subtype={null} indent="pl-11" />)}</ul></li>}
                </ul>
              )}
            </li>
          );
        })}
      </ul>
      {groups.length > limit && (
        <button type="button" onClick={() => setLimit((l) => l + 20)} className="flex h-10 w-full items-center justify-center border-t border-line text-[13px] font-medium text-ink-2 transition-colors hover:bg-ink/[0.03]">
          {t(`Show more part types, ${num(groups.length - limit)} left`, `Tampilkan jenis suku cadang lainnya, ${num(groups.length - limit)} tersisa`)}
        </button>
      )}
    </Panel>
  );
}

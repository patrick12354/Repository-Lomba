"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { ArrowLeft, ArrowRight } from "lucide-react";
import { Boxes, CalendarClock, CircleAlert, Hourglass, ListTodo, Repeat, Sigma } from "@/components/icons";
import type { MachineView } from "@/lib/data";
import { type Machine, ZONE_LABEL } from "@/lib/machines";
import { cn, isTopCrit, partName, amount, qty, rp, shortDate, num, shortPartName, subtypeOf, subtypeName } from "@/lib/format";
import { MachineStage, type ZoneStat } from "./machine-stage";
import { CritRows, MetricCard, NeedleGauge, TickGauge } from "./deck";
import { OrderCalendar } from "./order-calendar";
import { Em, Panel, SevBar, sevOf } from "./ui";
import { ChevronRight } from "lucide-react";
import { Hint } from "./hint";
import type { TaPart } from "@/lib/data";
import { t } from "@/lib/i18n";

const taSev = (p: TaPart) => sevOf({ short: p.status !== "READY", late: p.status === "TOO_LATE", critical: p.criticality === "A" || p.criticality === "B", empty: p.stock <= 0 });

/** Categories drawn on each model. A category that is not drawn is listed under the stage. */
const DRAWN: Record<string, string[]> = {
  pump: ["IMPELLER", "BEARING", "O-RING", "GASKET", "STUDBOLT", "OIL", "GREASE", "TERMINAL", "FLANGE"],
  compressor: ["BEARING", "O-RING", "GASKET", "STUDBOLT", "OIL", "GREASE", "TERMINAL", "SEAL", "COUPLING", "FILTER ELEMENT"],
  turbine: ["BEARING", "O-RING", "GASKET", "STUDBOLT", "FILTER ELEMENT"],
  furnace: ["FIREBRICK", "CERAMIC FIBER", "ANCHOR", "CASTABLE", "PIPE", "VALVE", "ELBOW", "GASKET", "STUDBOLT", "SCREW"],
  exchanger: ["GASKET", "STUDBOLT", "FLANGE", "PIPE"],
};

export function MachineDetail({ machine, view, unit, query, hit }: { machine: Machine; view: MachineView; unit: string | null; query: { date?: string; scale?: string; shock?: string }; hit: number }) {
  const q = new URLSearchParams();
  if (query.date) q.set("date", query.date);
  if (query.scale) q.set("scale", query.scale);
  if (query.shock) q.set("shock", query.shock);
  const suffix = q.size ? `?${q}` : "";
  const board = `/todo?machine=${machine.slug}`;

  const zones = useMemo<ZoneStat[]>(() => {
    const map = new Map<string, ZoneStat>();
    for (const p of view.parts) {
      const z = map.get(p.category) ?? { key: p.category, short: 0, total: 0 };
      z.total++;
      if (p.status !== "READY") z.short++;
      map.set(p.category, z);
    }
    return Array.from(map.values());
  }, [view.parts]);
  const drawn = zones.filter((z) => DRAWN[machine.slug]?.includes(z.key));
  const others = zones.filter((z) => !DRAWN[machine.slug]?.includes(z.key) && z.short > 0);

  const firstZone = [...drawn].sort((a, b) => b.short - a.short)[0]?.key ?? null;
  const [selected, setSelected] = useState<string | null>(firstZone);
  const selectedParts = useMemo(() => view.parts.filter((p) => p.category === selected), [view.parts, selected]);

  const short = view.total - view.counts.READY;
  const pct = Math.round((view.counts.READY / Math.max(1, view.total)) * 100);
  const ab = view.parts.filter((p) => isTopCrit(p.criticality));
  const abReady = ab.filter((p) => p.status === "READY").length;
  const abPct = Math.round((abReady / Math.max(1, ab.length)) * 100);
  const soon = view.counts.ORDER_NOW + view.counts.PLAN;
  const gapText = rp(view.gapValue);

  return (
    <div className="space-y-6">
      <header className="flex items-end justify-between gap-6">
        <div className="min-w-0">
          <Link href={`/${suffix}`} className="inline-flex items-center gap-1 text-[13px] text-ink-3 transition-colors hover:text-ink">
            <ArrowLeft aria-hidden className="h-3.5 w-3.5" /> {t("Plant map", "Peta kilang")}
          </Link>
          <h1 className="m-0 mt-1 text-[28px] font-semibold leading-[1.15] tracking-[-0.02em]">
            {machine.plural}
            {unit ? ` · ${unit}` : ""}
          </h1>
          <p className="m-0 mt-1.5 text-[14px] leading-[1.55] text-ink-2">
            {t(
              <><Em tone="act">{short}</Em> of the {view.total} parts these machines used last turnaround will not have enough stock by the turnaround. Click a numbered dot on the machine to see which ones.</>,
              <><Em tone="act">{short}</Em> dari {view.total} suku cadang yang dipakai mesin-mesin ini pada turnaround sebelumnya tidak akan cukup stoknya saat turnaround. Klik titik bernomor pada mesin untuk melihat yang mana saja.</>,
            )}
          </p>
        </div>
        {machine.slug === "furnace" && (
          <div className="flex max-w-[60%] flex-wrap justify-end gap-1" aria-label={t("Pick a furnace", "Pilih tungku")}>
            <Link href={`/plant/furnace${suffix}`} className={cn("rounded-[8px] border px-2 py-1 text-[12px] font-medium transition-colors", !unit ? "border-ink bg-ink text-white" : "border-line bg-panel text-ink-2 hover:border-line-2")}>{t("All 12", "Semua 12")}</Link>
            {[...view.units].filter((u) => /^BF-1(0[1-9]|1[0-2])$/.test(u.equipment)).sort((a, b) => a.equipment.localeCompare(b.equipment)).map((u) => {
              const nq = new URLSearchParams(q);
              nq.set("unit", u.equipment);
              return (
                <Link key={u.equipment} href={`/plant/furnace?${nq}`} title={t(`${u.short} of ${u.total} parts short`, `${u.short} dari ${u.total} suku cadang kurang`)} className={cn("rounded-[8px] border px-2 py-1 text-[12px] tabular-nums transition-colors", unit === u.equipment ? "border-ink bg-ink font-medium text-white" : "border-line bg-panel text-ink-2 hover:border-line-2")}>
                  {u.equipment.replace("BF-", "")}
                </Link>
              );
            })}
          </div>
        )}
      </header>

      <div className="grid grid-cols-[minmax(0,1fr)_320px] gap-6">
        <section className="relative h-[calc(100dvh-196px)] min-h-[520px] overflow-hidden rounded-[20px] border border-line bg-[#eee9e3]">
          <MachineStage key={machine.slug} slug={machine.slug} zones={drawn} selected={selected} onSelect={setSelected} className="absolute inset-0" />
          {others.length > 0 && (
            <div className="absolute bottom-3 right-3 z-10 max-w-[260px] rounded-[10px] bg-white/95 px-3 py-2 text-[12px] leading-snug text-ink-2 shadow-card">
              <b className="font-medium text-ink">{t("Not drawn: ", "Tidak digambar: ")}</b>
              {others.map((o) => `${ZONE_LABEL[o.key] ?? o.key.toLowerCase()} (${o.short})`).join(", ")}
            </div>
          )}
        </section>

        <aside className="flex h-[calc(100dvh-196px)] min-h-[520px] flex-col gap-4">
          <Panel className="shrink-0 p-4">
            <div className="flex items-baseline justify-between">
              <h2 className="m-0 text-[14px] font-semibold">{t("Parts ready for the turnaround", "Suku cadang siap untuk turnaround")}</h2>
              <span className="shrink-0 text-[12px] tabular-nums text-ink-3">{t(`${view.daysToTa} days left`, `${view.daysToTa} hari lagi`)}</span>
            </div>
            <div className="mx-auto mt-1 max-w-[230px]">
              <TickGauge value={pct} caption={t(`${view.counts.READY} of ${view.total} ready`, `${view.counts.READY} dari ${view.total} siap`)} />
            </div>
          </Panel>
          <Panel className="flex min-h-0 flex-1 flex-col">
            {selected ? (
              <>
                <div className="flex shrink-0 items-baseline justify-between gap-3 border-b border-line px-4 py-3">
                  <h2 className="m-0 flex min-w-0 items-center gap-1 text-[14px] font-semibold"><span className="truncate">{ZONE_LABEL[selected] ?? selected}</span><Hint>{t("The parts of this type on this machine, grouped by sub-type. Row colour: Red: too late, or a critical (A or B) part with nothing on the shelf. Orange: short, still time to order. Green: enough. \"Order by\" is the last safe day to place the order, not the delivery date.", "Suku cadang jenis ini pada mesin ini, dikelompokkan menurut subjenisnya. Warna baris: merah berarti terlambat, atau suku cadang kritis (A atau B) yang raknya kosong; oranye berarti kurang, tetapi masih sempat dipesan; hijau berarti cukup. \"Pesan paling lambat\" adalah hari terakhir yang aman untuk memesan, bukan tanggal barang tiba.")}</Hint></h2>
                  <span className="shrink-0 text-[12px] tabular-nums text-ink-3">
                    <b className="font-semibold text-act-ink">{selectedParts.filter((p) => p.status !== "READY").length}</b> {t(`of ${selectedParts.length} short`, `dari ${selectedParts.length} kurang`)}
                  </span>
                </div>
                <PartGroups key={selected} parts={selectedParts} />
              </>
            ) : (
              <div className="grid flex-1 place-items-center px-6 text-center text-[13px] text-ink-3">{t("Click a numbered dot on the machine to list its parts.", "Klik titik bernomor pada mesin untuk menampilkan daftar suku cadangnya.")}</div>
            )}
          </Panel>
        </aside>
      </div>

      <section className="grid grid-cols-[300px_minmax(0,1fr)] gap-4">
        <Panel className="flex flex-col p-5">
          <h2 className="m-0 text-[14px] font-semibold">{t("Critical parts ready (A and B)", "Suku cadang kritis siap (A dan B)")}</h2>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-[40px] font-semibold leading-none tracking-[-0.02em] tabular-nums">{abPct}%</span>
            <span className="text-[13px] text-ink-3">{ab.length - abReady} {t("short", "kurang")}</span>
          </div>
          <div className="mx-auto mt-2 w-full max-w-[220px]"><NeedleGauge value={abPct} /></div>
          <div className="mt-auto pt-2"><CritRows byCrit={view.byCrit} /></div>
        </Panel>
        <div className="grid auto-rows-fr grid-cols-3 gap-3">
          <MetricCard glow icon={CircleAlert} label={t("Too late for a normal order", "Terlambat untuk pemesanan biasa")} sub={t("Their last safe order day has passed, so rush them", "Batas aman pemesanannya sudah lewat, jadi percepat pesanannya")} value={view.counts.TOO_LATE} href={`${board}&urgency=late`} />
          <MetricCard icon={CalendarClock} label={t("Order within 30 days", "Pesan dalam 30 hari")} sub={t("Their last safe order day is close", "Batas aman pemesanannya sudah dekat")} value={soon} href={`${board}&urgency=month`} />
          <MetricCard icon={Hourglass} label={t("Order later", "Pesan nanti")} sub={t("There is still time, the dates are set", "Masih ada waktu, tanggalnya sudah ditetapkan")} value={view.counts.LATER} href={board} />
          <MetricCard icon={Boxes} label={t("Max limit too low", "Batas Max terlalu rendah")} sub={t(`One turnaround used more than Max. ${view.noMax} more have no Max at all`, `Satu turnaround memakai lebih banyak daripada Max. ${view.noMax} lainnya sama sekali tidak memiliki Max`)} value={view.belowMaxStocked} />
          <MetricCard icon={Repeat} label={t("Can use a duplicate part", "Bisa memakai suku cadang kembar")} sub={t("Same part under another number has extra stock", "Suku cadang yang sama dengan nomor lain memiliki kelebihan stok")} value={view.twinCount} href={`${board}&kind=twin`} />
          <MetricCard icon={Sigma} label={t("To buy", "Perlu dibeli")} sub={t(`Parts with a known price. The forecast picks the right part ${hit} times in 100`, `Suku cadang yang harganya diketahui. Prakiraan memilih suku cadang yang tepat ${hit} kali dari 100`)} value={gapText.replace(/^Rp\s*/, "").replace(/\s*[A-Za-z]+$/, "")} unit={/[A-Za-z]+$/.exec(gapText)?.[0]} />
        </div>
      </section>

      <OrderCalendar parts={view.parts} asOf={view.asOf} taDate={view.taDate} />
      <Link href={board} className="flex items-center gap-3 rounded-[16px] border border-line bg-panel px-5 py-4 shadow-card transition-colors hover:border-line-2">
        <span className="grid h-9 w-9 place-items-center rounded-[10px] bg-panel-2 text-ink-2"><ListTodo aria-hidden className="h-[18px] w-[18px]" /></span>
        <span className="min-w-0 flex-1">
          <span className="block text-[14px] font-semibold">{t(`See the ${short} open parts on the To do board`, `Lihat ${short} suku cadang yang masih terbuka di papan Tugas`)}</span>
          <span className="block text-[12.5px] text-ink-3">{t(`Filtered to ${machine.plural.toLowerCase()}. Approve, reject and track orders there.`, `Disaring untuk ${machine.plural.toLowerCase()}. Setujui, tolak, dan pantau pesanannya di sana.`)}</span>
        </span>
        <ArrowRight aria-hidden className="h-4 w-4 text-ink-3" />
      </Link>
    </div>
  );
}

function PartRow({ p, sub }: { p: TaPart; sub: string | null }) {
  return (
    <li>
      <Link href={`/parts/${p.material_no}`} title={`${partName(p.description)} · ${t("criticality", "kekritisan")} ${p.criticality}`} className={cn("relative block py-2.5 pr-4 transition-colors hover:bg-ink/[0.03]", sub ? "pl-9" : "pl-4")}>
        <SevBar sev={taSev(p)} />
        <span className="relative block truncate text-[13px] font-medium">{shortPartName(p.description, sub)}</span>
        <span className="relative mt-0.5 flex justify-between gap-2 text-[12px] tabular-nums">
          <span className="text-ink-3">{t(`Have ${qty(p.stock, p.unit)} of ${amount(p.need_total, p.unit)}`, `Ada ${qty(p.stock, p.unit)} dari ${amount(p.need_total, p.unit)}`)}</span>
          <span className={cn(p.status === "TOO_LATE" ? "text-act-ink" : p.status === "READY" ? "text-ready-ink" : "text-plan-ink")}>{p.status === "TOO_LATE" ? t(`Too late, ${Math.round(p.lt_p90)} days to arrive`, `Terlambat, ${Math.round(p.lt_p90)} hari sampai tiba`) : p.status === "READY" ? t("Ready", "Siap") : t(`Order by ${shortDate(p.order_by)}`, `Pesan s.d. ${shortDate(p.order_by)}`)}</span>
        </span>
      </Link>
    </li>
  );
}

/** Sheet, ring, spiral wound: one drop-down per sub-type when the type has more than one. */
function PartGroups({ parts }: { parts: TaPart[] }) {
  const rank = (p: TaPart) => ({ bad: 0, warn: 1, ok: 2, none: 3 })[taSev(p)];
  const sorted = [...parts].sort((a, b) => rank(a) - rank(b));
  const subs = new Map<string, TaPart[]>();
  for (const p of sorted) subs.set(subtypeOf(p.description), [...(subs.get(subtypeOf(p.description)) ?? []), p]);
  const groups = Array.from(subs, ([name, items]) => ({ name, items, short: items.filter((p) => p.status !== "READY").length })).sort((a, b) => b.short - a.short || b.items.length - a.items.length);
  const [open, setOpen] = useState<string[]>(groups.slice(0, 1).map((g) => g.name));
  if (groups.length < 2) return <ul className="m-0 min-h-0 flex-1 list-none divide-y divide-line overflow-y-auto p-0">{sorted.map((p) => <PartRow key={p.material_no} p={p} sub={null} />)}</ul>;
  return (
    <ul className="m-0 min-h-0 flex-1 list-none divide-y divide-line overflow-y-auto p-0">
      {groups.map((g) => {
        const on = open.includes(g.name);
        return (
          <li key={g.name}>
            <button type="button" aria-expanded={on} onClick={() => setOpen((o) => (on ? o.filter((x) => x !== g.name) : [...o, g.name]))} className="flex w-full items-center gap-2 px-4 py-2 text-left transition-colors hover:bg-ink/[0.03]">
              <ChevronRight aria-hidden className={cn("h-3.5 w-3.5 shrink-0 text-ink-3 transition-transform duration-150", on && "rotate-90")} />
              <span className="min-w-0 flex-1 truncate text-[13px] font-semibold">{subtypeName(g.name)} <span className="font-normal text-ink-3">· {num(g.items.length)}</span></span>
              {g.short > 0 ? <span className="shrink-0 rounded-[6px] bg-act-soft px-1.5 py-0.5 text-[11.5px] font-medium tabular-nums text-act-ink">{num(g.short)} {t("short", "kurang")}</span> : <span className="shrink-0 rounded-[6px] bg-ready-soft px-1.5 py-0.5 text-[11.5px] font-medium text-ready-ink">{t("ready", "siap")}</span>}
            </button>
            {on && <ul className="m-0 list-none divide-y divide-line border-t border-line p-0">{g.items.map((p) => <PartRow key={p.material_no} p={p} sub={g.name} />)}</ul>}
          </li>
        );
      })}
    </ul>
  );
}

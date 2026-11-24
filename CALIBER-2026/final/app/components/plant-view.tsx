"use client";

import { useEffect, useMemo, useRef, useState, useTransition } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowRight, Minus, Plus } from "lucide-react";
import { CalendarDays, Cog, Compass, Droplet, Flame, ListTodo, Repeat, RotateCcw, RotateCw, Truck, Wind, type LucideIcon } from "@/components/icons";
import type { Readiness, TaPart } from "@/lib/data";
import { MACHINES, type MachineSlug, machineByPlural, machineBySlug } from "@/lib/machines";
import { amount, cn, isTopCrit, num, partName, qty, rp, shortDate, type Crit } from "@/lib/format";
import { createPlant, type PlantHandle } from "./three/plant-scene";
import { OrderCalendar } from "./order-calendar";
import { Em, Panel, SevBar, sevOf } from "./ui";
import { AiBrief } from "./ai-brief";
import { Hint } from "./hint";
import { isId, t } from "@/lib/i18n";

const sizes = () => [
  { v: 0.7, label: t("Smaller", "Lebih kecil") },
  { v: 1, label: t("Same as last", "Sama seperti sebelumnya") },
  { v: 1.3, label: t("Bigger", "Lebih besar") },
];

const ICON: Record<MachineSlug, LucideIcon> = { furnace: Flame, compressor: Wind, pump: Droplet, turbine: Cog, exchanger: Repeat };

type ProofRow = { material_no: number; description: string; unit: string; criticality: Crit; ta_qty_last: number; max_cur: number; stock: number };
type Month = { month: string; parts: number; parts_ta: number; lines: number };
const MON_EN = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const MON_ID = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"];
const mon = () => (isId() ? MON_ID : MON_EN);

export function PlantView({ initial, proof, facts, months, overValue, pctAbove }: { initial: Readiness; proof: ProofRow[]; facts: { stocked: number; stocked_ab: number; no_max: number }; months: Month[]; overValue: number; pctAbove: number }) {
  const [data, setData] = useState(initial);
  const [date, setDate] = useState(initial.taDate);
  const [scale, setScale] = useState(initial.scale);
  const [shock, setShock] = useState(0);
  const [pending, start] = useTransition();
  const router = useRouter();

  const load = (d: string, s: number, delay = shock) => {
    start(async () => {
      const res = await fetch(`/api/ta-readiness?date=${d}&scale=${s}&shock=${delay}`);
      if (res.ok) setData(await res.json());
    });
  };

  const ab = data.parts.filter((p) => isTopCrit(p.criticality));
  const abReady = ab.filter((p) => p.status === "READY").length;
  const abPct = Math.round((abReady / Math.max(1, ab.length)) * 100);
  const abCanPct = Math.round((ab.filter((p) => p.status !== "TOO_LATE").length / Math.max(1, ab.length)) * 100);
  const late = data.counts.TOO_LATE;
  const soon = data.counts.ORDER_NOW + data.counts.PLAN;
  const short = data.total - data.counts.READY;
  const simulated = date !== initial.taDate || scale !== 1 || shock > 0;

  const query = useMemo(() => {
    const q = new URLSearchParams();
    if (date !== initial.taDate) q.set("date", date);
    if (scale !== 1) q.set("scale", String(scale));
    if (shock > 0) q.set("shock", String(shock));
    return q;
  }, [date, scale, shock, initial.taDate]);

  const classes = useMemo(() => {
    const out: Partial<Record<MachineSlug, { short: number; total: number }>> = {};
    for (const c of data.classes) {
      const m = machineByPlural(c.cls);
      if (m) out[m.slug] = { short: c.short, total: c.total };
    }
    return out;
  }, [data.classes]);

  /* the 3D site is rebuilt only when the numbers painted on it change */
  const canvas = useRef<HTMLCanvasElement>(null);
  const layer = useRef<HTMLDivElement>(null);
  const tip = useRef<HTMLDivElement>(null);
  const handle = useRef<PlantHandle | null>(null);
  const [hover, setHover] = useState<{ slug: MachineSlug; unit?: string } | null>(null);
  const [failed, setFailed] = useState(false);
  const [ready, setReady] = useState(false);
  const queryRef = useRef(query);
  useEffect(() => {
    queryRef.current = query;
  }, [query]);
  const paint = useMemo(() => JSON.stringify({ f: data.furnaces, c: classes }), [data.furnaces, classes]);

  useEffect(() => {
    const cv = canvas.current;
    if (!cv) return;
    const parsed = JSON.parse(paint) as { f: Readiness["furnaces"]; c: typeof classes };
    const go = (slug: MachineSlug, unit?: string) => {
      const q = new URLSearchParams(queryRef.current);
      if (unit) q.set("unit", unit);
      const url = `/plant/${slug}${q.size ? `?${q}` : ""}`;
      router.prefetch(url);
      if (handle.current) handle.current.flyTo(slug, () => router.push(url));
      else router.push(url);
    };
    let h: PlantHandle | null = null;
    let dead = false;
    const place = () => {
      const el = layer.current;
      if (!el || !h) return;
      for (const b of Array.from(el.children) as HTMLElement[]) {
        const p = h.project(b.dataset.anchor ?? "");
        if (!p) continue;
        const inside = p.x > 8 && p.y > 8 && p.x < h.pipeline.size.w - 8 && p.y < h.pipeline.size.h - 8;
        b.style.transform = `translate3d(${p.x.toFixed(1)}px,${p.y.toFixed(1)}px,0) translate(-50%,-50%)`;
        b.style.visibility = inside ? "visible" : "hidden";
      }
    };
    /* let the page paint first: building the site takes a moment */
    const timer = window.setTimeout(() => {
      if (dead) return;
      try {
        h = createPlant(cv, { furnaces: parsed.f, classes: parsed.c }, {
          onHover: (hit, x, y) => {
            setHover((cur) => (cur?.slug === hit?.slug && cur?.unit === hit?.unit ? cur : hit));
            if (tip.current) tip.current.style.transform = `translate(${x + 16}px,${y + 12}px)`;
          },
          onPick: go,
          onCamera: place,
          onReady: () => setReady(true),
        });
        handle.current = h;
        place();
      } catch {
        setFailed(true);
      }
    }, 30);
    return () => {
      dead = true;
      window.clearTimeout(timer);
      handle.current = null;
      h?.dispose();
    };
  }, [paint, router]);

  const openMachine = (slug: MachineSlug) => {
    const url = `/plant/${slug}${query.size ? `?${query}` : ""}`;
    router.prefetch(url);
    if (handle.current) handle.current.flyTo(slug, () => router.push(url));
    else router.push(url);
  };

  const hoverFurnace = hover?.unit ? data.furnaces.find((f) => f.equipment === hover.unit) : null;
  const hoverClass = hover ? classes[hover.slug] : null;

  return (
    <div className="space-y-6">
      <header>
        <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-2">
        <h1 className="m-0 min-w-0 text-[28px] font-semibold leading-[1.15] tracking-[-0.02em]">{t("Ready for the next turnaround?", "Siapkah kita untuk turnaround berikutnya?")}</h1>
        <div data-tour="p-controls" className={cn("flex flex-wrap items-center gap-2 transition-opacity", pending && "opacity-60")}>
          <AiBrief page="plant" />
          <label className="inline-flex h-9 items-center gap-2 rounded-[10px] border border-line bg-panel px-2.5 text-[13px]">
            <CalendarDays aria-hidden className="h-4 w-4 text-ink-3" />
            <span className="whitespace-nowrap text-ink-2">{t("Turnaround starts", "Turnaround dimulai")}</span>
            <input
              type="date"
              value={date}
              min={data.asOf}
              onChange={(e) => {
                setDate(e.target.value);
                if (e.target.value) load(e.target.value, scale);
              }}
              className="bg-transparent font-medium outline-none"
            />
          </label>
          <label data-tour="p-shock" className="inline-flex h-9 items-center gap-2 rounded-[10px] border border-line bg-panel px-2.5 text-[13px]" title={t("What if every supplier takes this much longer?", "Bagaimana jika setiap pemasok terlambat selama ini?")}>
            <Truck aria-hidden className="h-4 w-4 text-ink-3" />
            <span className="whitespace-nowrap text-ink-2">{t("Supplier delay", "Keterlambatan pemasok")}</span>
            <input
              type="range"
              min={0}
              max={90}
              step={15}
              value={shock}
              onChange={(e) => setShock(Number(e.target.value))}
              onPointerUp={(e) => load(date, scale, Number(e.currentTarget.value))}
              onKeyUp={(e) => load(date, scale, Number(e.currentTarget.value))}
              className="h-1.5 w-16 cursor-pointer accent-[var(--accent)]"
              aria-valuetext={t(`${shock} days`, `${shock} hari`)}
            />
            <b className="w-[58px] text-right font-semibold tabular-nums">+{shock} {t("days", "hari")}</b>
          </label>
          <div role="radiogroup" aria-label={t("Turnaround size", "Ukuran turnaround")} className="inline-flex h-9 items-center gap-0.5 rounded-[10px] border border-line bg-panel p-[3px]">
            <span className="px-1.5 text-[13px] text-ink-2">{t("Size", "Ukuran")}</span>
            {sizes().map((s) => (
              <button
                key={s.v}
                type="button"
                role="radio"
                aria-checked={scale === s.v}
                title={t(`${s.v}× the last turnaround`, `${num(s.v, 1)}× turnaround sebelumnya`)}
                onClick={() => {
                  setScale(s.v);
                  load(date, s.v);
                }}
                className={cn("h-full rounded-[7px] px-2.5 text-[13px] transition-colors duration-150", scale === s.v ? "bg-ink font-medium text-white" : "text-ink-2 hover:bg-ink/[0.05]")}
              >
                {s.label}
              </button>
            ))}
          </div>
        </div>
        </div>
        <p className="m-0 mt-1 text-[14px] leading-[1.55] text-ink-2">
          {t(
            <>
              <Em tone={abPct < 80 ? "act" : "ready"}>{abPct}% of critical parts will be ready</Em> for the turnaround on {shortDate(data.taDate, true)} if we order nothing. On-time orders bring it to <Em>{abCanPct}%</Em>. <Em tone="act">{late} parts are already too late.</Em>{" "}
              <Hint>A turnaround is the plant&apos;s big planned shutdown. We assume it uses the same parts as the last one, plus normal use until then. Critical means criticality A or B. &quot;Too late&quot; means the last safe order day has passed, so a normal order arrives too late. {soon} more must be ordered within 30 days.</Hint>
            </>,
            <>
              <Em tone={abPct < 80 ? "act" : "ready"}>{abPct}% suku cadang kritis akan siap</Em> untuk turnaround pada {shortDate(data.taDate, true)} jika kita tidak memesan apa pun. Pemesanan tepat waktu menaikkannya menjadi <Em>{abCanPct}%</Em>. <Em tone="act">{late} suku cadang sudah terlambat.</Em>{" "}
              <Hint>Turnaround adalah penghentian besar kilang yang terencana. Kami mengasumsikan turnaround ini memakai suku cadang yang sama dengan turnaround sebelumnya, ditambah pemakaian normal sampai saat itu. Kritis berarti kekritisan A atau B. &quot;Terlambat&quot; berarti batas aman pemesanan sudah lewat, sehingga pesanan biasa akan tiba terlambat. {soon} lainnya harus dipesan dalam 30 hari.</Hint>
            </>,
          )}
        </p>
        {simulated && (
          <p className="m-0 mt-2 inline-flex items-center gap-2 rounded-[10px] bg-plan-soft px-3 py-1.5 text-[12.5px] text-plan-ink">
            {t("Simulation: these numbers use your date, size or delay. Part pages and To do still use the normal plan.", "Simulasi: angka-angka ini memakai tanggal, ukuran, atau keterlambatan pilihan Anda. Halaman suku cadang dan Tugas tetap memakai rencana normal.")}
            <button type="button" onClick={() => { setDate(initial.taDate); setScale(1); setShock(0); load(initial.taDate, 1, 0); }} className="font-medium underline underline-offset-2">{t("Reset", "Atur ulang")}</button>
          </p>
        )}
      </header>

      <section data-tour="p-map" className="relative h-[calc(100dvh-236px)] min-h-[520px] overflow-hidden rounded-[20px] border border-line bg-[#a9c98d]">
        <canvas ref={canvas} tabIndex={0} className={cn("absolute inset-0 block h-full w-full outline-none", ready ? "opacity-100" : "opacity-0")} aria-label={t("3D model of the plant. Drag to move, scroll to zoom, right-drag to turn, click a unit to open it. Arrow keys move the view.", "Model 3D kilang. Seret untuk menggeser, gulir untuk memperbesar, seret dengan klik kanan untuk memutar, klik unit untuk membukanya. Tombol panah menggeser tampilan.")} />
        {failed && <p className="absolute inset-x-0 top-1/3 m-0 text-center text-[14px] text-ink">{t("3D needs WebGL, which this browser has turned off.", "Tampilan 3D membutuhkan WebGL, yang dimatikan di peramban ini.")}</p>}

        <div ref={layer} className={cn("pointer-events-none absolute inset-0 overflow-hidden", ready ? "opacity-100" : "opacity-0")}>
          {MACHINES.map((m) => {
            const c = classes[m.slug];
            if (!c) return null;
            const Icon = ICON[m.slug];
            return (
              <button
                key={m.slug}
                type="button"
                data-anchor={m.slug}
                onClick={() => openMachine(m.slug)}
                aria-label={t(`${m.plural}: ${c.short} of ${c.total} parts short. Open`, `${m.plural}: ${c.short} dari ${c.total} suku cadang kurang. Buka`)}
                className="pointer-events-auto absolute left-0 top-0 flex h-9 items-center gap-2 whitespace-nowrap rounded-full bg-white pl-1.5 pr-3 text-[13px] shadow-float transition-colors duration-150 will-change-transform hover:bg-ink hover:text-white"
              >
                <span className="grid h-6 w-6 place-items-center rounded-full bg-accent-soft">
                  <Icon aria-hidden className="h-3.5 w-3.5" />
                </span>
                <span className="font-medium">{m.plural}</span>
                <span className="tabular-nums"><b className="font-semibold">{c.short}</b> <span className="text-[12px] opacity-70">{t(`of ${c.total} parts short`, `dari ${c.total} suku cadang kurang`)}</span></span>
              </button>
            );
          })}
        </div>

        <div ref={tip} className={cn("pointer-events-none absolute left-0 top-0 z-20 rounded-[10px] bg-ink px-3 py-2 text-[12.5px] text-white shadow-float", hover ? "visible" : "invisible")}>
          {hover && (
            <>
              <b className="font-semibold">{hover.unit ?? machineBySlug(hover.slug)?.plural}</b>
              <div className="text-white/75">{hoverFurnace ? t(`${hoverFurnace.short} of ${hoverFurnace.total} parts short`, `${hoverFurnace.short} dari ${hoverFurnace.total} suku cadang kurang`) : hoverClass ? t(`${hoverClass.short} of ${hoverClass.total} parts short`, `${hoverClass.short} dari ${hoverClass.total} suku cadang kurang`) : ""} · {t("click to open", "klik untuk membuka")}</div>
            </>
          )}
        </div>

        {/* legend */}
        <div className="absolute left-3 top-3 z-10 w-[190px] rounded-[12px] bg-white/95 px-3 py-2.5 text-[12px] shadow-card">
          <div className="font-medium">{t("Parts short for the turnaround", "Suku cadang kurang untuk turnaround")}</div>
          <div className="my-1.5 h-1.5 rounded-full" style={{ background: "linear-gradient(90deg,#66b256,#a8cc4a,#f6ca34,#f28a2c,#e2422a)" }} />
          <div className="flex justify-between text-[11px] text-ink-3"><span>{t("Fewer", "Sedikit")}</span><span>{t("More", "Banyak")}</span></div>
        </div>

        {/* map controls */}
        <div className="absolute right-3 top-3 z-10 flex flex-col overflow-hidden rounded-[12px] bg-white/95 shadow-card">
          <MapBtn label={t("Zoom in", "Perbesar")} icon={Plus} onClick={() => handle.current?.zoomBy(0.8)} />
          <MapBtn label={t("Zoom out", "Perkecil")} icon={Minus} onClick={() => handle.current?.zoomBy(1.25)} />
          <MapBtn label={t("Turn left", "Putar ke kiri")} icon={RotateCcw} onClick={() => handle.current?.turnBy(-Math.PI / 6)} />
          <MapBtn label={t("Turn right", "Putar ke kanan")} icon={RotateCw} onClick={() => handle.current?.turnBy(Math.PI / 6)} />
          <MapBtn label={t("Reset the view", "Kembalikan tampilan")} icon={Compass} onClick={() => handle.current?.reset()} />
        </div>
        <div className="absolute bottom-3 left-3 z-10 rounded-full bg-white/95 px-3 py-1.5 text-[12px] text-ink-2 shadow-card">
          {t("Drag to move · Scroll to zoom · Right-drag to turn · Click a machine to open it · The drawing is a sketch, the counts are real", "Seret untuk menggeser · Gulir untuk memperbesar · Seret klik kanan untuk memutar · Klik mesin untuk membukanya · Gambarnya hanya sketsa, angkanya nyata")}
        </div>
      </section>

      <FirstFive parts={data.parts} />

      <div className="grid grid-cols-[minmax(0,1fr)_minmax(0,1.35fr)_minmax(0,1.1fr)] gap-6">
        <ReadyCard abPct={abPct} abCanPct={abCanPct} abReady={abReady} abTotal={ab.length} short={short} late={late} gap={data.gapValue} gapPriced={data.parts.filter((p) => p.gap > 0 && p.gap_value != null).length} days={data.daysToTa} asOf={data.asOf} />
        <MonthsCard months={months} />
        <MaxCard proof={proof} facts={facts} overValue={overValue} pctAbove={pctAbove} />
      </div>

      <OrderCalendar parts={data.parts} asOf={data.asOf} taDate={data.taDate} />
      <Link href="/todo?view=urgent" className="flex items-center gap-3 rounded-[16px] border border-line bg-panel px-5 py-4 shadow-card transition-colors hover:border-line-2">
        <span className="grid h-9 w-9 place-items-center rounded-[10px] bg-panel-2 text-ink-2"><ListTodo aria-hidden className="h-[18px] w-[18px]" /></span>
        <span className="min-w-0 flex-1">
          <span className="block text-[14px] font-semibold">{t("Ready to act? Every part above is a task on the To do board", "Siap bertindak? Setiap suku cadang di atas adalah tugas di papan Tugas")}</span>
          <span className="block text-[12.5px] text-ink-3">{t("Approve, reject and track the orders there. It opens on the urgent ones.", "Setujui, tolak, dan pantau pesanannya di sana. Papan akan terbuka pada tugas yang mendesak.")}</span>
        </span>
        <ArrowRight aria-hidden className="h-4 w-4 text-ink-3" />
      </Link>
    </div>
  );
}

/** The five parts to deal with first, so the map always ends in something to do. */
function FirstFive({ parts }: { parts: TaPart[] }) {
  const top = parts.filter((p) => p.status !== "READY").slice(0, 5);
  if (!top.length) return null;
  return (
    <Panel className="overflow-hidden">
      <div className="flex items-baseline justify-between gap-3 px-5 pb-2 pt-4">
        <h2 className="m-0 text-[14px] font-semibold">{t("Deal with these first", "Tangani ini lebih dulu")}</h2>
        <Hint>{t("Row colour: Red: too late, or a critical (A or B) part with nothing on the shelf. Orange: short, still time to order. Green: enough.", "Warna baris: merah berarti terlambat, atau suku cadang kritis (A atau B) yang raknya kosong; oranye berarti kurang, tetapi masih sempat dipesan; hijau berarti cukup.")}</Hint>
      </div>
      <ul className="m-0 list-none divide-y divide-line border-t border-line p-0">
        {top.map((p) => (
          <li key={p.material_no}>
            <Link href={`/parts/${p.material_no}`} className="relative grid grid-cols-[minmax(0,2fr)_minmax(0,1.2fr)_minmax(0,1.3fr)_16px] items-center gap-3 px-5 py-2.5 text-[12.5px] tabular-nums transition-colors hover:bg-ink/[0.02]">
              <SevBar sev={sevOf({ short: true, late: p.status === "TOO_LATE", critical: p.criticality === "A" || p.criticality === "B", empty: p.stock <= 0 })} className="left-2" /><span className="flex min-w-0 items-center gap-2.5"><span className="truncate text-[13px] font-medium">{partName(p.description)}</span></span>
              <span className="text-ink-2">{t(`Have ${qty(p.stock, p.unit)}, need ${amount(p.need_total, p.unit)}`, `Ada ${qty(p.stock, p.unit)}, butuh ${amount(p.need_total, p.unit)}`)}</span>
              <span className={p.status === "TOO_LATE" ? "font-medium text-act-ink" : "font-medium text-plan-ink"}>{p.status === "TOO_LATE" ? t(`Rush: delivery can take ${Math.round(p.lt_p90)} days`, `Percepat: pengiriman bisa ${Math.round(p.lt_p90)} hari`) : t(`Order by ${shortDate(p.order_by, true)}`, `Pesan paling lambat ${shortDate(p.order_by, true)}`)}</span>
              <ArrowRight aria-hidden className="h-4 w-4 text-ink-4" />
            </Link>
          </li>
        ))}
      </ul>
    </Panel>
  );
}

function MapBtn({ label, icon: Icon, onClick }: { label: string; icon: LucideIcon; onClick: () => void }) {
  return (
    <button type="button" aria-label={label} title={label} onClick={onClick} className="grid h-9 w-9 place-items-center border-b border-line text-ink-2 transition-colors last:border-b-0 hover:bg-ink/[0.05] hover:text-ink">
      <Icon aria-hidden className="h-4 w-4" />
    </button>
  );
}

function ReadyCard({ abPct, abCanPct, abReady, abTotal, short, late, gap, gapPriced, days, asOf }: { abPct: number; abCanPct: number; abReady: number; abTotal: number; short: number; late: number; gap: number; gapPriced: number; days: number; asOf: string }) {
  return (
    <Panel className="flex flex-col p-5">
      <h2 className="m-0 text-[14px] font-semibold">{t("Critical parts ready for the turnaround", "Suku cadang kritis yang siap untuk turnaround")}</h2>
      <div className="mt-3 flex items-baseline gap-2">
        <span className="text-[40px] font-semibold leading-none tracking-[-0.02em] tabular-nums">{abPct}%</span>
        <span className="text-[13px] leading-snug text-ink-3">{t(`${abReady} of ${abTotal} critical parts ready`, `${abReady} dari ${abTotal} suku cadang kritis siap`)} <Hint>{t("Parts with criticality A or B that will still have enough stock on the turnaround day, after normal use until then, if we order nothing.", "Suku cadang dengan kekritisan A atau B yang stoknya masih cukup pada hari turnaround, setelah dikurangi pemakaian normal sampai saat itu, jika kita tidak memesan apa pun.")}</Hint></span>
      </div>
      <div className="relative mt-4 h-2.5 overflow-hidden rounded-full bg-ink/[0.07]" role="img" aria-label={t(`${abPct}% ready today, ${abCanPct}% possible`, `${abPct}% siap hari ini, ${abCanPct}% bisa dicapai`)}>
        <div className="absolute inset-y-0 left-0 rounded-full bg-accent/30" style={{ width: `${abCanPct}%` }} />
        <div className="absolute inset-y-0 left-0 rounded-full bg-accent" style={{ width: `${abPct}%` }} />
      </div>
      <div className="mt-1.5 text-[12px] text-ink-3">{t(`Light bar: ${abCanPct}% with on-time orders`, `Batang terang: ${abCanPct}% dengan pemesanan tepat waktu`)}</div>
      <dl className="mt-auto grid grid-cols-[auto_minmax(0,1fr)_auto] gap-3 border-t border-line pt-3 text-[12px] leading-snug text-ink-3" style={{ marginBottom: 0, marginInline: 0 }}>
        <div><dd className="m-0 text-[16px] font-semibold tabular-nums text-ink">{short}</dd><dt>{t("parts short", "suku cadang kurang")} <Hint>{t(`All criticality levels. ${late} of them are already past their last safe order day.`, `Semua tingkat kekritisan. ${late} di antaranya sudah melewati batas aman pemesanan.`)}</Hint></dt></div>
        <div><dd className="m-0 text-[16px] font-semibold tabular-nums text-ink">{rp(gap)}</dd><dt>{t("to buy for it", "perlu dibeli")} <Hint>{t(`Cost of covering the turnaround shortages only. Just ${gapPriced} of the ${short} short parts have a real price from past purchase orders, so this counts those only and the full bill is higher. Everyday reorders are on the To do board.`, `Biaya untuk menutup kekurangan turnaround saja. Hanya ${gapPriced} dari ${short} suku cadang yang kurang memiliki harga riil dari pesanan pembelian sebelumnya, jadi angka ini hanya menghitung suku cadang tersebut dan tagihan sebenarnya lebih besar. Pemesanan ulang rutin ada di papan Tugas.`)}</Hint></dt></div>
        <div><dd className="m-0 text-[16px] font-semibold tabular-nums text-ink">{Math.max(0, days)}</dd><dt>{t("days to go", "hari lagi")} <Hint>{t(`From ${shortDate(asOf, true)}, the last day of the data.`, `Dihitung dari ${shortDate(asOf, true)}, hari terakhir data.`)}</Hint></dt></div>
      </dl>
    </Panel>
  );
}

function MonthsCard({ months }: { months: Month[] }) {
  const W = 560;
  const H = 170;
  const pad = 22;
  const n = months.length;
  const max = Math.max(1, ...months.map((m) => m.parts));
  const x = (i: number) => (i / (n - 1)) * (W - 8) + 4;
  const y = (v: number) => H - pad - (v / max) * (H - pad - 8);
  const smooth = (k: "parts" | "parts_ta") => {
    let s = `M${x(0)} ${y(months[0][k])}`;
    for (let i = 1; i < n; i++) {
      const mx = (x(i - 1) + x(i)) / 2;
      s += ` C${mx} ${y(months[i - 1][k])} ${mx} ${y(months[i][k])} ${x(i)} ${y(months[i][k])}`;
    }
    return s;
  };
  const peakI = months.reduce((b, m, i) => (m.parts_ta > months[b].parts_ta ? i : b), 0);
  const peak = months[peakI];
  const flip = x(peakI) + 194 > W;
  const label = (m: string) => `${mon()[+m.slice(5) - 1]} ${m.slice(0, 4)}`;
  return (
    <Panel className="min-w-0 p-5">
      <div className="flex items-baseline justify-between gap-3">
        <h2 className="m-0 flex items-center gap-1 text-[14px] font-semibold">{t("Parts used per month", "Suku cadang terpakai per bulan")}<Hint>{t("How many different parts were used each month, not how many units. The jump in Nov 2025 is the last turnaround: stock limits built for normal months cannot cover it, so we plan it as its own event.", "Jumlah jenis suku cadang yang dipakai setiap bulan, bukan jumlah unitnya. Lonjakan pada Nov 2025 adalah turnaround terakhir: batas stok untuk bulan-bulan biasa tidak sanggup menutupinya, jadi kami merencanakannya sebagai kejadian tersendiri.")}</Hint></h2>
        <span className="flex gap-3 text-[12px] text-ink-3">
          <span className="inline-flex items-center gap-1.5"><i className="inline-block h-[3px] w-3 rounded bg-accent" />{t("All work", "Semua pekerjaan")}</span>
          <span className="inline-flex items-center gap-1.5"><i className="inline-block h-[3px] w-3 rounded bg-twin" />{t("Turnaround work", "Pekerjaan turnaround")}</span>
        </span>
      </div>
      <svg viewBox={`0 0 ${W} ${H}`} className="mt-3 block h-auto w-full overflow-visible" role="img" aria-label={t(`Parts moved each month, peak of turnaround parts in ${label(peak.month)}`, `Suku cadang terpakai setiap bulan, puncak suku cadang turnaround pada ${label(peak.month)}`)}>
        <defs>
          <linearGradient id="pm2" x1="0" x2="0" y1="0" y2="1">
            <stop offset="0" stopColor="#d9480f" stopOpacity=".18" />
            <stop offset="1" stopColor="#d9480f" stopOpacity="0" />
          </linearGradient>
        </defs>
        {[200, 400, 600].filter((v) => v < max).map((v) => <line key={v} x1={0} x2={W} y1={y(v)} y2={y(v)} stroke="rgb(0 0 0 / .05)" />)}
        <path d={`${smooth("parts")} L${x(n - 1)} ${H - pad} L${x(0)} ${H - pad} Z`} fill="url(#pm2)" />
        <path d={smooth("parts")} fill="none" stroke="#d9480f" strokeWidth={2} />
        <path d={smooth("parts_ta")} fill="none" stroke="#0e9384" strokeWidth={1.6} />
        <line x1={x(peakI)} x2={x(peakI)} y1={6} y2={H - pad} stroke="#16171a" strokeOpacity={0.25} />
        <circle cx={x(peakI)} cy={y(peak.parts)} r={4.5} fill="#d9480f" stroke="#fff" strokeWidth={2} />
        <g transform={`translate(${flip ? x(peakI) - 194 : x(peakI) + 10},${Math.max(0, y(peak.parts) - 26)})`}>
          <rect width={184} height={40} rx={8} fill="#16171a" />
          <text x={10} y={16} fontSize={10.5} fill="rgb(255 255 255 / .7)">{t(`${label(peak.month)}, last turnaround`, `${label(peak.month)}, turnaround terakhir`)}</text>
          <text x={10} y={31} fontSize={12} fontWeight={600} fill="#fff">{t(`${peak.parts} parts, ${peak.parts_ta} for turnaround`, `${peak.parts} jenis, ${peak.parts_ta} untuk turnaround`)}</text>
        </g>
        {months.map((m, i) => i % 2 === 0 && <text key={m.month} x={x(i)} y={H - 6} textAnchor="middle" fontSize={11} fill="#a3a3a7">{mon()[+m.month.slice(5) - 1]}</text>)}
      </svg>
    </Panel>
  );
}

function MaxCard({ proof, facts, overValue, pctAbove }: { proof: ProofRow[]; facts: { stocked: number; stocked_ab: number; no_max: number }; overValue: number; pctAbove: number }) {
  const top = Math.max(1, ...proof.map((r) => r.ta_qty_last));
  return (
    <Panel className="flex min-w-0 flex-col p-5">
      <div className="flex items-baseline justify-between gap-3">
        <h2 className="m-0 flex items-center gap-1 text-[14px] font-semibold">{t("Max too low for a turnaround", "Max terlalu rendah untuk turnaround")}<Hint>{t(`Max is the upper stock limit in SAP. For ${facts.stocked} parts, the last turnaround alone used more than Max allows. Green is Max, amber is what the turnaround used.`, `Max adalah batas atas stok di SAP. Untuk ${facts.stocked} suku cadang, turnaround terakhir saja sudah memakai lebih banyak daripada yang diizinkan Max. Hijau adalah Max, kuning adalah pemakaian turnaround.`)}</Hint></h2>
        <span className="shrink-0 text-[12px] tabular-nums text-ink-3">{t(`${facts.stocked} parts`, `${facts.stocked} suku cadang`)}</span>
      </div>
      <ul className="m-0 mt-2.5 list-none space-y-2 p-0">
        {proof.slice(0, 3).map((r) => (
          <li key={r.material_no} className="text-[12.5px] text-ink-2">
            <div className="flex justify-between gap-3">
              <span className="truncate">{partName(r.description)}</span>
              <span className="shrink-0 tabular-nums">Max {num(r.max_cur)}, {t("used", "terpakai")} <b className="font-semibold text-act-ink">{qty(r.ta_qty_last, r.unit)}</b></span>
            </div>
            <div className="relative mt-1 h-1.5 rounded-full bg-ink/[0.06]">
              <i className="absolute inset-y-0 left-0 block rounded-full bg-plan" style={{ width: `${(r.ta_qty_last / top) * 100}%` }} />
              <i className="absolute inset-y-0 left-0 block rounded-full bg-ready" style={{ width: `${(r.max_cur / top) * 100}%` }} />
            </div>
          </li>
        ))}
      </ul>
      <div className="mt-3 flex items-center justify-between gap-3 rounded-[12px] bg-ink px-3.5 py-2.5 text-white">
        <div className="min-w-0 text-[12px] leading-tight text-white/70">{t("Meanwhile, held above Max", "Sementara itu, stok di atas Max")} <Hint>{t(`Other parts hold this much more than their Max allows. ${Math.round(pctAbove * 100)}% of purchase spend went to parts that are over their limit today.`, `Suku cadang lain menyimpan sebanyak ini melebihi batas Max-nya. Sebesar ${Math.round(pctAbove * 100)}% belanja pembelian dipakai untuk suku cadang yang hari ini melebihi batasnya.`)}</Hint></div>
        <div className="shrink-0 text-[20px] font-semibold tracking-[-0.01em] tabular-nums">{rp(overValue)}</div>
      </div>
    </Panel>
  );
}

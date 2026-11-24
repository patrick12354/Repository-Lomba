"use client";

import { t } from "@/lib/i18n";
import { useEffect, useMemo, useState, type ReactNode } from "react";
import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import { ArrowRight, ChevronDown, X } from "lucide-react";
import { Activity, Anchor, BrickWall, Cable, Circle, CircleDashed, CircleDot, Cog, CornerDownRight, Disc, Droplet, Droplets, Fan, Filter, Flame, Gauge, GitFork, Grid3x3, Layers, Lightbulb, Link2, Package, PackageCheck, Plug, Route, Ruler, Scroll, Search, ShieldCheck, ShoppingCart, SprayCan, Spline, Thermometer, ToggleLeft, Truck, Waves, Workflow, Wrench, Zap, type LucideIcon } from "@/components/icons";
import type { PartRow, Shelf } from "@/lib/data";
import { ACTION_STATUS, ACTION_VERB, cn, num, partName, amount, rp } from "@/lib/format";
import { Chip, CritTile, Panel } from "./ui";

const ICONS: Record<string, LucideIcon> = {
  ANCHOR: Anchor, ANTIRUST: SprayCan, BEARING: CircleDot, BLADE: Fan, BOLT: Wrench, "BURNER TIP": Flame, CABLE: Cable, CASTABLE: Layers, "CERAMIC FIBER": Waves, CONNECTOR: Plug, COUPLING: Link2, "DEMISTER PAD": Grid3x3, DIAPHRAGM: CircleDashed, DISC: Disc, ELBOW: CornerDownRight, FAN: Fan, "FILTER ELEMENT": Filter, FIREBRICK: BrickWall, FLANGE: Circle, GASKET: Circle, GAUGE: Gauge, GLAND: ShieldCheck, GREASE: Droplet, IMPELLER: Cog, LAMP: Lightbulb, NOZZLE: Droplets, "O-RING": Circle, OIL: Droplet, "PACKING SET": Package, PIPE: Route, POSITIONER: Gauge, RING: Circle, SCREEN: Grid3x3, SCREW: Wrench, SEAL: ShieldCheck, "SEAT RING": Circle, SLEEVE: Ruler, "SOLENOID VALVE": Zap, SPRING: Spline, STUDBOLT: Wrench, SWITCH: ToggleLeft, TAPE: Scroll, TEE: GitFork, TERMINAL: Plug, "TERMINAL BLOCK": Plug, THERMOCOUPLE: Thermometer, THERMOWELL: Thermometer, TRANSMITTER: Activity, "TRAY VALVE": Workflow, "TRIM SET": Workflow, "TUBE PLUG": Plug, TUBING: Route, VALVE: Workflow,
};
const label = (c: string) => c.charAt(0) + c.slice(1).toLowerCase();
const p_ = () => t("parts", "suku cadang");

type Flow = { suppliers: number; supplied: number; lead: number; reorder: number; reorder_priced: number; reorder_value: number; on_shelf: number; on_shelf_priced: number; shelf_value: number; used: number; parts: number };
type Supplier = { name: string; parts: number; lead: number | null };
type Sort = "empty" | "money" | "name";

const BINS = 20;
/** Split a shelf into bins by share, so every card reads the same way. */
function bins(s: Shelf) {
  const groups: [string, number][] = [
    ["bg-act", s.empty],
    ["bg-plan", s.low],
    ["bg-ready", s.ok],
    ["bg-excess", s.over],
    ["bg-ink/20", s.idle],
  ];
  const total = Math.max(1, s.parts);
  const out: string[] = [];
  let carried = 0;
  for (const [cls, n] of groups) {
    const exact = (n / total) * BINS + carried;
    const take = Math.round(exact);
    carried = exact - take;
    for (let i = 0; i < take && out.length < BINS; i++) out.push(cls);
  }
  while (out.length < BINS) out.push("bg-ink/[0.07]");
  return out;
}

function Arrow({ note }: { note?: string }) {
  return (
    <div className="flex w-[96px] shrink-0 flex-col items-center justify-center gap-0.5 text-ink-4">
      <ArrowRight aria-hidden className="h-4 w-4" />
      {note && <span className="whitespace-nowrap text-center text-[11px] leading-tight text-ink-3">{note}</span>}
    </div>
  );
}

export function SupplyFlow({ flow, suppliers }: { flow: Flow; suppliers: Supplier[] }) {
  const [open, setOpen] = useState(false);
  const stage = "group flex min-w-0 flex-1 flex-col rounded-[12px] px-3 py-2 text-left transition-colors duration-150 hover:bg-ink/[0.03]";
  return (
    <Panel className="p-1.5">
      <div className="flex items-stretch">
        <button type="button" aria-expanded={open} onClick={() => setOpen((o) => !o)} className={stage}>
          <span className="flex items-center gap-2 text-[12.5px] font-medium text-ink-3">
            <Truck aria-hidden className="h-4 w-4" />{t("Suppliers", "Pemasok")}
            <ChevronDown aria-hidden className={cn("ml-auto h-3.5 w-3.5 transition-transform duration-150", open && "rotate-180")} />
          </span>
          <span className="mt-1 text-[22px] font-semibold leading-none tracking-[-0.02em] tabular-nums">{num(flow.suppliers)}</span>
          <span className="mt-1 text-[12px] text-ink-3">{t(`for ${num(flow.supplied)} parts`, `untuk ${num(flow.supplied)} suku cadang`)}</span>
        </button>
        <Arrow note={t(`about ${num(flow.lead)} days`, `sekitar ${num(flow.lead)} hari`)} />
        <Link href="/todo?kind=expedite,order" className={stage}>
          <span className="flex items-center gap-2 text-[12.5px] font-medium text-ink-3"><ShoppingCart aria-hidden className="h-4 w-4" />{t("To order", "Perlu dipesan")}</span>
          <span className="mt-1 text-[22px] font-semibold leading-none tracking-[-0.02em] tabular-nums text-act-ink">{num(flow.reorder)}</span>
          <span className="mt-1 text-[12px] text-ink-3" title={t(`Rupiah counts the ${num(flow.reorder_priced)} parts that have a PO price`, `Nilai rupiah menghitung ${num(flow.reorder_priced)} suku cadang yang memiliki harga PO`)}>{t(`parts · ${rp(flow.reorder_value)} for ${num(flow.reorder_priced)} priced`, `suku cadang · ${rp(flow.reorder_value)} untuk ${num(flow.reorder_priced)} yang berharga`)}</span>
        </Link>
        <Arrow />
        <Link href="/stock?tab=library" className={stage}>
          <span className="flex items-center gap-2 text-[12.5px] font-medium text-ink-3"><PackageCheck aria-hidden className="h-4 w-4" />{t("On the shelf", "Di rak")}</span>
          <span className="mt-1 text-[22px] font-semibold leading-none tracking-[-0.02em] tabular-nums">{num(flow.on_shelf)}</span>
          <span className="mt-1 text-[12px] text-ink-3" title={t(`Rupiah counts the ${num(flow.on_shelf_priced)} parts on the shelf that have a PO price`, `Nilai rupiah menghitung ${num(flow.on_shelf_priced)} suku cadang di rak yang memiliki harga PO`)}>{t(`of ${num(flow.parts)} parts · ${rp(flow.shelf_value)} for ${num(flow.on_shelf_priced)} priced`, `dari ${num(flow.parts)} suku cadang · ${rp(flow.shelf_value)} untuk ${num(flow.on_shelf_priced)} yang berharga`)}</span>
        </Link>
        <Arrow />
        <Link href="/forecast" className={stage}>
          <span className="flex items-center gap-2 text-[12.5px] font-medium text-ink-3"><Wrench aria-hidden className="h-4 w-4" />{t("Used by the plant", "Dipakai kilang")}</span>
          <span className="mt-1 text-[22px] font-semibold leading-none tracking-[-0.02em] tabular-nums">{num(flow.used)}</span>
          <span className="mt-1 text-[12px] text-ink-3">{t("used in 17 months", "terpakai dalam 17 bulan")}</span>
        </Link>
      </div>
      {open && (
        <ul className="m-0 mt-1 grid list-none grid-cols-5 gap-2 border-t border-line p-2 pt-3">
          {suppliers.map((s) => (
            <li key={s.name} className="min-w-0 rounded-[10px] bg-panel-2 px-3 py-2">
              <div className="truncate text-[12.5px] font-medium" title={s.name}>{s.name}</div>
              <div className="mt-0.5 text-[12px] tabular-nums text-ink-3">{num(s.parts)} {p_()} · {s.lead != null ? t(`about ${num(s.lead)} days`, `sekitar ${num(s.lead)} hari`) : t("delivery time unknown", "waktu kirim tidak diketahui")}</div>
            </li>
          ))}
        </ul>
      )}
    </Panel>
  );
}

const tabs = () =>
  [
    ["overview", t("Overview", "Ringkasan")],
    ["library", t("Parts library", "Pustaka suku cadang")],
    ["slow", t("Slow and dead stock", "Stok lambat dan stok mati")],
  ] as const;

/** One page, three questions. The overview always comes first; the long lists wait behind a tab. */
export function StockTabs({ overview, library, slow }: { overview: ReactNode; library: ReactNode; slow: ReactNode }) {
  const sp = useSearchParams();
  const router = useRouter();
  const path = usePathname();
  const TABS = tabs();
  const tab = TABS.find(([k]) => k === sp.get("tab"))?.[0] ?? "overview";
  return (
    <div className="space-y-4">
      <div data-tour="s-tabs" role="tablist" aria-label={t("Stock views", "Tampilan stok")} className="flex gap-1 border-b border-line">
        {TABS.map(([k, l]) => (
          <button key={k} type="button" role="tab" aria-selected={tab === k} onClick={() => router.replace(k === "overview" ? path : `${path}?tab=${k}`, { scroll: false })} className={cn("relative h-9 px-2.5 text-[13px] transition-colors", tab === k ? "font-medium text-ink" : "text-ink-3 hover:text-ink")}>
            {l}
            {tab === k && <span aria-hidden className="absolute inset-x-1.5 -bottom-px h-0.5 rounded-full bg-ink" />}
          </button>
        ))}
      </div>
      {tab === "overview" ? overview : tab === "library" ? library : slow}
    </div>
  );
}

export function StockLibrary({ shelves }: { shelves: Shelf[] }) {
  const [q, setQ] = useState("");
  const [sort, setSort] = useState<Sort>("empty");
  const [onlyEmpty, setOnlyEmpty] = useState(false);
  const [open, setOpen] = useState<Shelf | null>(null);

  const list = useMemo(() => {
    const w = q.trim().toLowerCase();
    const r = shelves.filter((s) => (!w || s.category.toLowerCase().includes(w)) && (!onlyEmpty || s.critical_empty > 0));
    return [...r].sort((a, b) => (sort === "name" ? a.category.localeCompare(b.category) : sort === "money" ? b.value - a.value : b.critical_empty - a.critical_empty || b.empty - a.empty));
  }, [shelves, q, sort, onlyEmpty]);

  return (
    <section id="library" aria-label={t("Parts library", "Pustaka suku cadang")} className="space-y-3">
      <div className="flex items-center gap-2">
        <div className="mr-auto flex flex-wrap gap-x-3 gap-y-1 text-[12px] text-ink-3">
          {([["bg-act", t("Empty, still used", "Kosong, masih dipakai")], ["bg-plan", t("Low", "Menipis")], ["bg-ready", t("Healthy", "Sehat")], ["bg-excess", t("Too much", "Berlebih")], ["bg-ink/20", t("Not used", "Tidak terpakai")]] as const).map(([c, l]) => (
            <span key={l} className="inline-flex items-center gap-1.5"><i className={cn("h-2.5 w-2.5 rounded-[3px]", c)} />{l}</span>
          ))}
        </div>
        <label className="flex h-9 w-[240px] items-center gap-2 rounded-[10px] border border-line bg-panel px-2.5 text-[13px]">
          <Search aria-hidden className="h-4 w-4 shrink-0 text-ink-3" />
          <span className="sr-only">{t("Find a shelf", "Cari rak")}</span>
          <input value={q} onChange={(e) => setQ(e.target.value)} placeholder={t("Find a shelf", "Cari rak")} className="min-w-0 flex-1 bg-transparent outline-none placeholder:text-ink-4" />
        </label>
        <button type="button" aria-pressed={onlyEmpty} onClick={() => setOnlyEmpty((v) => !v)} className={cn("h-9 rounded-[10px] border px-3 text-[13px] transition-colors", onlyEmpty ? "border-ink bg-ink font-medium text-white" : "border-line bg-panel text-ink-2 hover:border-line-2")}>
          {t("Empty critical parts", "Suku cadang kritis kosong")}
        </button>
        <div role="radiogroup" aria-label={t("Sort shelves", "Urutkan rak")} className="inline-flex h-9 rounded-[10px] border border-line bg-panel p-[3px]">
          {([["empty", t("Most empty", "Paling kosong")], ["money", t("Most money", "Nilai terbesar")], ["name", "A–Z"]] as const).map(([k, l]) => (
            <button key={k} type="button" role="radio" aria-checked={sort === k} onClick={() => setSort(k)} className={cn("rounded-[7px] px-2.5 text-[13px] transition-colors", sort === k ? "bg-ink font-medium text-white" : "text-ink-2 hover:bg-ink/[0.05]")}>
              {l}
            </button>
          ))}
        </div>
      </div>
      {list.length === 0 ? (
        <Panel className="px-6 py-12 text-center text-[13.5px] text-ink-3">{t("No shelf matches. Clear the search or the filter.", "Tidak ada rak yang cocok. Hapus pencarian atau filternya.")}</Panel>
      ) : (
        <ul className="m-0 grid max-h-[calc(100dvh-352px)] min-h-[320px] list-none grid-cols-5 gap-2.5 overflow-y-auto p-0 pr-1">
          {list.map((s) => {
            const Icon = ICONS[s.category] ?? Package;
            const alarm = s.critical_empty > 0;
            return (
              <li key={s.category}>
                <button type="button" onClick={() => setOpen(s)} className="group flex h-full w-full flex-col rounded-[12px] border border-line bg-panel p-2.5 text-left transition-[border-color,box-shadow] duration-150 hover:border-line-2">
                  <span className="flex items-center gap-2">
                    <span className={cn("grid h-7 w-7 shrink-0 place-items-center rounded-[8px]", alarm ? "bg-act-soft text-act-ink" : "bg-panel-2 text-ink-2")}>
                      <Icon aria-hidden className="h-4 w-4" strokeWidth={1.8} />
                    </span>
                    <span className="min-w-0 flex-1 truncate text-[13px] font-medium">{label(s.category)}</span>
                    <span className="shrink-0 text-[12px] tabular-nums text-ink-3">{num(s.parts)} {p_()}</span>
                  </span>
                  <span className="mt-2 grid grid-cols-[repeat(20,minmax(0,1fr))] gap-[2px]" role="img" aria-label={t(`${s.empty} empty, ${s.low} low, ${s.ok} healthy, ${s.over} too much, ${s.idle} not used`, `${s.empty} kosong, ${s.low} menipis, ${s.ok} sehat, ${s.over} berlebih, ${s.idle} tidak terpakai`)}>
                    {bins(s).map((c, i) => <i key={i} className={cn("block h-2.5 rounded-[2px]", c)} />)}
                  </span>
                  <span className="mt-1.5 flex items-baseline justify-between gap-2 text-[12px] tabular-nums">
                    <span className={alarm ? "font-medium text-act-ink" : "text-ink-3"}>{alarm ? t(`${s.critical_empty} critical empty`, `${s.critical_empty} kritis kosong`) : t("No critical empty", "Tidak ada yang kritis kosong")}</span>
                    <span className="text-ink-3">{rp(s.value)}</span>
                  </span>
                </button>
              </li>
            );
          })}
        </ul>
      )}
      <ShelfDrawer shelf={open} onClose={() => setOpen(null)} />
    </section>
  );
}

function ShelfDrawer({ shelf, onClose }: { shelf: Shelf | null; onClose: () => void }) {
  const reduce = useReducedMotion();
  const [rows, setRows] = useState<PartRow[] | null>(null);
  const [total, setTotal] = useState(0);
  const category = shelf?.category;
  useEffect(() => {
    if (!category) return;
    const ctl = new AbortController();
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setRows(null);
    fetch(`/api/parts?category=${encodeURIComponent(category)}&limit=100`, { signal: ctl.signal })
      .then((r) => r.json())
      .then((d) => {
        setRows(d.rows);
        setTotal(d.total);
      })
      .catch(() => {});
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => {
      ctl.abort();
      window.removeEventListener("keydown", onKey);
    };
  }, [category, onClose]);
  const Icon = shelf ? ICONS[shelf.category] ?? Package : Package;
  return (
    <AnimatePresence>
      {shelf && (
        <div className="fixed inset-0 z-40" role="dialog" aria-modal="true" aria-label={label(shelf.category)}>
          <motion.button type="button" aria-label={t("Close", "Tutup")} onClick={onClose} className="absolute inset-0 bg-ink/25" initial={reduce ? false : { opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.16 }} />
          <motion.aside className="absolute inset-y-0 right-0 flex w-[460px] max-w-full flex-col bg-panel shadow-float" initial={reduce ? false : { x: 40, opacity: 0 }} animate={{ x: 0, opacity: 1 }} exit={{ x: 40, opacity: 0 }} transition={{ duration: 0.2, ease: [0.16, 1, 0.3, 1] }}>
            <header className="flex items-center gap-3 border-b border-line p-4">
              <span className="grid h-10 w-10 place-items-center rounded-[12px] bg-panel-2 text-ink-2"><Icon aria-hidden className="h-5 w-5" /></span>
              <div className="min-w-0 flex-1">
                <h3 className="m-0 truncate text-[16px] font-semibold">{label(shelf.category)}</h3>
                <p className="m-0 text-[12.5px] tabular-nums text-ink-3">{num(shelf.parts)} {p_()} · {shelf.empty} {t("empty", "kosong")} · {rp(shelf.value)}</p>
              </div>
              <button type="button" onClick={onClose} aria-label={t("Close", "Tutup")} className="grid h-8 w-8 place-items-center rounded-[8px] text-ink-3 transition-colors hover:bg-ink/[0.05] hover:text-ink"><X aria-hidden className="h-4 w-4" /></button>
            </header>
            {rows == null ? (
              <p className="m-0 p-6 text-center text-[13px] text-ink-3">{t("Opening the shelf…", "Membuka rak…")}</p>
            ) : (
              <ul className="m-0 min-h-0 flex-1 list-none divide-y divide-line overflow-y-auto p-0">
                {rows.map((p) => (
                  <li key={p.material_no}>
                    <Link href={`/parts/${p.material_no}`} className="flex items-center gap-3 px-4 py-2.5 transition-colors hover:bg-ink/[0.03]">
                      <CritTile crit={p.criticality} />
                      <span className="min-w-0 flex-1">
                        <span className="block truncate text-[13px] font-medium">{partName(p.description)}</span>
                        <span className="block text-[12px] tabular-nums text-ink-3">{amount(p.stock, p.unit)} {t("on the shelf", "di rak")} · Min {num(p.min_cur)} Max {num(p.max_cur)}</span>
                      </span>
                      <Chip status={ACTION_STATUS[p.action]} label={ACTION_VERB[p.action]} />
                    </Link>
                  </li>
                ))}
                {total > rows.length && <li className="p-3 text-center text-[12.5px] text-ink-3">{t(`First ${rows.length} of ${num(total)}, most urgent on top. Use Find a part for the rest.`, `${rows.length} pertama dari ${num(total)}, yang paling mendesak di atas. Gunakan Cari suku cadang untuk sisanya.`)}</li>}
              </ul>
            )}
          </motion.aside>
        </div>
      )}
    </AnimatePresence>
  );
}

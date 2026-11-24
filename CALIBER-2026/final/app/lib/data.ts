import "server-only";
import { all, one, meta } from "./db";
import { buyBasis, buySplit, type Section } from "./people";
import { SHELF_LIFE, type ShelfLife } from "./shelf-life";

let tables: Set<string> | null = null;
function hasTable(name: string): boolean {
  if (!tables) tables = new Set(all<{ name: string }>("select name from sqlite_master where type = 'table'").map((r) => r.name));
  return tables.has(name);
}

function fact(key: string): number | null {
  if (!hasTable("app_facts")) return null;
  return one<{ value: number }>("select value from app_facts where key = ?", key)?.value ?? null;
}
import {
  type Action,
  type Crit,
  type TaStatus,
  addDays,
  daysBetween,
  CRITS,
  CRIT_RANK,
  isTopCrit,
} from "./format";

/* ------------------------------------------------------------------ shared */

export function asOf(): string {
  return meta().as_of_date;
}

export function defaultTa(): string {
  return meta().next_ta_default;
}

export function hasLocations(): boolean {
  return hasTable("material_location");
}

type Donor = { group_id: number; material_no: number; donor_no: number; surplus: number };

/** For every part that has a twin holding stock above its Max: the best donor. */
function donorMap(): Map<number, { donor: number; surplus: number }> {
  const rows = all<Donor>(`
    select t.group_id, t.material_no, d.material_no as donor_no, (dm.stock - dm.max_cur) as surplus
    from twins t
    join twins d on d.group_id = t.group_id and d.material_no != t.material_no and d.role = 'DONOR'
    join materials dm on dm.material_no = d.material_no
    where dm.stock > dm.max_cur`);
  const map = new Map<number, { donor: number; surplus: number }>();
  for (const r of rows) {
    const cur = map.get(r.material_no);
    if (!cur || r.surplus > cur.surplus) map.set(r.material_no, { donor: r.donor_no, surplus: r.surplus });
  }
  return map;
}

/* ---------------------------------------------------------- turnaround (E1) */

export type TaPart = {
  material_no: number;
  description: string;
  category: string;
  unit: string;
  criticality: Crit;
  /** What the turnaround itself uses. */
  need: number;
  /** Normal use expected between today and the turnaround. */
  routine: number;
  /** need + routine: everything that has to be on hand or on order by the turnaround. */
  need_total: number;
  stock: number;
  gap: number;
  lt_p90: number;
  order_by: string;
  days_left: number;
  status: TaStatus;
  gap_value: number | null;
  exceeds_max: boolean;
  max_cur: number;
  equipment: string[];
  twin: { donor: number; surplus: number } | null;
};

export type Readiness = {
  asOf: string;
  taDate: string;
  scale: number;
  daysToTa: number;
  total: number;
  byCrit: { crit: Crit; ready: number; total: number }[];
  counts: Record<TaStatus, number>;
  weeks: { week: number; start: string; count: number; act: number }[];
  parts: TaPart[];
  gapValue: number;
  exceedsMax: number;
  furnaces: { equipment: string; total: number; short: number }[];
  classes: { cls: string; total: number; short: number }[];
};

type TaRow = {
  material_no: number;
  description: string;
  category: string;
  unit: string;
  criticality: Crit;
  ta_qty_last: number;
  stock: number;
  lt_p90: number;
  unit_price: number | null;
  price_source: string;
  max_cur: number;
  exceeds_max: number;
  base_qty: number;
  q50: number;
  event_qty: number;
  equipment: string | null;
};

const CLASS_NAMES: Record<string, string> = {
  BF: "Furnaces",
  KC: "Compressors",
  PP: "Pumps",
  HE: "Heat exchangers",
  KT: "Turbines",
};

export function readiness(taDate?: string, scale = 1, shock = 0): Readiness {
  const m = meta();
  const today = m.as_of_date;
  const ta = taDate && /^\d{4}-\d{2}-\d{2}$/.test(taDate) ? taDate : m.next_ta_default;
  const s = Math.min(2, Math.max(0.3, Number.isFinite(scale) ? scale : 1));
  const buffer = Number(m.ta_buffer_days ?? 14);
  const delay = Math.min(180, Math.max(0, Number.isFinite(shock) ? shock : 0));
  const donors = donorMap();

  const rows = all<TaRow>(`
    select t.material_no, m.description, m.category, m.unit, t.criticality, t.ta_qty_last, m.stock, t.lt_p90,
           m.unit_price, m.price_source, m.max_cur, t.exceeds_max, f.base_qty, f.q50, f.event_qty,
           ${hasTable("material_location") ? "(select group_concat(distinct l.equipment) from material_location l where l.material_no = t.material_no)" : "null"} as equipment
    from ta_kit t join materials m using (material_no) join forecast f using (material_no)`);

  const horizon = Number(m.forecast_horizon_days ?? 180);
  const leadUp = Math.max(0, daysBetween(today, ta));
  const parts: TaPart[] = rows.map((r) => {
    const need = r.ta_qty_last * s;
    // The shelf keeps emptying before the turnaround, so count normal use up to that day. The most likely estimate, not the mean,
    // so a few extreme months do not inflate it. Whole units: a fraction of a part is not a shortage.
    const routine = Math.round((Math.max(0, (r.q50 ?? 0) - (r.event_qty ?? 0)) * leadUp) / horizon);
    const need_total = need + routine;
    const gap = Math.max(0, need_total - r.stock);
    const lt = r.lt_p90 + delay;
    const order_by = addDays(ta, -Math.round(lt) - buffer);
    const days_left = daysBetween(today, order_by);
    let status: TaStatus = "READY";
    if (gap > 1e-9) status = days_left < 0 ? "TOO_LATE" : days_left <= 7 ? "ORDER_NOW" : days_left <= 30 ? "PLAN" : "LATER";
    return {
      material_no: r.material_no,
      description: r.description,
      category: r.category,
      unit: r.unit,
      criticality: r.criticality,
      need,
      routine,
      need_total,
      stock: r.stock,
      gap,
      lt_p90: lt,
      order_by,
      days_left,
      status,
      gap_value: r.price_source === "po" && r.unit_price ? gap * r.unit_price : null,
      exceeds_max: need > r.max_cur,
      max_cur: r.max_cur,
      equipment: r.equipment ? r.equipment.split(",") : [],
      twin: gap > 0 ? donors.get(r.material_no) ?? null : null,
    };
  });

  const counts: Record<TaStatus, number> = { TOO_LATE: 0, ORDER_NOW: 0, PLAN: 0, LATER: 0, READY: 0 };
  for (const p of parts) counts[p.status]++;

  const byCrit = CRITS.map((crit) => {
    const ps = parts.filter((p) => p.criticality === crit);
    return { crit, ready: ps.filter((p) => p.status === "READY").length, total: ps.length };
  });

  const daysToTa = daysBetween(today, ta);
  const nWeeks = Math.max(1, Math.min(26, Math.ceil(daysToTa / 7)));
  const weeks = Array.from({ length: nWeeks + 1 }, (_, i) => ({
    week: i - 1,
    start: i === 0 ? today : addDays(today, (i - 1) * 7),
    count: 0,
    act: 0,
  }));
  for (const p of parts) {
    if (p.status === "READY") continue;
    const w = p.days_left < 0 ? -1 : Math.min(nWeeks - 1, Math.floor(p.days_left / 7));
    const bin = weeks[w + 1];
    bin.count++;
    if (isTopCrit(p.criticality)) bin.act++;
  }

  const furnaceMap = new Map<string, { total: number; short: number }>();
  const classMap = new Map<string, { total: number; short: number }>();
  for (const p of parts) {
    const seenCls = new Set<string>();
    for (const e of p.equipment) {
      if (/^BF-1(0[1-9]|1[0-2])$/.test(e)) {
        const f = furnaceMap.get(e) ?? { total: 0, short: 0 };
        f.total++;
        if (p.status !== "READY") f.short++;
        furnaceMap.set(e, f);
      }
      const cls = e.split("-")[0];
      if (CLASS_NAMES[cls] && !seenCls.has(cls)) {
        seenCls.add(cls);
        const c = classMap.get(cls) ?? { total: 0, short: 0 };
        c.total++;
        if (p.status !== "READY") c.short++;
        classMap.set(cls, c);
      }
    }
  }
  const furnaces = Array.from({ length: 12 }, (_, i) => `BF-1${String(i + 1).padStart(2, "0")}`).map((e) => ({
    equipment: e,
    ...(furnaceMap.get(e) ?? { total: 0, short: 0 }),
  }));
  const classes = Object.keys(CLASS_NAMES)
    .map((cls) => ({ cls: CLASS_NAMES[cls], ...(classMap.get(cls) ?? { total: 0, short: 0 }) }))
    .sort((a, b) => b.total - a.total);

  const order: Record<TaStatus, number> = { TOO_LATE: 0, ORDER_NOW: 1, PLAN: 2, LATER: 3, READY: 4 };
  const critRank = CRIT_RANK;
  parts.sort(
    (a, b) =>
      order[a.status] - order[b.status] ||
      critRank[a.criticality] - critRank[b.criticality] ||
      a.days_left - b.days_left ||
      (b.gap_value ?? 0) - (a.gap_value ?? 0),
  );

  return {
    asOf: today,
    taDate: ta,
    scale: s,
    daysToTa,
    total: parts.length,
    byCrit,
    counts,
    weeks,
    parts,
    gapValue: parts.reduce((acc, p) => acc + (p.gap_value ?? 0), 0),
    exceedsMax: parts.filter((p) => p.exceeds_max).length,
    furnaces,
    classes,
  };
}

export type MachineView = {
  taDate: string;
  scale: number;
  asOf: string;
  daysToTa: number;
  total: number;
  counts: Record<TaStatus, number>;
  byCrit: Readiness["byCrit"];
  gapValue: number;
  belowMaxStocked: number;
  noMax: number;
  twinCount: number;
  parts: TaPart[];
  weeks: Readiness["weeks"];
  units: { equipment: string; total: number; short: number }[];
};

/** The same readiness numbers, narrowed to one equipment family and optionally one unit. */
export function machineView(prefix: string, taDate?: string, scale = 1, unit?: string, shock = 0): MachineView {
  const r = readiness(taDate, scale, shock);
  const inFamily = r.parts.filter((p) => p.equipment.some((e) => e.startsWith(`${prefix}-`)));
  const parts = unit ? inFamily.filter((p) => p.equipment.includes(unit)) : inFamily;
  const counts: Record<TaStatus, number> = { TOO_LATE: 0, ORDER_NOW: 0, PLAN: 0, LATER: 0, READY: 0 };
  for (const p of parts) counts[p.status]++;
  const byCrit = CRITS.map((crit) => {
    const ps = parts.filter((p) => p.criticality === crit);
    return { crit, ready: ps.filter((p) => p.status === "READY").length, total: ps.length };
  });
  const weeks = r.weeks.map((w) => ({ ...w, count: 0, act: 0 }));
  const nWeeks = weeks.length - 1;
  for (const p of parts) {
    if (p.status === "READY") continue;
    const w = p.days_left < 0 ? -1 : Math.min(nWeeks - 1, Math.floor(p.days_left / 7));
    weeks[w + 1].count++;
    if (isTopCrit(p.criticality)) weeks[w + 1].act++;
  }
  const unitMap = new Map<string, { total: number; short: number }>();
  for (const p of inFamily)
    for (const e of p.equipment) {
      if (!e.startsWith(`${prefix}-`)) continue;
      const u = unitMap.get(e) ?? { total: 0, short: 0 };
      u.total++;
      if (p.status !== "READY") u.short++;
      unitMap.set(e, u);
    }
  const units = Array.from(unitMap, ([equipment, v]) => ({ equipment, ...v })).sort((a, b) => b.short - a.short || a.equipment.localeCompare(b.equipment));
  return {
    taDate: r.taDate,
    scale: r.scale,
    asOf: r.asOf,
    daysToTa: r.daysToTa,
    total: parts.length,
    counts,
    byCrit,
    gapValue: parts.reduce((a, p) => a + (p.gap_value ?? 0), 0),
    belowMaxStocked: parts.filter((p) => p.exceeds_max && p.max_cur > 0).length,
    noMax: parts.filter((p) => p.exceeds_max && p.max_cur <= 0).length,
    twinCount: parts.filter((p) => p.twin).length,
    parts,
    weeks,
    units,
  };
}

/** Parts whose one-turnaround need is bigger than their Max: the proof that static Min–Max cannot cover a shutdown. */
export function maxFacts() {
  return one<{ stocked: number; stocked_ab: number; no_max: number; no_max_nonstock: number }>(`
    select sum(t.exceeds_max = 1 and m.max_cur > 0) as stocked,
           sum(t.exceeds_max = 1 and m.max_cur > 0 and t.criticality in ('A','B')) as stocked_ab,
           sum(t.exceeds_max = 1 and m.max_cur <= 0) as no_max,
           0 as no_max_nonstock
    from ta_kit t join materials m using (material_no)`)!;
}

export function maxProof(limit = 8) {
  return all<{ material_no: number; description: string; unit: string; criticality: Crit; ta_qty_last: number; max_cur: number; stock: number }>(
    `select t.material_no, m.description, m.unit, t.criticality, t.ta_qty_last, m.max_cur, m.stock
     from ta_kit t join materials m using (material_no)
     where t.exceeds_max = 1 and t.criticality in ('A','B') and m.max_cur > 0
     order by (t.ta_qty_last * 1.0 / m.max_cur) desc limit ?`,
    limit,
  );
}

/* ------------------------------------------------------------- to-do tasks */

export type TaskKind = "expedite" | "order" | "twin" | "reduce" | "dispose" | "watch";
export type Urgency = "late" | "now" | "month" | "later" | "house";

export type Unusual = { month: string; qty: number; usual: number; ratio: number };

/** One part, one task: the turnaround gap and the everyday policy are merged so every page says the same thing. */
export type Task = {
  id: string;
  material_no: number;
  description: string;
  category: string;
  unit: string;
  criticality: Crit;
  kind: TaskKind;
  urgency: Urgency;
  stock: number;
  /** The level stock is measured against: turnaround need, new Min, or new Max when there is too much. */
  target: number;
  qty: number;
  order_by: string | null;
  days_left: number | null;
  lead_time: number;
  value: number | null;
  risk: number;
  ta: boolean;
  mrp: string;
  ta_gap: number;
  /** Normal use expected before the turnaround, already counted in target. */
  ta_routine: number;
  equipment: string[];
  machines: string[];
  /** Equipment codes from the functional locations, most installed first. */
  codes: string[];
  section: Section;
  twin: { donor: number; surplus: number } | null;
  unusual: Unusual | null;
};

const URGENCY_RANK: Record<Urgency, number> = { late: 0, now: 1, month: 2, later: 3, house: 4 };
const KIND_RANK: Record<TaskKind, number> = { expedite: 0, order: 1, twin: 2, watch: 3, reduce: 4, dispose: 5 };
const PREFIX_MACHINE: Record<string, string> = { BF: "furnace", KC: "compressor", PP: "pump", KT: "turbine", HE: "exchanger" };

let unusualCache: Map<number, Unusual> | null = null;

/** A routine (non-turnaround) month in the last six that ran at 3× or more of the part's other active months. */
function unusualMap(): Map<number, Unusual> {
  if (unusualCache) return unusualCache;
  const rows = all<{ material_no: number; ym: string; qty: number; qty_event: number }>("select material_no, ym, qty, qty_event from consumption_monthly");
  const by = new Map<number, { ym: string; v: number }[]>();
  for (const r of rows) {
    const v = Math.max(0, (r.qty ?? 0) - (r.qty_event ?? 0));
    if (v <= 0) continue;
    const list = by.get(r.material_no) ?? [];
    list.push({ ym: r.ym, v });
    by.set(r.material_no, list);
  }
  const months = Array.from(new Set(rows.map((r) => r.ym))).sort();
  const cut = months[Math.max(0, months.length - 6)];
  const out = new Map<number, Unusual>();
  for (const [no, list] of by) {
    if (list.length < 4) continue;
    const recent = list.filter((x) => x.ym >= cut).sort((a, b) => b.v - a.v)[0];
    if (!recent) continue;
    const others = list.filter((x) => x !== recent);
    const usual = others.reduce((a, x) => a + x.v, 0) / others.length;
    if (recent.v >= 3 * usual && recent.v - usual >= 3) out.set(no, { month: recent.ym, qty: recent.v, usual, ratio: recent.v / usual });
  }
  unusualCache = out;
  return out;
}

function codeMap(): Map<number, { codes: string[]; section: Section }> {
  const out = new Map<number, { codes: string[]; section: Section }>();
  if (!hasTable("material_code")) return out;
  for (const r of all<{ material_no: number; code: string; section: Section }>("select material_no, code, section from material_code order by material_no, code = 'OTHER', n desc")) {
    const cur = out.get(r.material_no);
    if (cur) cur.codes.push(r.code);
    else out.set(r.material_no, { codes: [r.code], section: r.section });
  }
  return out;
}

let taskCache: Task[] | null = null;

export function tasks(): Task[] {
  if (taskCache) return taskCache;
  const today = asOf();
  const r = readiness();
  const ta = new Map(r.parts.map((p) => [p.material_no, p]));
  const donors = donorMap();
  const unusual = unusualMap();
  const codes = codeMap();
  const rows = all<{ material_no: number; description: string; category: string; unit: string; criticality: Crit; stock: number; lt_p90: number; unit_price: number | null; price_source: string; mrp_type: string; action: Action; order_qty: number; order_by_date: string | null; min_new: number; max_new: number; risk_cost_yr: number; health: string; equipment: string | null }>(`
    select m.material_no, m.description, m.category, m.unit, m.criticality, m.stock, m.lt_p90, m.unit_price, m.price_source, m.health, m.mrp_type,
           p.action, p.order_qty, p.order_by_date, p.min_new, p.max_new, p.risk_cost_yr,
           ${hasTable("material_location") ? "(select group_concat(distinct l.equipment) from material_location l where l.material_no = m.material_no)" : "null"} as equipment
    from materials m join policy p using (material_no)`);

  const list: Task[] = [];
  for (const m of rows) {
    const t = ta.get(m.material_no);
    const gap = t && t.status !== "READY" ? t : null;
    const reorder = m.action === "REORDER";
    const odd = unusual.get(m.material_no) ?? null;
    const price = m.price_source === "po" ? m.unit_price : null;
    const equipment = m.equipment ? m.equipment.split(",") : [];
    const machines = Array.from(new Set(equipment.map((e) => PREFIX_MACHINE[e.split("-")[0]]).filter(Boolean)));
    const base = { id: String(m.material_no), material_no: m.material_no, description: m.description, category: m.category, unit: m.unit, criticality: m.criticality, stock: m.stock, lead_time: m.lt_p90, risk: m.risk_cost_yr, ta: !!t, mrp: m.mrp_type, ta_gap: gap ? gap.gap : 0, ta_routine: gap ? gap.routine : 0, equipment: equipment.slice(0, 6), machines, codes: codes.get(m.material_no)?.codes ?? [], section: codes.get(m.material_no)?.section ?? ("static" as Section), unusual: odd };

    if (gap || reorder) {
      // Rushing only what the turnaround is missing; everything else on an order goes at normal speed.
      const qty = Math.ceil((gap?.status === "TOO_LATE" ? gap.gap : Math.max(gap ? gap.gap : 0, reorder ? m.order_qty : 0)) - 1e-9);
      const donor = donors.get(m.material_no) ?? null;
      const twin = donor && donor.surplus >= qty ? donor : null;
      const fromTa: Urgency | null = !gap ? null : gap.status === "TOO_LATE" ? "late" : gap.status === "ORDER_NOW" ? "now" : gap.status === "PLAN" ? "month" : "later";
      const fromPolicy: Urgency | null = !reorder ? null : isTopCrit(m.criticality) ? (m.health === "STOCKOUT" ? "now" : "month") : "later";
      const urgency = ([fromTa, fromPolicy] as (Urgency | null)[]).filter((u): u is Urgency => !!u).sort((a, b) => URGENCY_RANK[a] - URGENCY_RANK[b])[0];
      const order_by = gap?.status === "TOO_LATE" || !reorder ? gap!.order_by : (m.order_by_date ?? today);
      list.push({ ...base, kind: twin ? "twin" : gap?.status === "TOO_LATE" ? "expedite" : "order", urgency, target: gap ? gap.need_total : m.min_new, qty, order_by, days_left: daysBetween(today, order_by), value: price != null ? qty * price : null, twin });
    } else if (m.action === "REDUCE") {
      const qty = Math.max(0, m.stock - m.max_new);
      list.push({ ...base, kind: "reduce", urgency: "house", target: m.max_new, qty, order_by: null, days_left: null, value: price != null ? qty * price : null, twin: null });
    } else if (m.action === "DISPOSE_REVIEW") {
      list.push({ ...base, kind: "dispose", urgency: "house", target: 0, qty: m.stock, order_by: null, days_left: null, value: price != null ? m.stock * price : null, twin: null });
    } else if (m.action === "MONITOR" || odd) {
      list.push({ ...base, kind: "watch", urgency: "later", target: m.min_new, qty: 0, order_by: null, days_left: null, value: null, twin: null });
    }
  }
  list.sort(
    (a, b) =>
      URGENCY_RANK[a.urgency] - URGENCY_RANK[b.urgency] ||
      CRIT_RANK[a.criticality] - CRIT_RANK[b.criticality] ||
      KIND_RANK[a.kind] - KIND_RANK[b.kind] ||
      (a.days_left ?? 9999) - (b.days_left ?? 9999) ||
      b.risk - a.risk ||
      (b.value ?? 0) - (a.value ?? 0),
  );
  taskCache = list;
  return list;
}

export function taskFor(materialNo: number): Task | null {
  return tasks().find((t) => t.material_no === materialNo) ?? null;
}

export function taskCounts() {
  const list = tasks();
  return {
    total: list.length,
    urgent: list.filter((t) => t.urgency === "late" || t.urgency === "now").length,
    late: list.filter((t) => t.urgency === "late").length,
    toBuy: list.filter((t) => t.kind === "order" || t.kind === "expedite").reduce((a, t) => a + (t.value ?? 0), 0),
    buy: buySplit(list),
    toFree: list.filter((t) => t.kind === "reduce" || t.kind === "dispose").reduce((a, t) => a + (t.value ?? 0), 0),
  };
}

/** Parts whose recent routine use jumped well above their own normal, for the forecast page. */
/** Non Stock parts on the buying list, with the Min and Max they would need as Stock Items. */
export function moveToStock() {
  const limits = new Map(all<{ material_no: number; min_new: number; max_new: number }>("select material_no, min_new, max_new from policy").map((p) => [p.material_no, p]));
  return tasks()
    .filter((t) => buyBasis(t) === "ahead" || buyBasis(t) === "job")
    .map((t) => ({ material_no: t.material_no, description: t.description, criticality: t.criticality, basis: buyBasis(t), min_new: limits.get(t.material_no)?.min_new ?? 0, max_new: limits.get(t.material_no)?.max_new ?? 0, qty: t.qty, unit: t.unit, value: t.value }));
}

export function unusualUse(limit = 8) {
  const list = tasks().filter((t) => t.unusual);
  const sorted = [...list].sort((a, b) => CRIT_RANK[a.criticality] - CRIT_RANK[b.criticality] || b.unusual!.ratio - a.unusual!.ratio);
  return { total: list.length, items: sorted.slice(0, limit) };
}

/** New Min/Max per part, in the fields SAP MM17 mass maintenance expects. */
export function mrpChanges() {
  return all<{ material_no: number; description: string; criticality: string; min_cur: number; max_cur: number; safety_stock: number; rop: number; min_new: number; max_new: number; action: string }>(`
    select m.material_no, m.description, m.criticality, m.min_cur, m.max_cur, p.safety_stock, p.rop, p.min_new, p.max_new, p.action
    from materials m join policy p using (material_no)
    where m.mrp_type = 'Stock Item' and (round(p.min_new) != round(m.min_cur) or round(p.max_new) != round(m.max_cur))
    order by m.material_no`);
}

/* ------------------------------------------------------------- parts list */

export type PartRow = {
  material_no: number;
  description: string;
  category: string;
  unit: string;
  criticality: Crit;
  stock: number;
  min_cur: number;
  max_cur: number;
  min_new: number;
  max_new: number;
  action: Action;
  order_qty: number;
  order_by_date: string | null;
  reason: string;
  health: string;
  unit_price: number | null;
  price_source: string;
  p_move: number;
  cold_start: number;
};

export type PartFilter = {
  category?: string;
  action?: string;
  crit?: string;
  health?: string;
  q?: string;
  twin?: boolean;
  limit?: number;
  offset?: number;
};

export function parts(f: PartFilter) {
  const where: string[] = [];
  const args: unknown[] = [];
  if (f.category) {
    where.push("m.category = ?");
    args.push(f.category);
  }
  if (f.action && f.action !== "ALL") {
    where.push("p.action = ?");
    args.push(f.action);
  }
  if (f.crit) {
    const cs = f.crit.split(",").filter((c) => (CRITS as string[]).includes(c));
    if (cs.length) {
      where.push(`m.criticality in (${cs.map(() => "?").join(",")})`);
      args.push(...cs);
    }
  }
  if (f.health) {
    where.push("m.health = ?");
    args.push(f.health);
  }
  if (f.twin) {
    where.push(`m.material_no in (
      select t.material_no from twins t
      join twins d on d.group_id = t.group_id and d.material_no != t.material_no and d.role = 'DONOR'
      join materials dm on dm.material_no = d.material_no
      where t.role = 'SHORT' and dm.stock > dm.max_cur)`);
  }
  if (f.q && f.q.trim()) {
    const q = f.q.trim();
    if (/^\d+$/.test(q)) {
      where.push("cast(m.material_no as text) like ?");
      args.push(`%${q}%`);
    } else {
      for (const w of q.split(/\s+/).slice(0, 4)) {
        where.push("m.description like ?");
        args.push(`%${w}%`);
      }
    }
  }
  const w = where.length ? `where ${where.join(" and ")}` : "";
  const limit = Math.min(200, Math.max(1, f.limit ?? 40));
  const offset = Math.max(0, f.offset ?? 0);
  const rows = all<PartRow>(
    `select m.material_no, m.description, m.category, m.unit, m.criticality, m.stock, m.min_cur, m.max_cur,
            p.min_new, p.max_new, p.action, p.order_qty, p.order_by_date, p.reason, m.health, m.unit_price, m.price_source,
            f.p_move, f.cold_start
     from materials m join policy p using (material_no) join forecast f using (material_no)
     ${w}
     order by case m.criticality when 'A' then 0 when 'B' then 1 when 'C' then 2 else 3 end,
              case p.action when 'REORDER' then 0 when 'MONITOR' then 1 when 'REDUCE' then 2 when 'DISPOSE_REVIEW' then 3 else 4 end,
              p.risk_cost_yr desc, m.stock_value desc
     limit ? offset ?`,
    ...args,
    limit,
    offset,
  );
  const total = one<{ n: number }>(
    `select count(*) as n from materials m join policy p using (material_no) ${w}`,
    ...args,
  )!.n;
  return { rows, total };
}

export function actionSummary() {
  return all<{ action: Action; n: number; value: number | null }>(`
    select p.action, count(*) as n,
      sum(case when m.price_source = 'po' then
        case p.action when 'REORDER' then p.order_qty * m.unit_price
                      when 'REDUCE' then max(m.stock - p.max_new, 0) * m.unit_price
                      when 'DISPOSE_REVIEW' then m.stock * m.unit_price
                      else 0 end end) as value
    from policy p join materials m using (material_no)
    group by p.action`);
}

/* ------------------------------------------------------------- part detail */

export function part(id: number) {
  const m = one<Record<string, unknown> & PartRow & {
    n_funcloc: number;
    installed_qty: number;
    stock_value: number | null;
    lt_p50: number;
    lt_p90: number;
    lt_source: string;
    main_supplier: string | null;
    qty_issued_17m: number;
    months_active: number;
    last_issue: string | null;
    demand_class: string;
    trust_score: number;
    trust_flags: string;
    mrp_type: string;
  }>(
    `select m.*, p.min_new, p.max_new, p.action, p.order_qty, p.order_by_date, p.reason, p.service_level, p.safety_stock, p.rop,
            p.hold_cost_yr, p.risk_cost_yr, f.p_move, f.mean_qty, f.q50, f.q90, f.q95, f.base_qty, f.event_qty, f.ltd_mean, f.ltd_var,
            f.cold_start, f.drivers
     from materials m join policy p using (material_no) join forecast f using (material_no)
     where m.material_no = ?`,
    id,
  );
  if (!m) return null;
  const history = all<{ month: string; qty: number; qty_ta: number }>(
    "select ym as month, qty, qty_event as qty_ta from consumption_monthly where material_no = ? order by ym",
    id,
  );
  const months = all<{ month: string }>("select distinct ym as month from consumption_monthly order by ym").map((r) => r.month);
  const ta = one<{ ta_qty_last: number; gap: number }>("select ta_qty_last, gap from ta_kit where material_no = ?", id) ?? null;
  const twins = all<{ material_no: number; role: string; stock: number; max_cur: number; description: string }>(
    `select t2.material_no, t2.role, m.stock, m.max_cur, m.description from twins t1
     join twins t2 on t2.group_id = t1.group_id and t2.material_no != t1.material_no
     join materials m on m.material_no = t2.material_no where t1.material_no = ?`,
    id,
  );
  const equipment = hasTable("material_location")
    ? all<{ equipment: string }>("select distinct equipment from material_location where material_no = ?", id).map((r) => r.equipment)
    : [];
  return { m, history, months, ta, twins, equipment, standby: standbyOf(equipment), asOf: asOf(), taDate: defaultTa() };
}

let unitNames: Set<string> | null = null;

/** Units that come as a lettered pair (PP-128A with PP-128C): one can run while the other waits for a part. */
function standbyOf(equipment: string[]): { unit: string; standby: string[] }[] {
  if (!hasTable("material_location")) return [];
  if (!unitNames) unitNames = new Set(all<{ equipment: string }>("select distinct equipment from material_location").map((r) => r.equipment));
  const out: { unit: string; standby: string[] }[] = [];
  for (const e of equipment) {
    const m = /^(.*\d)([A-Z])$/.exec(e);
    if (!m) continue;
    const sibs = Array.from(unitNames).filter((u) => u !== e && u.startsWith(m[1]) && /^[A-Z]$/.test(u.slice(m[1].length)));
    if (sibs.length) out.push({ unit: e, standby: sibs.sort() });
  }
  return out;
}

export function searchParts(q: string, limit = 8) {
  return parts({ q, limit }).rows.map((r) => ({
    material_no: r.material_no,
    description: r.description,
    criticality: r.criticality,
    action: r.action,
    stock: r.stock,
    unit: r.unit,
  }));
}

/* ------------------------------------------------------------- the answer for one part */

export type PartAnswer = {
  material_no: number;
  unit: string;
  have: number;
  likely6: number;
  bad6: number;
  chance6: number;
  forecastEnds: string;
  /** Null when the last turnaround did not use this part. */
  ta: { date: string; need: number; routine: number; total: number; left: number; gap: number } | null;
  lead: number;
  orderBy: string | null;
  /** The last safe day for the turnaround alone. Normal use can make the order due earlier. */
  taOrderBy: string | null;
  arrives: string | null;
  asOf: string;
  aging: {
    lastUsed: string | null;
    slowOn: string | null;
    deadOn: string | null;
    /** Months the stock lasts at normal use. Null when there is no regular use. */
    coverMonths: number | null;
    runsOutOn: string | null;
    shelf: ShelfLife | null;
    /** Stock would outlast its typical shelf life at normal use. */
    outlasts: boolean;
  };
  value: number | null;
};

/** How long stock lasts at normal use, in months. Very slow use counts as no regular use. */
function coverOf(stock: number, base: number): number | null {
  const perMonth = base / 6;
  if (stock <= 0 || perMonth <= 0 || stock / perMonth > 240) return null;
  return stock / perMonth;
}

/** Have, need, do what, by when: the one answer every page opens for a part. */
export function partAnswer(id: number): PartAnswer | null {
  const m = one<{ material_no: number; unit: string; stock: number; category: string; lt_p90: number; last_issue: string | null; q50: number; q95: number; p_move: number; base_qty: number; order_by_date: string | null; action: Action; unit_price: number | null; price_source: string }>(
    `select m.material_no, m.unit, m.stock, m.category, m.lt_p90, m.last_issue, f.q50, f.q95, f.p_move, f.base_qty, p.order_by_date, p.action, m.unit_price, m.price_source
     from materials m join policy p using (material_no) join forecast f using (material_no) where m.material_no = ?`,
    id,
  );
  if (!m) return null;
  const today = asOf();
  const r = readiness().parts.find((p) => p.material_no === id) ?? null;
  const task = taskFor(id);
  const buying = task && (task.kind === "order" || task.kind === "expedite");
  const orderBy = buying ? task.order_by : null;
  const cover = coverOf(m.stock, m.base_qty);
  const shelf = SHELF_LIFE[m.category] ?? null;
  return {
    material_no: m.material_no,
    unit: m.unit,
    have: m.stock,
    likely6: m.q50,
    bad6: m.q95,
    chance6: m.p_move,
    forecastEnds: addDays(today, Number(meta().forecast_horizon_days ?? 180)),
    ta: r ? { date: defaultTa(), need: r.need, routine: r.routine, total: r.need_total, left: Math.max(0, r.stock - r.routine), gap: r.gap } : null,
    lead: m.lt_p90,
    orderBy,
    taOrderBy: r && r.gap > 0 ? r.order_by : null,
    // A missed last safe day cannot be the order date: the earliest an order can go out is today.
    arrives: orderBy ? addDays(orderBy > today ? orderBy : today, Math.round(m.lt_p90)) : null,
    asOf: today,
    aging: {
      lastUsed: m.last_issue,
      slowOn: m.last_issue ? addDays(m.last_issue, 180) : null,
      deadOn: m.last_issue ? addDays(m.last_issue, 365) : null,
      coverMonths: cover,
      runsOutOn: cover != null ? addDays(today, Math.round(cover * 30.4)) : null,
      shelf,
      outlasts: !!shelf && m.stock > 0 && (cover == null || cover > shelf.months),
    },
    value: task?.value ?? null,
  };
}

/* ------------------------------------------------------------- what we need */

export type NeedRow = { material_no: number; description: string; category: string; criticality: Crit; unit: string; have: number; likely6: number; bad6: number; ta: number; total: number; gap: number; order_qty: number; order_by: string | null; order_now: boolean; late: boolean; no_history: boolean; chance: number };

/** Every part we expect to use, with what we have against what we will need. This is the forecast's actual answer. */
export function needList() {
  const kit = new Map(readiness().parts.map((p) => [p.material_no, p]));
  // Quantity and date come from the task, so this list says the same thing as the part page and the To do board.
  const today = asOf();
  const buying = new Map(tasks().filter((t) => t.kind === "order" || t.kind === "expedite").map((t) => [t.material_no, t]));
  const rows = all<{ material_no: number; description: string; category: string; criticality: Crit; unit: string; stock: number; q50: number; q95: number; p_move: number; cold_start: number }>(`
    select m.material_no, m.description, m.category, m.criticality, m.unit, m.stock, f.q50, f.q95, f.p_move, f.cold_start
    from materials m join forecast f using (material_no)
    where f.p_move >= 0.5 or m.material_no in (select material_no from ta_kit)`);
  const list: NeedRow[] = rows.map((r) => {
    const k = kit.get(r.material_no);
    const task = buying.get(r.material_no);
    const order_by = task?.order_by ?? (k && k.gap > 0 ? k.order_by : null);
    return { material_no: r.material_no, description: r.description, category: r.category, criticality: r.criticality, unit: r.unit, have: r.stock, likely6: r.q50, bad6: r.q95, ta: k?.need ?? 0, total: k?.need_total ?? 0, gap: k?.gap ?? 0, order_qty: task?.qty ?? k?.gap ?? 0, order_by, order_now: !!order_by && order_by <= today, late: k?.status === "TOO_LATE", no_history: !!r.cold_start, chance: r.p_move };
  });
  list.sort((a, b) => CRIT_RANK[a.criticality] - CRIT_RANK[b.criticality] || (b.gap > 0 ? 1 : 0) - (a.gap > 0 ? 1 : 0) || Math.max(0, b.likely6 - b.have) - Math.max(0, a.likely6 - a.have));
  const likely = list.filter((r) => r.chance >= 0.5);
  return {
    list,
    likely: likely.length,
    shortLikely: likely.filter((r) => r.likely6 > r.have).length,
    shortBad: likely.filter((r) => r.bad6 > r.have).length,
    kit: kit.size,
    shortKit: list.filter((r) => r.gap > 0).length,
    // Parts with under a 1 in 2 chance still get used, so the total to expect is the sum of the chances, checked against recent use.
    expected: Math.round(one<{ v: number }>("select sum(p_move) as v from forecast")!.v),
    usedLately: one<{ n: number }>("select count(distinct material_no) as n from consumption_monthly where ym >= ? and qty > qty_event", addDays(asOf(), -182).slice(0, 7))!.n,
    forecastEnds: addDays(asOf(), Number(meta().forecast_horizon_days ?? 180)),
    taDate: defaultTa(),
  };
}

/* ------------------------------------------------------------- aging ahead */

/** Parts about to cross into slow or dead stock, and stock that would outlast its typical shelf life at normal use. */
export function agingAhead() {
  const today = asOf();
  const soon = one<{ slow: number; dead: number }>(
    `select sum(julianday(?) - julianday(last_issue) between 90 and 180) as slow, sum(julianday(?) - julianday(last_issue) between 270 and 365) as dead
     from materials where mrp_type = 'Stock Item' and stock > 0`,
    today,
    today,
  )!;
  const rows = all<{ material_no: number; description: string; criticality: Crit; stock: number; unit: string; stock_value: number | null; last_issue: string | null; category: string; base_qty: number; action: Action; price_source: string }>(`
    select m.material_no, m.description, m.criticality, m.stock, m.unit, m.stock_value, m.last_issue, m.category, f.base_qty, p.action, m.price_source
    from materials m join forecast f using (material_no) join policy p using (material_no)
    where m.mrp_type = 'Stock Item' and m.stock > 0`);
  const over = rows.filter((r) => {
    const shelf = SHELF_LIFE[r.category];
    if (!shelf) return false;
    const cover = coverOf(r.stock, r.base_qty);
    return cover == null || cover > shelf.months;
  });
  const priced = over.filter((r) => r.price_source === "po" && r.stock_value);
  return {
    soon,
    outlast: { n: over.length, value: priced.reduce((a, r) => a + (r.stock_value ?? 0), 0), rows: [...priced].sort((a, b) => (b.stock_value ?? 0) - (a.stock_value ?? 0)).slice(0, 10) },
  };
}

/* ------------------------------------------------------------- stock health */

export function health() {
  const byHealth = all<{ health: string; n: number; value: number | null }>(`
    select health, count(*) as n, sum(case when price_source = 'po' then stock_value end) as value
    from materials where mrp_type = 'Stock Item' group by health`);
  const quadrant = all<{ critical: number; state: string; n: number; value: number | null }>(`
    select criticality in ('A','B') as critical,
           case when health in ('STOCKOUT','BELOW_MIN') then 'short'
                when health in ('OVER_MAX','NON_MOVING','OBSOLETE_CANDIDATE') then 'excess' else 'ok' end as state,
           count(*) as n, sum(case when price_source = 'po' then stock_value end) as value
    from materials where mrp_type = 'Stock Item' group by 1, 2`);
  const topOver = all<{ material_no: number; description: string; criticality: Crit; unit: string; stock: number; max_cur: number; over_value: number; action: Action }>(`
    select m.material_no, m.description, m.criticality, m.unit, m.stock, m.max_cur,
           (m.stock - m.max_cur) * m.unit_price as over_value, p.action
    from materials m join policy p using (material_no)
    where m.price_source = 'po' and m.stock > m.max_cur and m.mrp_type = 'Stock Item'
    order by over_value desc limit 10`);
  const aging = all<{ bucket: string; n: number; value: number | null }>(
    `select case
        when last_issue is null then 'never'
        when julianday(?) - julianday(last_issue) <= 90 then 'lt3'
        when julianday(?) - julianday(last_issue) <= 180 then '3to6'
        when julianday(?) - julianday(last_issue) <= 365 then '6to12'
        else 'gt12' end as bucket,
        count(*) as n, sum(case when price_source = 'po' then stock_value end) as value
     from materials where mrp_type = 'Stock Item' and stock > 0 group by 1`,
    asOf(),
    asOf(),
    asOf(),
  );
  const totals = one<{ n: number; value: number; over_value: number }>(`
    select count(*) as n, sum(case when price_source = 'po' then stock_value end) as value,
           sum(case when price_source = 'po' and stock > max_cur then (stock - max_cur) * unit_price end) as over_value
    from materials where mrp_type = 'Stock Item'`)!;
  // Stock Items only: a Non Stock part is bought per job, so an empty shelf is its normal state, not a gap.
  const critZero = one<{ n: number }>(`select count(*) as n from materials where health = 'STOCKOUT' and criticality in ('A','B') and mrp_type = 'Stock Item'`)!.n;
  const critBelowMin = one<{ n: number }>(`select count(*) as n from materials where health = 'BELOW_MIN' and criticality in ('A','B') and mrp_type = 'Stock Item'`)!.n;
  const priced = one<{ n: number; all: number }>(`select sum(price_source = 'po') as n, count(*) as "all" from materials`)!;
  const stale = (where: string, limit: number) =>
    all<{ material_no: number; description: string; criticality: Crit; stock: number; unit: string; stock_value: number | null; last_issue: string | null; action: Action }>(
      `select m.material_no, m.description, m.criticality, m.stock, m.unit, m.stock_value, m.last_issue, p.action
       from materials m join policy p using (material_no)
       where m.mrp_type = 'Stock Item' and m.stock > 0 and m.price_source = 'po' and ${where}
       order by m.stock_value desc limit ?`,
      asOf(),
      limit,
    );
  const slowing = stale("m.last_issue is not null and julianday(?) - julianday(m.last_issue) between 180 and 365", 10);
  const dead = stale("(m.last_issue is null or julianday(?) - julianday(m.last_issue) > 365)", 10);
  return {
    slowing,
    dead,
    byHealth,
    quadrant,
    topOver,
    aging,
    totals,
    critZero,
    critBelowMin,
    priced,
    pctSpendAboveMax: fact("pct_spend_above_max"),
    spendTotal: fact("spend_idr_total"),
  };
}

/* ------------------------------------------------------------- demand outlook */

export function outlook() {
  const months = all<{ month: string; parts: number; parts_ta: number; lines: number }>(
    "select ym as month, count(*) as parts, sum(qty_event > 0) as parts_ta, sum(n_lines) as lines from consumption_monthly group by ym order by ym",
  );
  const likely = all<{ criticality: Crit; band: string; n: number }>(`
    select m.criticality, case when f.p_move >= 0.7 then 'very' when f.p_move >= 0.3 then 'maybe' else 'unlikely' end as band, count(*) as n
    from forecast f join materials m using (material_no) group by 1, 2`);
  const hidden = all<{ material_no: number; description: string; criticality: Crit; n_funcloc: number; p_move: number; stock: number; unit: string; lt_p90: number }>(`
    select m.material_no, m.description, m.criticality, m.n_funcloc, f.p_move, m.stock, m.unit, m.lt_p90
    from forecast f join materials m using (material_no)
    where f.cold_start = 1 and m.stock = 0 and m.criticality in ('A','B')
    order by f.p_move desc, m.n_funcloc desc limit 8`);
  const sum = one<{ likely: number; likely_cold: number; event_driven: number; base_driven: number; cold_total: number }>(`
    select sum(p_move >= 0.5) as likely, sum(p_move >= 0.5 and cold_start = 1) as likely_cold,
           sum(event_qty > base_qty and event_qty > 0) as event_driven, sum(base_qty >= event_qty and base_qty > 0.05) as base_driven,
           sum(cold_start) as cold_total
    from forecast`)!;
  const patterns = all<{ demand_class: string; n: number }>("select demand_class, count(*) as n from materials group by 1");
  return { months, likely, hidden, sum, patterns, proof: proof() };
}

/* ------------------------------------------------------------- scenarios */

export type FrontierPoint = {
  scenario: string;
  budget_idr: number;
  exp_risk_cost: number;
  fill_rate_A: number;
  fill_rate_B: number;
  n_parts_funded: number;
};

/**
 * The engine's budget-vs-risk frontier (Monte Carlo lead-time demand, in pipeline/build_db.py).
 * The app moves along it instead of re-simulating, so every number matches the engine.
 * Risk is a relative index (no downtime cost in the data), so it is shown against today.
 */
export function scenario(budget?: number, holding?: number) {
  const pts = all<FrontierPoint>("select * from frontier order by budget_idr");
  const curve = pts.filter((p) => p.scenario === "frontier");
  const named = (n: string) => pts.find((p) => p.scenario === n)!;
  const current = named("current");
  const optimized = named("optimized");
  const lean = named("lean");
  const h = holding ?? Number(meta().holding_rate);
  let pick: FrontierPoint = optimized;
  if (budget != null && Number.isFinite(budget)) {
    pick = curve.reduce((best, p) => (Math.abs(p.budget_idr - budget) < Math.abs(best.budget_idr - budget) ? p : best), curve[0]);
  }
  return {
    curve,
    current,
    optimized,
    lean,
    pick,
    holding: h,
    riskVsToday: pick.exp_risk_cost / current.exp_risk_cost,
    budgetVsToday: pick.budget_idr / current.budget_idr,
    holdCost: pick.budget_idr * h,
    holdCostToday: current.budget_idr * h,
  };
}

/* ------------------------------------------------------------- data trust */

export function trust() {
  const dq = all<{ issue: string; n: number; example: string; impact: string }>("select * from dq_issues");
  const backtest = all<{ method: string; auc_all: number | null; auc_cold: number | null; coverage_q95: number | null; note: string }>(
    "select * from backtest",
  );
  const levels = one<{ high: number; medium: number; low: number }>(`
    select sum(trust_score >= 0.7) as high, sum(trust_score >= 0.4 and trust_score < 0.7) as medium, sum(trust_score < 0.4) as low
    from materials where stock > 0 or qty_issued_17m > 0`)!;
  const countFirst = all<{ material_no: number; description: string; criticality: Crit; stock: number; unit: string; stock_value: number | null; trust_score: number }>(`
    select material_no, description, criticality, stock, unit, stock_value, trust_score
    from materials where trust_score < 0.5 and price_source = 'po' and stock > 0
    order by stock_value desc limit 6`);
  return { dq, backtest, levels, countFirst, meta: meta(), proof: proof() };
}

/** Headline forecast proof, read from the backtest table. */
export function proof() {
  const bt = all<{ method: string; auc_all: number | null; auc_cold: number | null; coverage_q95: number | null; note: string }>("select method, auc_all, auc_cold, coverage_q95, note from backtest");
  const get = (m: string) => bt.find((b) => b.method === m);
  const rolling = get("engine_rolling_mean");
  const naiveMatch = rolling?.note.match(/AUC naive ([0-9.]+)/);
  const sba = get("sba");
  const holdout = get("lgbm_2part");
  return {
    engine: rolling?.auc_all ?? holdout?.auc_all ?? null,
    baseline: naiveMatch ? Number(naiveMatch[1]) : get("naive_mean")?.auc_all ?? null,
    engineCold: rolling?.auc_cold ?? holdout?.auc_cold ?? null,
    // The classic formula was only scored on the single hold-out test, so it is set against the engine on that same test.
    engineColdHoldout: sba?.auc_cold != null ? holdout?.auc_cold ?? null : null,
    classicCold: sba?.auc_cold ?? null,
    /** Share of the parts that were actually used whose 90-day use stayed within the high (q95) estimate. */
    coverUsed: rolling?.coverage_q95 ?? null,
  };
}

/* ------------------------------------------------------------- stock library */

export type Shelf = { category: string; parts: number; empty: number; low: number; ok: number; over: number; idle: number; critical_empty: number; value: number; used: number };

/** One shelf per category, and the four stages a part moves through. */
export function stockLibrary() {
  const shelves = all<Shelf>(`
    select category, count(*) as parts,
      sum(health = 'STOCKOUT') as empty, sum(health = 'BELOW_MIN') as low, sum(health = 'OK') as ok, sum(health = 'OVER_MAX') as over,
      sum(health in ('NON_MOVING','OBSOLETE_CANDIDATE')) as idle,
      sum(stock = 0 and criticality in ('A','B')) as critical_empty,
      coalesce(sum(case when price_source = 'po' then stock_value end), 0) as value,
      sum(qty_issued_17m > 0) as used
    from materials group by category order by category`);
  const base = one<{ suppliers: number; supplied: number; lead: number; on_shelf: number; on_shelf_priced: number; shelf_value: number; used: number; parts: number }>(`
    select
      (select count(distinct main_supplier) from materials where main_supplier is not null) as suppliers,
      (select count(*) from materials where main_supplier is not null) as supplied,
      (select round(avg(lt_p50)) from materials where lt_source = 'material') as lead,
      (select count(*) from materials where stock > 0) as on_shelf,
      (select count(*) from materials where stock > 0 and price_source = 'po') as on_shelf_priced,
      (select coalesce(sum(stock_value), 0) from materials where stock > 0 and price_source = 'po') as shelf_value,
      (select count(*) from materials where qty_issued_17m > 0) as used,
      (select count(*) from materials) as parts`)!;
  // "To order" is the To do board's buying list (turnaround gaps and reorders merged), so both pages show one number.
  const buy = tasks().filter((t) => t.kind === "order" || t.kind === "expedite");
  const flow = { ...base, reorder: buy.length, reorder_priced: buy.filter((t) => t.value != null).length, reorder_value: buy.reduce((a, t) => a + (t.value ?? 0), 0) };
  const suppliers = all<{ name: string; parts: number; lead: number | null }>(`
    select main_supplier as name, count(*) as parts, round(avg(lt_p50)) as lead
    from materials where main_supplier is not null group by 1 order by 2 desc limit 5`);
  return { shelves, flow, suppliers };
}

/** Replay of real demand against each policy, plus the strict forecast variant, for the proof tiles. */
export function modelProof() {
  const policy = hasTable("policy_backtest")
    ? all<{ policy: string; fill_units_AB: number; stockout_days_AB: number; avg_inv_idr: number; avg_inv_idr_po: number }>("select policy, fill_units_AB, stockout_days_AB, avg_inv_idr, avg_inv_idr_po from policy_backtest")
    : [];
  const strict = one<{ auc_all: number | null; auc_cold: number | null }>("select auc_all, auc_cold from backtest where method = 'engine_strict_mean'") ?? null;
  return { policy, strict };
}

/* ------------------------------------------------------------- maintenance ahead */

export type PmMonth = { month: string; jobs: number; major: number; equipment: number };
export type PmMajor = { month: string; due: string; fl: string; fl_desc: string; task: string; criticality: string | null; cycle_text: string; parts: number; parts_low: number };
export type NotifCode = { code: string; notices: number; emergency: number };

/** When planned jobs fall due until the turnaround, and where breakdown notices came from lately. */
export function maintenanceAhead() {
  if (!hasTable("pm_month")) return null;
  return {
    months: all<PmMonth>("select month, jobs, major, equipment from pm_month order by month"),
    major: all<PmMajor>("select month, due, fl, fl_desc, task, criticality, cycle_text, parts, parts_low from pm_major order by parts_low desc, parts desc, due"),
    notices: all<NotifCode>("select code, notices, emergency from notif_by_code where code <> 'OTHER' order by notices desc limit 6"),
  };
}

/* ------------------------------------------------------------- month-by-month replay */

export type ReplayPlan = { policy: string; parts: number; fill_units: number; fill_lines: number; stockout_days: number; avg_inv_idr: number; avg_inv_idr_po: number };
export type ReplayMonth = { policy: string; month: string; requested: number; served: number; stockout_days: number; avg_inv_idr: number };
export type ReplayRefresh = { month: string; changed: number; min_up: number; min_down: number; critical: number; value_max_idr: number };
export type ReplayPart = { material_no: number; description: string; criticality: Crit; unit: string; requested: number; served_today: number; served_sparekit: number; use: number[]; today: number[]; sparekit: number[]; mins: number[]; maxs: number[]; min_today: number; max_today: number; short_today: number[][]; short_sparekit: number[][]; orders_today: number[][]; orders_sparekit: number[][]; chance: number[]; use_in_delivery: number[]; delivery: number[] };
type ReplayPartData = Omit<ReplayPart, "material_no" | "description" | "criticality" | "unit" | "requested" | "served_today" | "served_sparekit">;
export type ReplayPartName = { material_no: number; description: string; criticality: Crit };
export type ReplayProof = {
  today: ReplayPlan; classic: ReplayPlan; sparekit: ReplayPlan; once: ReplayPlan; shelfToday: ReplayPlan; shelfSparekit: ReplayPlan; strict: ReplayPlan | null;
  allParts: { fill_units_AB: number; avg_inv_idr: number } | null;
  /** Stock value in the replay covers every Stock Item, not only the parts whose availability is measured. */
  stocked: number;
  /** Average stock on the measured parts alone, today's limits against Sparekit's. */
  measured: { today: number; sparekit: number };
};

/** The replay on the parts meant to be on the shelf, plus the wider run that also stocks Non Stock parts. */
export function replayProof(): ReplayProof | null {
  if (!hasTable("replay_policy")) return null;
  const plans = all<ReplayPlan>("select policy, parts, fill_units, fill_lines, stockout_days, avg_inv_idr, avg_inv_idr_po from replay_policy");
  const by = (k: string) => plans.find((p) => p.policy === k) ?? null;
  const allParts = one<{ fill_units_AB: number; avg_inv_idr: number }>("select fill_units_AB, avg_inv_idr from policy_backtest where policy = 'policy_partpulse_lean'") ?? null;
  return { today: by("today")!, classic: by("classic")!, sparekit: by("sparekit")!, once: by("sparekit_once")!, shelfToday: by("today_shelf")!, shelfSparekit: by("sparekit_shelf")!, strict: by("sparekit_strict"), allParts, stocked: stockedCount(), measured: measuredStock() };
}

let measuredCache: { today: number; sparekit: number } | null = null;
/** Daily stock of each measured part, priced and averaged. The database is read-only, so this is worked out once. */
function measuredStock() {
  if (measuredCache) return measuredCache;
  const mean = (a: number[]) => (a.length ? a.reduce((x, y) => x + y, 0) / a.length : 0);
  const rows = all<{ data: string; price: number | null }>("select r.data, m.unit_price as price from replay_parts r join materials m using (material_no)");
  measuredCache = rows.reduce(
    (acc, r) => {
      const d = JSON.parse(r.data) as { today: number[]; sparekit: number[] };
      const price = r.price ?? 0;
      return { today: acc.today + mean(d.today) * price, sparekit: acc.sparekit + mean(d.sparekit) * price };
    },
    { today: 0, sparekit: 0 },
  );
  return measuredCache;
}

const stockedCount = () => one<{ n: number }>("select count(*) as n from materials where mrp_type = 'Stock Item'")?.n ?? 0;

export function replayView() {
  const proof = replayProof();
  if (!proof) return null;
  const months = all<ReplayMonth>("select policy, month, requested, served, stockout_days, avg_inv_idr from replay_monthly where policy in ('today', 'classic', 'sparekit') order by month");
  const refresh = all<ReplayRefresh>("select month, changed, min_up, min_down, critical, value_max_idr from replay_refresh order by month");
  const rows = all<{ material_no: number; description: string; criticality: Crit; unit: string; requested: number; served_today: number; served_sparekit: number; data: string }>(`
    select r.material_no, m.description, m.criticality, m.unit, r.requested, r.served_today, r.served_sparekit, r.data
    from replay_parts r join materials m using (material_no)
    where m.price_source = 'po' and r.served_today < r.requested * 0.7 and r.served_sparekit >= r.requested * 0.95`);
  const moves = (p: ReplayPart) => p.mins.slice(1).map((v, i) => v - p.mins[i]);
  // Examples that show the idea: short under today's limits, covered under ours, a Min that went both ways and stayed in scale with real use.
  const parts = rows
    .map(({ data, ...r }): ReplayPart => ({ ...r, ...(JSON.parse(data) as ReplayPartData) }))
    .filter((p) => moves(p).some((d) => d > 0) && moves(p).some((d) => d < 0) && Math.max(...p.mins) <= p.requested && Math.min(...p.mins) > 0 && Math.max(...p.sparekit) <= p.requested * 1.2)
    .sort((a, b) => Number(b.min_today > 0 && b.requested <= 1000) - Number(a.min_today > 0 && a.requested <= 1000) || moves(b).filter(Boolean).length - moves(a).filter(Boolean).length || a.served_today / a.requested - b.served_today / b.requested);
  const names = all<ReplayPartName>("select r.material_no, m.description, m.criticality from replay_parts r join materials m using (material_no) order by m.description");
  return { proof, months, refresh, parts, names };
}

/** One part's replay, or null when the part is outside it (only critical stocked parts used in those months are in). */
export function replayPart(id: number): ReplayPart | null {
  if (!hasTable("replay_parts")) return null;
  const row = one<{ material_no: number; description: string; criticality: Crit; unit: string; requested: number; served_today: number; served_sparekit: number; data: string }>(
    "select r.material_no, m.description, m.criticality, m.unit, r.requested, r.served_today, r.served_sparekit, r.data from replay_parts r join materials m using (material_no) where r.material_no = ?",
    id,
  );
  if (!row) return null;
  const { data, ...r } = row;
  return { ...r, ...(JSON.parse(data) as ReplayPartData) };
}

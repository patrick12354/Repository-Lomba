// Shared by server and client. Plain-language formatting lives here so every page says things the same way.

import { bi, isId, numLocale, t } from "./i18n";

export type Crit = "A" | "B" | "C" | "S";
/** Organiser's order, highest first: A > B > C > S (S = special, lowest). */
export const CRITS: Crit[] = ["A", "B", "C", "S"];
export const CRIT_RANK: Record<Crit, number> = { A: 0, B: 1, C: 2, S: 3 };
/** The two classes treated as critical everywhere in the app. */
export const TOP_CRITS: Crit[] = ["A", "B"];
export const isTopCrit = (c: Crit) => c === "A" || c === "B";

export type Status = "act" | "plan" | "watch" | "ready" | "excess" | "idle" | "twin";

export const STATUS_LABEL: Record<Status, string> = bi({
  act: ["Act now", "Segera tindak"],
  plan: ["Plan", "Rencanakan"],
  watch: ["Watch", "Pantau"],
  ready: ["Ready", "Siap"],
  excess: ["Too much", "Berlebih"],
  idle: ["Not used", "Tidak terpakai"],
  twin: ["Use duplicate part", "Pakai suku cadang kembar"],
});

export type Action = "REORDER" | "MAINTAIN" | "REDUCE" | "MONITOR" | "DISPOSE_REVIEW";

export const ACTION_VERB: Record<Action, string> = bi({
  REORDER: ["Order", "Pesan"],
  REDUCE: ["Stop buying", "Hentikan pembelian"],
  DISPOSE_REVIEW: ["Still needed?", "Masih diperlukan?"],
  MONITOR: ["Keep an eye on", "Pantau"],
  MAINTAIN: ["Keep", "Pertahankan"],
});

/** Task kinds in words, for text written on the server. */
export const TASK_VERB: Record<string, string> = bi({
  expedite: ["Rush order", "Percepat pesanan"],
  order: ["Order", "Pesan"],
  twin: ["Move from a duplicate part", "Pindahkan dari suku cadang kembar"],
  reduce: ["Stop buying", "Hentikan pembelian"],
  dispose: ["Check if still needed", "Periksa apakah masih diperlukan"],
  watch: ["Keep an eye on", "Pantau"],
});

/** SAP unit codes in words: [one, many]. */
const UNIT_WORDS: Record<string, [string, string]> = {
  EA: ["piece", "pieces"],
  SET: ["set", "sets"],
  ASS: ["assembly", "assemblies"],
  KG: ["kg", "kg"],
  LG: ["length", "lengths"],
  RL: ["roll", "rolls"],
  M: ["metre", "metres"],
  L: ["litre", "litres"],
  CAN: ["can", "cans"],
  SHT: ["sheet", "sheets"],
};

/** Indonesian does not mark the plural, so one word per unit. */
const UNIT_WORDS_ID: Record<string, string> = {
  EA: "buah",
  SET: "set",
  ASS: "rakitan",
  KG: "kg",
  LG: "batang",
  RL: "gulung",
  M: "meter",
  L: "liter",
  CAN: "kaleng",
  SHT: "lembar",
};

export function unitName(unit: string | null | undefined, n = 2): string {
  if (!unit) return "";
  if (isId()) return UNIT_WORDS_ID[unit.toUpperCase()] ?? unit.toLowerCase();
  const w = UNIT_WORDS[unit.toUpperCase()];
  return w ? (n === 1 ? w[0] : w[1]) : unit.toLowerCase();
}

/** "9 SET" becomes "9 sets". */
export function amount(v: number | null | undefined, unit: string | null | undefined): string {
  const text = qty(v, unit);
  return `${text} ${unitName(unit, text === "1" ? 1 : 2)}`.trim();
}

/** The one-line reason the engine stores, without the planning codes. */
export function plainReason(reason: string | null | undefined): string {
  if (!reason) return "";
  if (isId()) return plainReasonId(reason);
  return reason
    .replace(/^REORDER\b/, "Order")
    .replace(/^REDUCE\b/, "Stop buying")
    .replace(/^DISPOSE_REVIEW\b/, "Check if still needed")
    .replace(/^MONITOR\b/, "Keep an eye on")
    .replace(/^MAINTAIN\b/, "Keep")
    .replace(/\b([ABCS])-critical\b/g, "criticality $1")
    .replace(/\bFLs?\b/g, "locations")
    .replace(/P\(use in 180d\)/g, "chance of use in 6 months")
    .replace(/in 180d\b/g, "in 6 months")
    .replace(/lead time P90 (\d+)d/g, "slow-case delivery $1 days")
    .replace(/\bnew ROP\b/g, "new reorder level")
    .replace(/\bnew Max\b/g, "new Max limit")
    .replace(/\bPM due in 90d\b/g, "planned maintenance jobs due in 90 days")
    .replace(/\bin last 90d\b/g, "in the last 90 days")
    .replace(/\bPM\b/g, "planned maintenance")
    .replace(/notifications/g, "breakdown notices")
    .replace(/\bRaise PR by\b/g, "Raise a purchase request by")
    .replace(/\bno new PR\b/g, "no new purchase request")
    .replace(/\btwin materials\b/g, "duplicate parts")
    .replace(/\btop driver: current Min\b/g, "biggest clue: its current Min")
    .replace(/\b(\d[\d,.]*) EA\b/g, "$1 pieces")
    .replace(/\b(\d[\d,.]*) SET\b/g, "$1 sets")
    .replace(/ on this dataset/g, "")
    .replace(/\bRp ([\d.,]+) M\b/g, "Rp $1 million")
    .replace(/\bRp ([\d.,]+) B\b/g, "Rp $1 billion");
}

/** The engine's reason, rewritten clause by clause into Indonesian. Numbers keep the engine's values. */
function plainReasonId(reason: string): string {
  const u = (code: string) => UNIT_WORDS_ID[code.toUpperCase()] ?? code.toLowerCase();
  const n = (v: string) => v.replace(/\./g, ",");
  const date = (d: string) => shortDate(d, true);
  const money = (v: string, scale: string) => `Rp${n(v)} ${scale === "B" ? "miliar" : "juta"}`;
  let s = reason;
  const head: [RegExp, (...m: string[]) => string][] = [
    [/^REORDER ([\d.,]+) (\w+):\s*/, (_, q, un) => `Pesan ${q} ${u(un)}: `],
    [/^REDUCE:\s*/, () => "Hentikan pembelian: "],
    [/^DISPOSE_REVIEW:\s*/, () => "Periksa apakah masih diperlukan: "],
    [/^MONITOR:\s*/, () => "Pantau: "],
    [/^MAINTAIN:\s*/, () => "Pertahankan: "],
  ];
  for (const [re, f] of head) s = s.replace(re, f as (...a: string[]) => string);
  const rules: [RegExp, (...m: string[]) => string][] = [
    [/\b([ABCS])-critical\b/g, (_, c) => `kekritisan ${c}`],
    [/installed on (\d+) FLs?/g, (_, k) => `terpasang di ${k} lokasi`],
    [/(\d+) notifications in last (\d+)d/g, (_, k, d) => `${k} laporan kerusakan dalam ${d} hari terakhir`],
    [/P\(use in 180d\) only (\d+)%/g, (_, p) => `peluang terpakai dalam 6 bulan hanya ${p}%`],
    [/\(P\(use in 180d\) (\d+)%\)/g, (_, p) => `(peluang terpakai dalam 6 bulan ${p}%)`],
    [/P\(use in 180d\) (\d+)%/g, (_, p) => `peluang terpakai dalam 6 bulan ${p}%`],
    [/lead time P90 (\d+)d/g, (_, d) => `waktu kirim skenario lambat ${d} hari`],
    [/stock ([\d.,]+) vs new ROP ([\d.,]+)/g, (_, a, b) => `stok ${a}, titik pesan ulang baru ${b}`],
    [/next turnaround needs ([\d.,]+) (\w+)/g, (_, q, un) => `turnaround berikutnya butuh ${q} ${u(un)}`],
    [/Next turnaround needs ([\d.,]+) (\w+): raise that PR by (\d{4}-\d{2}-\d{2})/g, (_, q, un, d) => `Turnaround berikutnya butuh ${q} ${u(un)}: ajukan permintaan pembeliannya paling lambat ${date(d)}`],
    [/upcoming work on its FLs: (\d+) PM due in 90d \((\d+) major\), (\d+) open notifications/g, (_, pm, mj, op) => `pekerjaan mendatang di lokasinya: ${pm} pemeliharaan terencana dalam 90 hari (${mj} besar), ${op} laporan kerusakan terbuka`],
    [/Raise PR by (\d{4}-\d{2}-\d{2})/g, (_, d) => `Ajukan permintaan pembelian paling lambat ${date(d)}`],
    [/stock ([\d.,]+) exceeds new Max ([\d.,]+) by ([\d.,]+) (\w+) \(~Rp ([\d.,]+) ([MB]) on this dataset\)/g, (_, a, b, c, un, v, sc) => `stok ${a} melebihi Max baru ${b} sebanyak ${c} ${u(un)} (sekitar ${money(v, sc)})`],
    [/Stop replenishing; check twin materials before buying again/g, () => "Hentikan pengisian ulang; periksa suku cadang kembar sebelum membeli lagi"],
    [/stock ([\d.,]+) is above new Max ([\d.,]+) (\w+), but the part is active/g, (_, a, b, un) => `stok ${a} di atas Max baru ${b} ${u(un)}, tetapi suku cadang ini masih aktif`],
    [/no new PR, let consumption draw it down/g, () => "tidak perlu permintaan pembelian baru, biarkan pemakaian menurunkannya"],
    [/stock ([\d.,]+) within new Min-Max ([\d.,]+)-([\d.,]+) (\w+)/g, (_, a, b, c, un) => `stok ${a} berada dalam Min–Max baru ${b}–${c} ${u(un)}`],
    [/no issue in (\d+) months and none of its (\d+) FLs? has PM or notifications/g, (_, mo, k) => `tidak ada pengeluaran selama ${mo} bulan dan tidak satu pun dari ${k} lokasinya memiliki pemeliharaan terencana atau laporan kerusakan`],
    [/([\d.,]+) (\w+) on shelf \(~Rp ([\d.,]+) ([MB]) on this dataset\)/g, (_, q, un, v, sc) => `${q} ${u(un)} di rak (sekitar ${money(v, sc)})`],
    [/\btop driver: current Min\b/g, () => "petunjuk terbesar: Min saat ini"],
  ];
  for (const [re, f] of rules) s = s.replace(re, f as (...a: string[]) => string);
  return s;
}

export const ACTION_STATUS: Record<Action, Status> = {
  REORDER: "plan",
  REDUCE: "excess",
  DISPOSE_REVIEW: "idle",
  MONITOR: "watch",
  MAINTAIN: "ready",
};

export type TaStatus = "TOO_LATE" | "ORDER_NOW" | "PLAN" | "LATER" | "READY";

const taLabel = (en: string, id: string) => ({ get label() { return t(en, id); } });

export const TA_STATUS: Record<TaStatus, { status: Status; label: string }> = {
  TOO_LATE: { status: "act", ...taLabel("Too late for a normal order", "Terlambat untuk pemesanan biasa") },
  ORDER_NOW: { status: "act", ...taLabel("Order this week", "Pesan minggu ini") },
  PLAN: { status: "plan", ...taLabel("Order this month", "Pesan bulan ini") },
  LATER: { status: "watch", ...taLabel("Order later", "Pesan nanti") },
  READY: { status: "ready", ...taLabel("Ready", "Siap") },
};

export const CRIT_NAME: Record<Crit, string> = bi({
  A: ["A, most critical", "A, paling kritis"],
  B: ["B, critical", "B, kritis"],
  C: ["C, less critical", "C, kurang kritis"],
  S: ["S, least critical", "S, paling tidak kritis"],
});

const nf = (digits: number) => new Intl.NumberFormat(numLocale(), { maximumFractionDigits: digits });
const NA = () => t("n/a", "t/a");

/** Rupiah with the scale spelled out: "M" reads as miliar in Indonesia, so never abbreviate it. */
export function rp(v: number | null | undefined, opts: { compact?: boolean } = {}): string {
  if (v == null || !Number.isFinite(v)) return NA();
  const a = Math.abs(v);
  const sign = v < 0 ? "−" : "";
  // Indonesian spelling writes Rp against the number: Rp1,2 miliar.
  const pre = `${sign}Rp${isId() ? "" : " "}`;
  if (a >= 1e9) return `${pre}${a >= 1e11 ? nf(0).format(a / 1e9) : nf(1).format(a / 1e9)} ${t("billion", "miliar")}`;
  if (a >= 1e6) return `${pre}${nf(0).format(a / 1e6)} ${t("million", "juta")}`;
  if (a >= 1e3 && opts.compact) return `${pre}${nf(0).format(a / 1e3)} ${t("thousand", "ribu")}`;
  return `${pre}${nf(0).format(a)}`;
}

export function num(v: number | null | undefined, digits = 0): string {
  if (v == null || !Number.isFinite(v)) return NA();
  return nf(digits).format(v);
}

/** Quantities: whole numbers for countable units, one decimal otherwise. */
export function qty(v: number | null | undefined, unit?: string | null): string {
  if (v == null || !Number.isFinite(v)) return NA();
  const frac = unit && ["M", "KG", "L", "M2", "M3", "LTR", "KGM"].includes(unit.toUpperCase());
  const r = frac ? v : Math.ceil(v - 1e-9);
  return num(r === 0 ? 0 : r, frac ? 1 : 0);
}

export function pct(v: number | null | undefined, digits = 0): string {
  if (v == null || !Number.isFinite(v)) return NA();
  const s = (v * 100).toFixed(digits);
  return `${isId() ? s.replace(".", ",") : s}%`;
}

const MONTHS_EN = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const MONTHS_ID = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"];
const months = () => (isId() ? MONTHS_ID : MONTHS_EN);

export function parseDate(s: string): Date {
  const [y, m, d] = s.split("-").map(Number);
  return new Date(Date.UTC(y, m - 1, d));
}

export function isoDate(d: Date): string {
  return d.toISOString().slice(0, 10);
}

export function addDays(s: string, n: number): string {
  const d = parseDate(s);
  d.setUTCDate(d.getUTCDate() + n);
  return isoDate(d);
}

export function daysBetween(from: string, to: string): number {
  return Math.round((parseDate(to).getTime() - parseDate(from).getTime()) / 86400000);
}

export function shortDate(s: string | null | undefined, withYear = false): string {
  if (!s) return NA();
  const d = parseDate(s);
  return `${d.getUTCDate()} ${months()[d.getUTCMonth()]}${withYear ? ` ${d.getUTCFullYear()}` : ""}`;
}

export function monthLabel(ym: string): string {
  const [y, m] = ym.split("-").map(Number);
  return `${months()[m - 1]} ${String(y).slice(2)}`;
}

/** "8 days left", "today", "12 days late". */
export function daysLeft(n: number): string {
  if (isId()) {
    if (n === 0) return "hari ini";
    return n > 0 ? `${n} hari lagi` : `terlambat ${-n} hari`;
  }
  if (n === 0) return "today";
  if (n > 0) return `${n} day${n === 1 ? "" : "s"} left`;
  return `${-n} day${n === -1 ? "" : "s"} late`;
}

export function daysShort(n: number): string {
  if (isId()) {
    if (n === 0) return "Hari ini";
    return n > 0 ? `${n} hr` : `telat ${-n} hr`;
  }
  if (n === 0) return "Today";
  return n > 0 ? `${n}d` : `${-n}d late`;
}

/** 0.73 → "7 in 10". */
export function chance(p: number): string {
  const k = Math.max(0, Math.min(10, Math.round(p * 10)));
  if (k === 0) return t("under 1 in 10", "kurang dari 1 dari 10");
  if (k === 10) return t("almost certain", "hampir pasti");
  return t(`${k} in 10`, `${k} dari 10`);
}

/** Turn "GASKET,SPIRAL WOUND,6IN,300#" into "Gasket, spiral wound 6in 300#". */
export function partName(desc: string | null | undefined): string {
  if (!desc) return t("Unnamed part", "Suku cadang tanpa nama");
  const parts = desc.replace(/\s+(for|of|with|to)\s*$/i, "").split(",").map((p) => p.trim()).filter(Boolean);
  if (!parts.length) return desc;
  const lower = (s: string) =>
    s
      .split(" ")
      .map((w) => (/\d/.test(w) || w.length <= 2 ? w : w.toLowerCase()))
      .join(" ");
  const head = lower(parts[0]);
  const first = head.charAt(0).toUpperCase() + head.slice(1);
  const rest = parts.slice(1).map(lower);
  if (!rest.length) return first;
  return `${first}, ${rest.join(" ")}`;
}

/** "GASKET,RING 4IN,..." is a ring gasket: the first word after the category. */
export function subtypeOf(desc: string | null | undefined): string {
  return (desc?.split(",")[1] ?? "").trim().split(/\s+/)[0]?.toUpperCase() || "OTHER";
}

/** The part's own name without the words its group already says: "Gasket, ring 4IN 300#" in the Ring group is "4IN 300#". */
export function shortPartName(desc: string | null | undefined, subtype: string | null): string {
  const full = partName(desc);
  let rest = full.replace(/^[^,]+,\s*/, "");
  if (subtype) rest = rest.replace(new RegExp(`^${subtype.replace(/[^\w-]/g, "")}\\b[\\s,]*`, "i"), "");
  return rest.trim() || full;
}

export function categoryName(cat: string | null | undefined): string {
  if (!cat) return t("Other", "Lainnya");
  const s = cat.toLowerCase();
  return s.charAt(0).toUpperCase() + s.slice(1);
}

export function cn(...c: Array<string | false | null | undefined>): string {
  return c.filter(Boolean).join(" ");
}

const SUBTYPE_WORDS: Record<string, string> = bi({ SW: ["Spiral wound", "Spiral wound"], "O-RING": ["O-ring", "O-ring"], OTHER: ["Other", "Lainnya"] });
export const subtypeName = (s: string) => SUBTYPE_WORDS[s] ?? categoryName(s);

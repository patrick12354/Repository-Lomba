/**
 * Why a planner turns a suggestion down. Each reason maps to one planned change in the engine. The prototype records
 * the reason but pipeline/ does not read it yet (plant-wide phase). Shared by the board, the API and the AI sorter.
 */
import { t } from "./i18n";

/** Wording follows the language when read; the code never changes. */
const reason = <C extends string>(code: C, label: [string, string], hint: [string, string], rule: [string, string]) => ({
  code,
  get label() {
    return t(label[0], label[1]);
  },
  get hint() {
    return t(hint[0], hint[1]);
  },
  get rule() {
    return t(rule[0], rule[1]);
  },
});

export const REASONS = [
  reason(
    "needed",
    ["Needed for planned work", "Dibutuhkan untuk pekerjaan terencana"],
    ["Keep the stock: a job, overhaul or turnaround will use it.", "Pertahankan stoknya: akan dipakai untuk pekerjaan, overhaul, atau turnaround."],
    ["Stock on these parts is protected from release while planned work is open on their machines.", "Stok suku cadang ini tidak akan dilepas selama masih ada pekerjaan terencana yang terbuka pada mesinnya."],
  ),
  reason(
    "covered",
    ["Already covered", "Sudah tercukupi"],
    ["Another store, a contract or an open order already covers it.", "Sudah dipenuhi oleh gudang lain, kontrak, atau pesanan yang masih berjalan."],
    ["These parts pause for 90 days, and the cover is counted as stock.", "Suku cadang ini ditunda selama 90 hari, dan cadangan tersebut dihitung sebagai stok."],
  ),
  reason(
    "qty",
    ["Quantity is off", "Jumlahnya tidak tepat"],
    ["The part is right, the amount is not.", "Suku cadangnya benar, tetapi jumlahnya keliru."],
    ["The target for this part type moves one step down for buying and one step up for releasing.", "Target untuk jenis suku cadang ini turun satu tingkat untuk pembelian dan naik satu tingkat untuk pelepasan."],
  ),
  reason(
    "retired",
    ["Machine retired or replaced", "Mesin sudah tidak dipakai atau diganti"],
    ["The equipment it fits is gone.", "Peralatan yang memakainya sudah tidak ada."],
    ["These parts stop being bought and go to disposal review.", "Suku cadang ini tidak dibeli lagi dan masuk ke tinjauan penghapusan."],
  ),
  reason(
    "data",
    ["Records are wrong", "Datanya salah"],
    ["The shelf count, Min, Max or price is not right.", "Jumlah di rak, Min, Max, atau harganya tidak benar."],
    ["These parts go to the count list first, and no order goes out until the count is in.", "Suku cadang ini masuk daftar penghitungan dulu, dan tidak ada pesanan yang dikirim sebelum hasil hitungnya masuk."],
  ),
] as const;

export type ReasonCode = (typeof REASONS)[number]["code"];

export const REASON_CODES = REASONS.map((r) => r.code) as readonly string[];

export function reasonOf(code: string | null | undefined) {
  return REASONS.find((r) => r.code === code) ?? null;
}

/** Keyword sorter: the fallback when AI is off, and a check on what the AI returns. */
export function guessReason(text: string): ReasonCode | null {
  const t = text.toLowerCase();
  const has = (...w: string[]) => w.some((x) => t.includes(x));
  if (has("retir", "replaced", "decommission", "scrap", "no longer", "removed", "obsolete")) return "retired";
  if (has("too many", "too much", "too high", "too low", "fewer", "half", "quantity", "qty", "amount", "kebanyakan", "kurang banyak")) return "qty";
  if (has("count", "wrong", "record", "error", "mistake", "price", "data", "salah")) return "data";
  if (has("contract", "consign", "other store", "another store", "warehouse", "open order", "already ordered", "covered", "vendor stock")) return "covered";
  if (has("overhaul", "turnaround", "shutdown", "planned", "job", "work order", "keep", "need", "insurance", "spare")) return "needed";
  return null;
}

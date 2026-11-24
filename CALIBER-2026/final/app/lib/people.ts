import type { Task, TaskKind } from "./data";
import { bi, t } from "./i18n";

/**
 * The demo team, and who owns what. Safe to import on the client and the server, so the board
 * and the API apply the same rules. Every address is a stand-in that delivers to one real inbox.
 */
export const DEMO_INBOX = "raphael.adikara@gmail.com";
export const DEMO_PASSWORD = "sparekit2026";

export type Role = "planner" | "procurement" | "warehouse" | "maintenance" | "finance";
export type Section = "rotating" | "static" | "instrument";
export type Person = { id: string; name: string; title: string; role: Role; section?: Section; login: string; email: string; does: string };

/** Title and duty are [English, Indonesian] and follow the language when read. */
const person = (id: string, name: string, title: [string, string], role: Role, does: [string, string], section?: Section): Person => ({
  id,
  name,
  get title() {
    return t(title[0], title[1]);
  },
  role,
  section,
  get does() {
    return t(does[0], does[1]);
  },
  login: `${name.split(" ")[0].toLowerCase()}@sparekit.demo`,
  email: DEMO_INBOX,
});

export const PEOPLE: Person[] = [
  person("planner", "Nadia Putri", ["Inventory Planner", "Perencana Persediaan"], "planner", ["Approves or rejects every recommendation", "Menyetujui atau menolak setiap rekomendasi"]),
  person("buyer", "Bima Santoso", ["Procurement Buyer", "Staf Pengadaan"], "procurement", ["Runs approved orders and expedites", "Menjalankan pesanan yang disetujui dan mempercepat pengiriman"]),
  person("warehouse", "Citra Lestari", ["Warehouse Lead", "Kepala Gudang"], "warehouse", ["Moves stock between twin parts", "Memindahkan stok antarsuku cadang kembar"]),
  person("rotating", "Dimas Prakoso", ["Maintenance Planner, Rotating", "Perencana Pemeliharaan, Rotating"], "maintenance", ["Pumps, compressors, turbines", "Pompa, kompresor, turbin"], "rotating"),
  person("static", "Eka Wulandari", ["Maintenance Planner, Static", "Perencana Pemeliharaan, Statis"], "maintenance", ["Furnaces, exchangers, vessels, piping", "Tungku, penukar panas, bejana, perpipaan"], "static"),
  person("instrument", "Fajar Hidayat", ["Maintenance Planner, Instrument", "Perencana Pemeliharaan, Instrumen"], "maintenance", ["Control valves and instruments", "Katup kendali dan instrumen"], "instrument"),
  person("finance", "Gita Maharani", ["Finance Lead", "Kepala Keuangan"], "finance", ["Reviews disposals and stock policy", "Meninjau penghapusan stok dan kebijakan persediaan"]),
];

/**
 * What a purchase rests on. A Non Stock part is bought per job, so only a turnaround need is a job we already know of.
 * Buying one ahead on the forecast means changing it to a Stock Item first, and the plant decides that.
 */
export type BuyBasis = "stocked" | "job" | "ahead";
export function buyBasis(t: Pick<Task, "kind" | "mrp" | "ta_gap">): BuyBasis | null {
  if (t.kind !== "order" && t.kind !== "expedite") return null;
  if (t.mrp === "Stock Item") return "stocked";
  return t.ta_gap > 0 ? "job" : "ahead";
}
export function buyNote(basis: BuyBasis | null) {
  if (basis === "job") return t("Bought per job today. This is for the turnaround.", "Saat ini dibeli per pekerjaan. Ini untuk turnaround.");
  if (basis === "ahead") return t("Bought per job today. Move it to Stock first to hold it.", "Saat ini dibeli per pekerjaan. Pindahkan ke Stock dulu agar bisa disimpan.");
  return null;
}
export function buySplit(list: Pick<Task, "kind" | "mrp" | "ta_gap" | "value">[]) {
  const out = { stocked: { n: 0, value: 0 }, job: { n: 0, value: 0 }, ahead: { n: 0, value: 0 } };
  for (const x of list) {
    const b = buyBasis(x);
    if (!b) continue;
    out[b].n++;
    out[b].value += x.value ?? 0;
  }
  return out;
}

export const personById = (id: string | null | undefined) => PEOPLE.find((p) => p.id === id) ?? null;
export const firstName = (p: Pick<Person, "name">) => p.name.split(" ")[0];

export const SECTION_NAME: Record<Section, string> = bi({ rotating: ["Rotating", "Rotating"], static: ["Static", "Statis"], instrument: ["Instrument & valves", "Instrumen & katup"] });
export const SECTIONS = Object.keys(SECTION_NAME) as Section[];

/** Equipment codes taken from the functional location, in plain words. */
export const CODE_NAME: Record<string, string> = bi({
  PP: ["Pumps", "Pompa"],
  KC: ["Compressors", "Kompresor"],
  KT: ["Turbines", "Turbin"],
  BF: ["Furnaces", "Tungku"],
  HE: ["Heat exchangers", "Penukar panas"],
  VD: ["Vessels and drums", "Bejana dan drum"],
  CL: ["Columns", "Kolom"],
  PIPE: ["Piping lines", "Jalur perpipaan"],
  FCV: ["Flow control valves", "Katup kendali aliran"],
  PCV: ["Pressure control valves", "Katup kendali tekanan"],
  LCV: ["Level control valves", "Katup kendali level"],
  TCV: ["Temperature control valves", "Katup kendali suhu"],
  PRV: ["Pressure relief valves", "Katup pelepas tekanan"],
  SDV: ["Shutdown valves", "Katup penghenti darurat"],
  MOV: ["Motor-operated valves", "Katup bermotor"],
  ROF: ["Restriction orifices", "Orifis pembatas"],
  PIT: ["Pressure transmitters", "Transmiter tekanan"],
  FIT: ["Flow transmitters", "Transmiter aliran"],
  LIT: ["Level transmitters", "Transmiter level"],
  TIT: ["Temperature transmitters", "Transmiter suhu"],
  DPT: ["Differential pressure transmitters", "Transmiter beda tekanan"],
  PGI: ["Pressure gauges", "Pengukur tekanan"],
  TEL: ["Temperature elements", "Elemen suhu"],
  JBX: ["Junction boxes", "Kotak sambungan"],
  OTHER: ["Other locations", "Lokasi lain"],
});

const STATIC_CODES = ["BF", "HE", "VD", "CL", "PIPE", "OTHER"];
const ROTATING_CODES = ["PP", "KC", "KT"];
export function codeSection(code: string): Section {
  return ROTATING_CODES.includes(code) ? "rotating" : STATIC_CODES.includes(code) ? "static" : "instrument";
}

export type Stage = "todo" | "approved" | "in_progress" | "done" | "rejected";
type Routed = Pick<Task, "kind" | "section" | "urgency">;

const KIND_OWNER: Record<Exclude<TaskKind, "watch">, string> = { expedite: "buyer", order: "buyer", twin: "warehouse", reduce: "planner", dispose: "finance" };

/** Who carries the task out once it is decided. */
export function ownerOf(t: Routed): Person {
  return personById(t.kind === "watch" ? t.section : KIND_OWNER[t.kind])!;
}

/** The planner decides. The owner runs it after that. Watch tasks belong to their section from the start. */
export function canMove(p: Person | null, t: Routed, from: Stage, to: Stage): boolean {
  if (!p || from === to) return false;
  if (t.kind === "watch") return ownerOf(t).id === p.id;
  const deciding = from === "todo" || to === "todo" || from === "rejected" || to === "rejected";
  return deciding ? p.role === "planner" : ownerOf(t).id === p.id;
}

/** The part of the board this person actually works on. */
export function isMine(p: Person, t: Routed, stage: Stage): boolean {
  if (p.role === "planner") return true; // decides everything and follows it through
  if (p.role === "maintenance") return t.section === p.section && (t.kind === "watch" || t.urgency === "late" || t.urgency === "now");
  return ownerOf(t).id === p.id && stage !== "todo" && stage !== "rejected";
}

export const SUPPLIER = "supplier";

/** The obvious person to write to about this task. A buyer writes to the supplier, everyone else to the next person in the chain. */
export function recipientFor(me: Person, t: Routed): string {
  const owner = ownerOf(t);
  if (me.role === "procurement" && (t.kind === "expedite" || t.kind === "order")) return SUPPLIER;
  if (me.role === "planner") return t.kind === "reduce" ? "buyer" : owner.id;
  return "planner";
}

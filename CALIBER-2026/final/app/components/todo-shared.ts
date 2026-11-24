import { ArrowLeftRight, Archive, Eye, OctagonAlert, Package, ShoppingCart, type LucideIcon } from "@/components/icons";
import type { Task, TaskKind, Urgency } from "@/lib/data";
import type { Decision, useDecisions } from "@/lib/decisions";
import { amount, qty, type Status } from "@/lib/format";
import { t as tx } from "@/lib/i18n";

/** A field that reads in the current language: `...w("label", "Ready", "Siap")`. */
const w = <K extends string>(key: K, en: string, id: string) => ({ get [key]() { return tx(en, id); } }) as Record<K, string>;

export type TaskStatus = Decision | "todo";

export const STATUSES: { code: TaskStatus; label: string; dot: string; hint: string; who: string }[] = [
  { code: "todo", ...w("label", "To decide", "Perlu diputuskan"), dot: "bg-ink-4", ...w("hint", "Nothing left to decide here.", "Tidak ada lagi yang perlu diputuskan di sini."), ...w("who", "Waiting for Nadia, the planner", "Menunggu Nadia, perencana") },
  { code: "approved", ...w("label", "Approved", "Disetujui"), dot: "bg-watch", ...w("hint", "Press Approve on a card to send it here.", "Tekan Setujui pada kartu untuk memindahkannya ke sini."), ...w("who", "Waiting for the person who runs it", "Menunggu pelaksananya") },
  { code: "in_progress", ...w("label", "In progress", "Sedang berjalan"), dot: "bg-plan", ...w("hint", "Press Start once the request is out.", "Tekan Mulai setelah permintaannya dikirim."), ...w("who", "Ordered or being moved", "Sudah dipesan atau sedang dipindahkan") },
  { code: "done", ...w("label", "Done", "Selesai"), dot: "bg-ready", ...w("hint", "Press Mark done when the part has arrived or the job is closed.", "Tekan Tandai selesai saat suku cadang sudah tiba atau pekerjaan sudah ditutup."), ...w("who", "Arrived or closed", "Sudah tiba atau ditutup") },
  { code: "rejected", ...w("label", "Rejected", "Ditolak"), dot: "bg-idle", ...w("hint", "Nothing rejected.", "Tidak ada yang ditolak."), ...w("who", "Not going ahead", "Tidak dilanjutkan") },
];

export const URGENCIES: { code: Urgency; label: string; dot: string }[] = [
  { code: "late", ...w("label", "Too late for a normal order", "Terlambat untuk pemesanan biasa"), dot: "bg-act" },
  { code: "now", ...w("label", "Order this week", "Pesan minggu ini"), dot: "bg-act" },
  { code: "month", ...w("label", "Order this month", "Pesan bulan ini"), dot: "bg-plan" },
  { code: "later", ...w("label", "Order later", "Pesan nanti"), dot: "bg-watch" },
  { code: "house", ...w("label", "No rush, tidy up", "Tidak mendesak, rapikan"), dot: "bg-idle" },
];

type KindInfo = {
  name: string;
  status: Status;
  icon: LucideIcon;
  ink: string;
  dot: string;
  label: (t: Task) => string;
};

export const KIND: Record<TaskKind, KindInfo> = {
  expedite: { ...w("name", "Rush order", "Percepat pesanan"), status: "act", icon: OctagonAlert, ink: "text-act-ink", dot: "bg-act", label: (t) => tx(`Rush ${amount(t.qty, t.unit)}`, `Percepat ${amount(t.qty, t.unit)}`) },
  order: { ...w("name", "Order", "Pesan"), status: "plan", icon: ShoppingCart, ink: "text-plan-ink", dot: "bg-plan", label: (t) => tx(`Order ${amount(t.qty, t.unit)}`, `Pesan ${amount(t.qty, t.unit)}`) },
  twin: { ...w("name", "Use a duplicate part", "Pakai suku cadang kembar"), status: "twin", icon: ArrowLeftRight, ink: "text-twin-ink", dot: "bg-twin", label: (t) => tx(`Move ${amount(t.qty, t.unit)}`, `Pindahkan ${amount(t.qty, t.unit)}`) },
  watch: { ...w("name", "Keep an eye on", "Pantau"), status: "watch", icon: Eye, ink: "text-watch-ink", dot: "bg-watch", label: () => tx("Keep an eye on", "Pantau") },
  reduce: { ...w("name", "Stop buying", "Hentikan pembelian"), status: "excess", icon: Package, ink: "text-excess-ink", dot: "bg-excess", label: (t) => tx(`Stop buying, ${qty(t.qty, t.unit)} extra`, `Hentikan pembelian, lebih ${qty(t.qty, t.unit)}`) },
  dispose: { ...w("name", "Check if still needed", "Periksa apakah masih diperlukan"), status: "idle", icon: Archive, ink: "text-idle-ink", dot: "bg-idle", label: () => tx("Check if still needed", "Periksa apakah masih diperlukan") },
};
export const KINDS = Object.keys(KIND) as TaskKind[];

export function approveLabel(t: Task): string {
  return t.kind === "expedite"
    ? tx(`Rush ${amount(t.qty, t.unit)}`, `Percepat ${amount(t.qty, t.unit)}`)
    : t.kind === "order"
      ? tx(`Order ${amount(t.qty, t.unit)}`, `Pesan ${amount(t.qty, t.unit)}`)
      : t.kind === "twin"
        ? tx("Move from the duplicate part", "Pindahkan dari suku cadang kembar")
        : t.kind === "reduce"
          ? tx("Stop buying", "Hentikan pembelian")
          : t.kind === "dispose"
            ? tx("Send to review", "Kirim untuk ditinjau")
            : tx("Keep watching", "Terus pantau");
}

/** The one step that comes next, in the words of a button. */
export function nextStep(t: Task, s: TaskStatus): { to: TaskStatus; label: string } | null {
  if (s === "todo") return { to: "approved", label: t.kind === "watch" ? tx("Keep watching", "Terus pantau") : tx("Approve", "Setujui") };
  if (s === "approved") return { to: "in_progress", label: tx("Start", "Mulai") };
  if (s === "in_progress") return { to: "done", label: tx("Mark done", "Tandai selesai") };
  return null;
}

export function daysText(d: number): string {
  if (d < 0) return tx(`${-d} ${-d === 1 ? "day" : "days"} ago`, `${-d} hari yang lalu`);
  if (d === 0) return tx("today", "hari ini");
  return tx(`${d} ${d === 1 ? "day" : "days"} left`, `${d} hari lagi`);
}

/** Seed notes the demo opens with, so the learning panel reads in the chosen language too. */
const SEED_NOTES: Record<string, string> = {
  "Overhaul of the same pump set is planned next quarter, keep it.": "Overhaul set pompa yang sama dijadwalkan kuartal depan, jadi stoknya dipertahankan.",
  "Shelf count looks wrong, someone should check bin first.": "Jumlah di rak tampaknya salah, raknya perlu dicek dulu.",
  "Already on an open order from the central store.": "Sudah ada pesanan berjalan dari gudang pusat.",
};
export const noteText = (note: string) => tx(note, SEED_NOTES[note] ?? note);

/** Activity lines are stored in English; this shows them in the current language. */
export function activityText(detail: string): string {
  const fixed: Record<string, string> = { Approved: "Disetujui", Started: "Dimulai", "Marked done": "Ditandai selesai", Rejected: "Ditolak", "Moved back to To decide": "Dikembalikan ke Perlu diputuskan" };
  if (fixed[detail]) return tx(detail, fixed[detail]);
  const rej = detail.match(/^Rejected: ([\s\S]*)$/);
  if (rej) return tx(detail, `Ditolak: ${noteText(rej[1])}`);
  const mail = detail.match(/^Emailed ([^:]+): ([\s\S]*)$/);
  if (mail) return tx(detail, `Mengirim surel ke ${mail[1]}: ${mail[2]}`);
  return detail;
}

export function setStatus(d: ReturnType<typeof useDecisions>, t: Task, s: TaskStatus, why?: { note?: string; reason?: string; reason_source?: string }) {
  d.set(t.id, s === "todo" ? null : s, { material_no: t.material_no, action: t.kind, ...why });
}

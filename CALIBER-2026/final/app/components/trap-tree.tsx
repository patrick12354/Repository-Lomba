"use client";

import { useState } from "react";
import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import { ChevronRight } from "lucide-react";
import { Bug, CalendarX2, CheckCircle2, Clock3, Copy, Receipt, Scale, Tag as TagIcon, Unlink, type LucideIcon } from "@/components/icons";
import { cn, num } from "@/lib/format";
import { t } from "@/lib/i18n";

const TRAP_ICON: [RegExp, LucideIcon][] = [
  [/duplicate/i, Copy],
  [/cycle/i, Clock3],
  [/required start/i, CalendarX2],
  [/negative lead/i, Clock3],
  [/unit price/i, Receipt],
  [/price/i, TagIcon],
  [/linked/i, Unlink],
  [/ledger/i, Scale],
];

type Trap = { issue: string; n: number; example: string; impact: string };

/** The issue names as the pipeline stores them, in plain words. */
type Plain = { title: string; example: string; did: string; unit: string };
const PLAIN_EN: Record<string, Plain> = {
  "BoM duplicate rows (same FL x material)": { title: "The same part listed twice at one location", example: "A location and part pair appears more than once in the parts list.", did: "Counted each pair once, so installed quantities are not doubled.", unit: "rows" },
  "PR/PO exact duplicate lines": { title: "Purchase lines copied exactly", example: "11,609 lines shrink to 6,189 real ones.", did: "Removed the copies before working out delivery times, prices and spend.", unit: "rows" },
  "Maintenance cycle text formats": { title: "Maintenance schedules written as free text", example: "\"5 YEARLY\" instead of a number of days.", did: "Read all 28 formats into a number of days. The count of jobs feeds the forecast, and the dates feed the maintenance calendar on the Forecast page.", unit: "formats" },
  "Notifications with Required Start before notification date": { title: "Breakdown notices that start before they were raised", example: "About 6.4% of all notices.", did: "Did not use those dates to work out delivery times.", unit: "notices" },
  "PR lines with negative lead time": { title: "Delivered before it was requested", example: "The delivery date is earlier than the purchase request date.", did: "Left them out of delivery time figures.", unit: "lines" },
  "Materials with an IDR PO price": { title: "Only some parts have a real rupiah price", example: "16.4% of all parts have a price from a purchase order.", did: "Estimated the rest from their category, and flagged them. Most money totals count only the real prices.", unit: "parts" },
  "Orders linked to a notification": { title: "Few parts issued can be tied to a breakdown", example: "Only 15.9% of parts issued point to a breakdown notice.", did: "Linked breakdowns to parts through the equipment location instead of one by one.", unit: "lines" },
  "PO-Item Amount is a unit price": { title: "The purchase amount field is a price per unit", example: "The amount stays the same whatever quantity is ordered.", did: "Worked out value as price times quantity, and never divided it by quantity.", unit: "lines" },
  "Stock ledger does not balance": { title: "Stock records that do not add up", example: "36.1% of parts with movements would have needed negative stock at the start.", did: "Lowered their trust score, so someone counts the shelf before acting.", unit: "parts" },
};

const PLAIN_ID: Record<string, Plain> = {
  "BoM duplicate rows (same FL x material)": { title: "Suku cadang yang sama tercatat dua kali di satu lokasi", example: "Pasangan lokasi dan suku cadang muncul lebih dari sekali dalam daftar suku cadang.", did: "Setiap pasangan dihitung sekali, sehingga jumlah terpasang tidak berlipat ganda.", unit: "baris" },
  "PR/PO exact duplicate lines": { title: "Baris pembelian yang tersalin persis", example: "11.609 baris menyusut menjadi 6.189 baris yang sebenarnya.", did: "Salinannya dihapus sebelum menghitung waktu kirim, harga, dan belanja.", unit: "baris" },
  "Maintenance cycle text formats": { title: "Jadwal pemeliharaan ditulis sebagai teks bebas", example: "\"5 YEARLY\" alih-alih jumlah hari.", did: "Ke-28 format dibaca menjadi jumlah hari. Jumlah pekerjaan masuk ke prakiraan, dan tanggalnya mengisi kalender pemeliharaan di halaman Prakiraan.", unit: "format" },
  "Notifications with Required Start before notification date": { title: "Laporan kerusakan yang dimulai sebelum dilaporkan", example: "Sekitar 6,4% dari semua laporan.", did: "Tanggal tersebut tidak dipakai untuk menghitung waktu kirim.", unit: "laporan" },
  "PR lines with negative lead time": { title: "Barang tiba sebelum diminta", example: "Tanggal kirimnya lebih awal daripada tanggal permintaan pembelian.", did: "Tidak diikutkan dalam perhitungan waktu kirim.", unit: "baris" },
  "Materials with an IDR PO price": { title: "Hanya sebagian suku cadang yang memiliki harga rupiah riil", example: "16,4% dari semua suku cadang memiliki harga dari pesanan pembelian.", did: "Sisanya ditaksir dari kategorinya dan diberi tanda. Sebagian besar total uang hanya menghitung harga riil.", unit: "suku cadang" },
  "Orders linked to a notification": { title: "Sedikit pengeluaran suku cadang yang bisa dikaitkan dengan kerusakan", example: "Hanya 15,9% pengeluaran suku cadang yang merujuk ke laporan kerusakan.", did: "Kerusakan dikaitkan dengan suku cadang melalui lokasi peralatannya, bukan satu per satu.", unit: "baris" },
  "PO-Item Amount is a unit price": { title: "Kolom nilai pembelian berisi harga per satuan", example: "Nilainya tetap sama berapa pun jumlah yang dipesan.", did: "Nilai dihitung sebagai harga dikali jumlah, dan tidak pernah dibagi dengan jumlah.", unit: "baris" },
  "Stock ledger does not balance": { title: "Catatan stok yang tidak seimbang", example: "36,1% suku cadang yang memiliki pergerakan seharusnya bermula dari stok negatif.", did: "Skor kepercayaannya diturunkan, sehingga raknya dihitung dulu sebelum ada tindakan.", unit: "suku cadang" },
};

/** Each trap is one row with a status; open it to read the evidence and what the pipeline did. */
export function TrapTree({ traps }: { traps: Trap[] }) {
  const reduce = useReducedMotion();
  const [open, setOpen] = useState<string | null>(traps[0]?.issue ?? null);
  return (
    <ul className="m-0 list-none divide-y divide-line p-0">
      {traps.map((d) => {
        const Icon = TRAP_ICON.find(([re]) => re.test(d.issue))?.[1] ?? Bug;
        const on = open === d.issue;
        const plain = t(PLAIN_EN, PLAIN_ID)[d.issue];
        return (
          <li key={d.issue}>
            <button type="button" aria-expanded={on} onClick={() => setOpen(on ? null : d.issue)} className="flex w-full items-center gap-3 px-4 py-3 text-left transition-colors duration-150 hover:bg-ink/[0.02]">
              <ChevronRight aria-hidden className={cn("h-4 w-4 shrink-0 text-ink-4 transition-transform duration-150", on && "rotate-90")} />
              <span className="grid h-8 w-8 shrink-0 place-items-center rounded-[9px] bg-plan-soft text-plan-ink"><Icon aria-hidden className="h-4 w-4" /></span>
              <span className="min-w-0 flex-1 truncate text-[13.5px] font-medium">{plain?.title ?? d.issue}</span>
              <span className="shrink-0 text-[13px] tabular-nums text-ink-3"><b className="font-semibold text-ink">{num(d.n)}</b> {plain?.unit}</span>
              <span className="inline-flex h-6 shrink-0 items-center gap-1 rounded-[7px] bg-ready-soft px-2 text-[12px] font-medium text-ready-ink">
                <CheckCircle2 aria-hidden className="h-3.5 w-3.5" />{t("Handled", "Tertangani")}
              </span>
            </button>
            <AnimatePresence initial={false}>
              {on && (
                <motion.div initial={reduce ? false : { height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }} exit={reduce ? undefined : { height: 0, opacity: 0 }} transition={{ duration: 0.18, ease: "easeOut" }} className="overflow-hidden">
                  <dl className="m-0 ml-[60px] grid gap-3 border-l border-line pb-4 pl-4 pr-4 text-[13px] leading-[1.5]">
                    <div>
                      <dt className="text-[12px] font-medium text-ink-3">{t("Example", "Contoh")}</dt>
                      <dd className="m-0 text-ink-2">{plain?.example ?? d.example}</dd>
                    </div>
                    <div>
                      <dt className="text-[12px] font-medium text-ink-3">{t("What we did", "Yang kami lakukan")}</dt>
                      <dd className="m-0 text-ink-2">{plain?.did ?? d.impact}</dd>
                    </div>
                  </dl>
                </motion.div>
              )}
            </AnimatePresence>
          </li>
        );
      })}
    </ul>
  );
}

"use client";

import * as Popover from "@radix-ui/react-popover";
import { CircleHelp } from "lucide-react";
import { t } from "@/lib/i18n";

const WORDS_EN: [string, string][] = [
  ["Turnaround", "The plant's big planned shutdown for maintenance. It uses far more parts in a few weeks than normal months do."],
  ["Parts short", "We will not have enough by the turnaround: the stock left after normal use is less than what the job needs. In \"46 of 119 parts short\", 46 parts are short out of the 119 that machine type used last turnaround."],
  ["A, B, C, S", "How much a part matters to the plant. A is the most critical, S the least. \"Critical parts\" on this site means A and B."],
  ["Min", "The low-stock line in SAP. When stock falls to it, a new order should go out."],
  ["Max", "The upper stock limit in SAP. Anything above it is money sitting on the shelf."],
  ["Reorder point", "The stock level that triggers a new order. Our suggested Min is the reorder point: use during delivery plus safety stock."],
  ["Safety stock", "Extra stock held for slow deliveries and bigger use than expected. It is sized to each part's target availability. Part pages show it under Show the math."],
  ["Stockout risk", "A part may run out before a new order can arrive. Critical parts that are empty or below Min come first, in the Fix now box on Stock."],
  ["Overstock risk", "Stock above Max, or above what the part is likely to use. It ties up money and can age on the shelf. See Stop buying and Free the cash."],
  ["Delivery time", "Days from purchase request to delivery. We plan on the slow case: 9 of 10 past orders arrived within it."],
  ["Last safe order day", "Turnaround date, minus the slow-case delivery time, minus 14 days of buffer."],
  ["Order by", "The last safe day to place the order. It is not the delivery date. Delivery comes later, up to the slow-case delivery time."],
  ["Rush order", "The last safe order day has passed, so a normal order arrives too close to the turnaround or after it starts."],
  ["Duplicate part", "The same part registered under another part number. Its extra stock can cover a shortage without buying."],
  ["Slow and dead stock", "Slow means no use for 6 months. Dead means no use for 12 months. The dates shown assume nothing uses the part before then."],
  ["Known price", "About 1 in 6 parts has a real price from past purchase orders. Money totals on most cards count only those, so the true amounts are higher."],
];

const WORDS_ID: [string, string][] = [
  ["Turnaround", "Penghentian besar kilang yang terencana untuk pemeliharaan. Dalam beberapa minggu, kebutuhan suku cadangnya jauh lebih banyak daripada bulan-bulan biasa."],
  ["Suku cadang kurang", "Stok tidak akan cukup sampai turnaround: sisa stok setelah pemakaian normal lebih sedikit daripada kebutuhan pekerjaan. Pada \"46 dari 119 suku cadang kurang\", 46 suku cadang kurang dari 119 yang dipakai jenis mesin itu pada turnaround sebelumnya."],
  ["A, B, C, S", "Seberapa penting suku cadang bagi kilang. A paling kritis, S paling tidak kritis. \"Suku cadang kritis\" di situs ini berarti A dan B."],
  ["Min", "Batas bawah stok di SAP. Saat stok turun sampai batas ini, pesanan baru seharusnya sudah dikirim."],
  ["Max", "Batas atas stok di SAP. Kelebihan di atasnya adalah uang yang mengendap di rak."],
  ["Reorder point", "Tingkat stok yang memicu pesanan baru. Min yang kami sarankan adalah reorder point: pemakaian selama pengiriman ditambah safety stock."],
  ["Safety stock", "Stok tambahan untuk pengiriman yang lambat dan pemakaian yang lebih besar dari perkiraan. Besarnya mengikuti target ketersediaan tiap suku cadang. Halaman suku cadang menampilkannya di Tampilkan perhitungannya."],
  ["Risiko kehabisan stok", "Suku cadang bisa habis sebelum pesanan baru tiba. Suku cadang kritis yang kosong atau di bawah Min didahulukan, di kotak Segera atasi pada halaman Stok."],
  ["Risiko kelebihan stok", "Stok di atas Max, atau di atas perkiraan pemakaiannya. Stok ini mengikat uang dan bisa menua di rak. Lihat tindakan Hentikan pembelian dan Bebaskan dananya."],
  ["Waktu kirim", "Jumlah hari dari permintaan pembelian sampai barang tiba. Kami merencanakan dengan skenario lambat: 9 dari 10 pesanan sebelumnya tiba dalam rentang waktu ini."],
  ["Batas aman pemesanan", "Tanggal turnaround dikurangi waktu kirim skenario lambat, lalu dikurangi lagi 14 hari cadangan waktu."],
  ["Pesan paling lambat", "Hari terakhir yang aman untuk memesan. Ini bukan tanggal barang tiba; barang tiba belakangan, paling lama sesuai waktu kirim skenario lambat."],
  ["Percepat pesanan", "Batas aman pemesanan sudah lewat, sehingga pesanan biasa akan tiba terlalu mepet dengan turnaround atau malah setelah turnaround dimulai."],
  ["Suku cadang kembar", "Suku cadang yang sama, tetapi terdaftar dengan nomor lain. Kelebihan stoknya bisa menutup kekurangan tanpa perlu membeli."],
  ["Stok lambat dan stok mati", "Stok lambat berarti tidak terpakai selama 6 bulan. Stok mati berarti tidak terpakai selama 12 bulan. Tanggal yang ditampilkan mengasumsikan suku cadang itu tidak terpakai sebelumnya."],
  ["Harga yang diketahui", "Hanya sekitar 1 dari 6 suku cadang yang memiliki harga riil dari pesanan pembelian sebelumnya. Total uang di sebagian besar kartu hanya menghitung suku cadang tersebut, jadi angka sebenarnya lebih besar."],
];

/** The same plain definitions from every page, one press away. */
export function Glossary() {
  return (
    <Popover.Root>
      <Popover.Trigger asChild>
        <button type="button" className="inline-flex h-9 shrink-0 items-center gap-2 rounded-[10px] border border-line bg-panel px-3 text-[13px] font-medium transition-colors hover:border-line-2">
          <CircleHelp aria-hidden className="h-4 w-4" />{t("Word guide", "Daftar istilah")}
        </button>
      </Popover.Trigger>
      <Popover.Portal>
        <Popover.Content align="end" sideOffset={6} className="z-40 max-h-[80vh] w-[400px] max-w-[92vw] overflow-y-auto rounded-[14px] border border-line bg-panel p-4 shadow-float">
          <h2 className="m-0 text-[14px] font-semibold">{t("What the words mean", "Arti istilah")}</h2>
          <dl className="m-0 mt-2 space-y-2.5 text-[13px] leading-[1.45]">
            {t(WORDS_EN, WORDS_ID).map(([word, meaning]) => (
              <div key={word}>
                <dt className="font-medium text-ink">{word}</dt>
                <dd className="m-0 text-ink-2">{meaning}</dd>
              </div>
            ))}
          </dl>
        </Popover.Content>
      </Popover.Portal>
    </Popover.Root>
  );
}

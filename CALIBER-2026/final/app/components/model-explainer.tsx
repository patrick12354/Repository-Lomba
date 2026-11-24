import type { ComponentType } from "react";
import Link from "next/link";
import type { ReplayProof } from "@/lib/data";
import { Brain, Database, FlaskConical, Sparkles } from "lucide-react";
import { Layers, Scale, ShieldCheck } from "@/components/icons";

type LucideIcon = ComponentType<{ className?: string }>;
import { cn, num, rp } from "@/lib/format";
import { Panel, PanelHead } from "./ui";
import { Hint } from "./hint";
import { isId, t } from "@/lib/i18n";

type Row = { method: string; auc_all: number | null; auc_cold: number | null; coverage_q95: number | null; note: string };

const stepsEn = (): { icon: LucideIcon; title: string; body: string; detail: string }[] => [
  { icon: Database, title: "Clean the six files", body: "BoM, movements, notifications, locations, maintenance plans, and purchase orders.", detail: "Nine data problems are fixed first, such as 5,420 purchase lines copied twice. See the list above." },
  { icon: Layers, title: "Build 25 signals per part", body: "How it was used, where it is installed, how often that equipment breaks, and how it is bought.", detail: "Use history (units and issues per month, last 90 days, months active, days since last use), equipment (installed quantity, locations, breakdown and emergency notices, planned maintenance), buying (requests, delivery time), criticality, category, and today's Min and Max." },
  { icon: Brain, title: "Model 1: will it be used?", body: "Gives each part a chance of use in the next 6 months.", detail: "A LightGBM classifier, trained on monthly 90-day windows from Jun 2025 to Jul 2026. Recent months count more, halving every 3 months. Parts with no history still get a chance, from their equipment and installed base." },
  { icon: Sparkles, title: "Model 2: how many?", body: "Estimates how many units, half from a model and half from the last 90 days.", detail: "A LightGBM regression with a Tweedie loss, made for counts that are often zero, blended 50/50 with the recent run rate." },
  { icon: FlaskConical, title: "Simulate 2,000 futures", body: "Turns one estimate into a range: most likely, high, and bad case.", detail: "Each future draws how many times the part is used (Poisson) and how much each time, from the part's own past issue sizes. Delivery time is varied too, to get the use while waiting for delivery." },
  { icon: Scale, title: "Set the stock limits", body: "New Min and Max from the target availability per criticality, plus turnaround order dates.", detail: "Targets are 95% for A, 90% B, 85% C, 80% S. New Min covers use during delivery at that level. New Max adds an order quantity that balances order cost and holding cost, capped at one year of use. The last turnaround is added on top as a planned event." },
];

const stepsId = (): { icon: LucideIcon; title: string; body: string; detail: string }[] => [
  { icon: Database, title: "Bersihkan enam berkas", body: "BoM, pergerakan stok, laporan kerusakan, lokasi, rencana pemeliharaan, dan pesanan pembelian.", detail: "Sembilan masalah data diperbaiki lebih dulu, misalnya 5.420 baris pembelian yang tersalin dua kali. Lihat daftar di atas." },
  { icon: Layers, title: "Susun 25 sinyal per suku cadang", body: "Cara pemakaiannya, lokasi pemasangannya, seberapa sering peralatannya rusak, dan cara pembeliannya.", detail: "Riwayat pemakaian (jumlah dan frekuensi pengeluaran per bulan, 90 hari terakhir, bulan aktif, hari sejak terakhir dipakai), peralatan (jumlah terpasang, lokasi, laporan kerusakan dan darurat, pemeliharaan terencana), pembelian (permintaan, waktu kirim), kekritisan, kategori, serta Min dan Max saat ini." },
  { icon: Brain, title: "Model 1: akan terpakai atau tidak?", body: "Memberi setiap suku cadang peluang terpakai dalam 6 bulan ke depan.", detail: "Klasifikasi LightGBM yang dilatih pada jendela 90 hari bulanan dari Jun 2025 sampai Jul 2026. Bulan-bulan terbaru diberi bobot lebih besar, yang berkurang separuhnya setiap 3 bulan. Suku cadang tanpa riwayat tetap mendapat peluang, dari peralatan dan basis terpasangnya." },
  { icon: Sparkles, title: "Model 2: berapa banyak?", body: "Menaksir jumlah unit, separuh dari model dan separuh dari 90 hari terakhir.", detail: "Regresi LightGBM dengan fungsi kerugian Tweedie, yang dirancang untuk data hitungan yang sering bernilai nol, lalu dicampur 50/50 dengan laju pemakaian terbaru." },
  { icon: FlaskConical, title: "Simulasikan 2.000 kemungkinan", body: "Mengubah satu taksiran menjadi rentang: paling mungkin, tinggi, dan terburuk.", detail: "Setiap kemungkinan menarik berapa kali suku cadang dipakai (Poisson) dan berapa banyak setiap kalinya, dari ukuran pengeluaran suku cadang itu sendiri di masa lalu. Waktu kirim juga divariasikan untuk mendapatkan pemakaian selama menunggu kiriman." },
  { icon: Scale, title: "Tetapkan batas stok", body: "Min dan Max baru dari target ketersediaan per kekritisan, ditambah tanggal pemesanan untuk turnaround.", detail: "Targetnya 95% untuk A, 90% B, 85% C, 80% S. Min baru menutup pemakaian selama masa pengiriman pada tingkat tersebut. Max baru menambahkan jumlah pesanan yang menyeimbangkan biaya pemesanan dan biaya penyimpanan, dengan batas pemakaian satu tahun. Turnaround terakhir ditambahkan di atasnya sebagai kejadian terencana." },
];

const pc = (v: number | null | undefined) => (v == null ? "–" : `${Math.round(v * 100)}`);
const mae = (note: string, which: "model" | "naive") => {
  const m = note.match(/MAE ([\d.]+) \(naive ([\d.]+)\)/);
  return m ? Number(m[which === "model" ? 1 : 2]) : null;
};
const month = (iso: string) => new Date(`${iso}T00:00:00Z`).toLocaleString(isId() ? "id-ID" : "en-GB", { month: "short", year: "numeric", timeZone: "UTC" });

const compareRows = (): [string, string, boolean][] => [
  ["lgbm_2part", t("Sparekit, two models", "Sparekit, dua model"), true],
  ["hybrid", t("Sparekit model mixed with the run rate", "Model Sparekit dicampur laju pemakaian"), true],
  ["naive_mean", t("Average of past use", "Rata-rata pemakaian sebelumnya"), false],
  ["sba", t("Classic spare-part formula (SBA)", "Rumus suku cadang klasik (SBA)"), false],
  ["tsb", t("Classic spare-part formula (TSB)", "Rumus suku cadang klasik (TSB)"), false],
  ["eb_installed", t("Installed base only", "Hanya basis terpasang"), false],
  ["zero", t("Always predict zero", "Selalu menebak nol"), false],
];

/** How the forecast is built and how well it did on months it never saw. */
export function ModelExplainer({ rows, replay }: { rows: Row[]; replay: ReplayProof | null }) {
  const origins = rows.filter((r) => r.method.startsWith("engine_rolling_2026")).sort((a, b) => a.method.localeCompare(b.method));
  const mean = rows.find((r) => r.method === "engine_rolling_mean");
  const strict = rows.find((r) => r.method === "engine_strict_mean");
  const naiveAuc = Number(mean?.note.match(/AUC naive ([\d.]+)/)?.[1] ?? NaN);
  const STEPS = t(stepsEn(), stepsId());
  const compare = compareRows().map(([k, label, ours]) => ({ label, ours, row: rows.find((r) => r.method === k) })).filter((x) => x.row);
  const now = replay?.today;
  const rec = replay?.sparekit;

  return (
    <div className="space-y-6">
      <Panel>
        <PanelHead title={<span className="flex items-center gap-1">{t("How the forecast works", "Cara kerja prakiraan")}<Hint>{t("The engine runs once on the data and writes every result into the SQLite database the app reads. The app never re-estimates, so every page shows the same numbers.", "Mesin hitung dijalankan sekali pada data dan menulis setiap hasilnya ke basis data SQLite yang dibaca aplikasi. Aplikasi tidak pernah menaksir ulang, sehingga setiap halaman menampilkan angka yang sama.")}</Hint></span>} icon={Brain} />
        <p className="m-0 px-5 pt-1 text-[13px] leading-[1.5] text-ink-2">{t("Six steps, from raw files to a Min and Max for every part. Hover a step for the detail.", "Enam langkah, dari berkas mentah sampai Min dan Max untuk setiap suku cadang. Arahkan kursor ke sebuah langkah untuk melihat rinciannya.")}</p>
        <ol className="m-0 grid list-none grid-cols-2 gap-3 p-5 lg:grid-cols-6">
          {STEPS.map((s, i) => (
            <li key={s.title} className="relative flex flex-col rounded-[14px] bg-panel-2 p-3.5">
              <div className="flex items-center justify-between">
                <span className="grid h-8 w-8 place-items-center rounded-[10px] bg-panel text-ink-2 shadow-card"><s.icon aria-hidden className="h-4 w-4" /></span>
                <span className="text-[11.5px] font-semibold tabular-nums text-ink-4">{i + 1}</span>
              </div>
              <div className="mt-2.5 flex items-center gap-1 text-[13px] font-semibold leading-snug">{s.title}<Hint>{s.detail}</Hint></div>
              <p className="m-0 mt-1 text-[12px] leading-snug text-ink-3">{s.body}</p>
            </li>
          ))}
        </ol>
      </Panel>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[minmax(0,1.2fr)_minmax(0,1fr)]">
        <Panel>
          <PanelHead title={<span className="flex items-center gap-1">{t("Tested on months it never saw", "Diuji pada bulan yang belum pernah dilihatnya")}<Hint>{t("Rolling test: at each start date the model is trained only on data before it, then asked to predict the next 90 days. It is scored against what really happened. The model was chosen on these four tests.", "Uji bergulir: pada setiap tanggal mulai, model hanya dilatih dengan data sebelum tanggal itu, lalu diminta memprakirakan 90 hari berikutnya. Hasilnya dinilai terhadap kejadian yang sebenarnya. Model dipilih berdasarkan keempat uji ini.")}</Hint></span>} icon={FlaskConical} />
          <div className="px-5 pb-5 pt-3">
            <div className="grid grid-cols-[minmax(0,1.1fr)_repeat(4,minmax(0,1fr))] gap-x-3 border-b border-line pb-2 text-[11.5px] font-medium leading-snug text-ink-3">
              <span>{t("Start of test", "Awal uji")}</span>
              <span className="flex items-center gap-1">{t("Right part", "Tepat sasaran")}<Hint>{t("Out of 100 pairs of parts, one used and one not, how often the model ranks the used one higher (AUC × 100).", "Dari 100 pasangan suku cadang, satu terpakai dan satu tidak, seberapa sering model menempatkan yang terpakai di peringkat lebih tinggi (AUC × 100).")}</Hint></span>
              <span>{t("Right part, no history", "Tepat sasaran, tanpa riwayat")}</span>
              <span className="flex items-center gap-1">{t("Units off", "Selisih unit")}<Hint>{t("Average error in units per part over the 90 days, against assuming the last 90 days repeat. Lower is better.", "Rata-rata kesalahan dalam unit per suku cadang selama 90 hari, dibandingkan dengan asumsi bahwa 90 hari terakhir terulang. Makin rendah makin baik.")}</Hint></span>
              <span className="flex items-center gap-1">{t("Bad case enough", "Skenario terburuk cukup")}<Hint>{t("Of the parts that were really used in the 90 days, the share whose use the bad-case estimate covered. Parts that were not used are left out, since any estimate covers zero.", "Dari suku cadang yang benar-benar terpakai dalam 90 hari, persentase yang pemakaiannya tertutup oleh taksiran skenario terburuk. Suku cadang yang tidak terpakai tidak dihitung, karena taksiran apa pun pasti menutup angka nol.")}</Hint></span>
            </div>
            {origins.map((r) => (
              <div key={r.method} className="grid grid-cols-[minmax(0,1.1fr)_repeat(4,minmax(0,1fr))] gap-x-3 border-b border-line py-2 text-[13px] tabular-nums">
                <span className="text-ink-2">{month(r.method.replace("engine_rolling_", ""))}</span>
                <span className="font-semibold text-ready-ink">{pc(r.auc_all)}</span>
                <span className="font-semibold">{pc(r.auc_cold)}</span>
                <span>{num(mae(r.note, "model"), 1)} <span className="text-[11.5px] text-ink-3">{t("vs", "vs")} {num(mae(r.note, "naive"), 1)}</span></span>
                <span>{pc(r.coverage_q95)}%</span>
              </div>
            ))}
            {mean && (
              <div className="grid grid-cols-[minmax(0,1.1fr)_repeat(4,minmax(0,1fr))] gap-x-3 pt-2 text-[13px] font-semibold tabular-nums">
                <span>{t("Average", "Rata-rata")}</span>
                <span className="text-ready-ink">{pc(mean.auc_all)} <span className="text-[11.5px] font-normal text-ink-3">vs {pc(naiveAuc)}</span></span>
                <span>{pc(mean.auc_cold)}</span>
                <span className="font-normal text-ink-3">{t("about level", "kurang lebih setara")}</span>
                <span>{pc(mean.coverage_q95)}%</span>
              </div>
            )}
            <ul className="m-0 mt-4 list-disc space-y-1 pl-4 text-[12.5px] leading-[1.5] text-ink-2">
              {t(
                <>
                  <li>It picks which parts will be used far better than the simple rule: {pc(mean?.auc_all)} against {pc(naiveAuc)} out of 100.</li>
                  <li>On how many units, it is about level with the last 90 days, so stock limits use a lead-time estimate at each part&apos;s service level rather than one number. The 180-day bad case alone covered about {pc(mean?.coverage_q95)}% of the parts that were really used.</li>
                  {strict && <li>Today&apos;s Min and Max are one of the signals. Without them the scores are {pc(strict.auc_all)} and {pc(strict.auc_cold)}, still ahead of the simple rule.</li>}
                </>,
                <>
                  <li>Model ini jauh lebih tepat daripada aturan sederhana dalam memilih suku cadang yang akan terpakai: {pc(mean?.auc_all)} berbanding {pc(naiveAuc)} dari 100.</li>
                  <li>Untuk jumlah unit, hasilnya kurang lebih setara dengan 90 hari terakhir, sehingga batas stok memakai taksiran selama waktu kirim pada tingkat layanan tiap suku cadang, bukan satu angka saja. Skenario terburuk 180 hari saja sudah menutup sekitar {pc(mean?.coverage_q95)}% suku cadang yang benar-benar terpakai.</li>
                  {strict && <li>Min dan Max saat ini adalah salah satu sinyalnya. Tanpa keduanya, skornya {pc(strict.auc_all)} dan {pc(strict.auc_cold)}, tetap lebih baik daripada aturan sederhana.</li>}
                </>,
              )}
            </ul>
          </div>
        </Panel>

        <div className="space-y-6">
          <Panel>
            <PanelHead title={<span className="flex items-center gap-1">{t("Against other methods", "Dibandingkan metode lain")}<Hint>{t("An earlier test of the same question on one hold-out window: how often each method ranks a used part above an unused one, out of 100. The light bar is for parts with no use on record.", "Uji sebelumnya untuk pertanyaan yang sama pada satu jendela hold-out: seberapa sering setiap metode menempatkan suku cadang yang terpakai di atas yang tidak terpakai, dari 100. Batang yang lebih terang untuk suku cadang tanpa catatan pemakaian.")}</Hint></span>} icon={ShieldCheck} />
            <ul className="m-0 list-none space-y-2.5 px-5 pb-5 pt-3">
              {compare.map(({ label, ours, row }) => (
                <li key={label} className="text-[12.5px]">
                  <div className="flex justify-between gap-3"><span className={cn(ours ? "font-semibold" : "text-ink-2")}>{label}</span><span className="shrink-0 tabular-nums">{pc(row!.auc_all)}{row!.auc_cold != null && <span className="text-ink-3"> · {pc(row!.auc_cold)}</span>}</span></div>
                  <div className="relative mt-1 h-2 overflow-hidden rounded-full bg-ink/[0.06]">
                    {row!.auc_cold != null && <div className="absolute inset-y-0 left-0 rounded-full bg-ink/15" style={{ width: `${row!.auc_cold * 100}%` }} />}
                    <div className={cn("absolute inset-y-0 left-0 rounded-full", ours ? "bg-ready" : "bg-ink-3/70")} style={{ width: `${(row!.auc_all ?? 0) * 100}%`, opacity: row!.auc_cold != null ? 0.9 : 1 }} />
                  </div>
                </li>
              ))}
            </ul>
          </Panel>

          {now && rec && (
            <Panel>
              <PanelHead title={<span className="flex items-center gap-1"><Link href="/replay" className="underline-offset-2 hover:underline">{t("Replayed on real use", "Diputar ulang dengan pemakaian riil")}</Link><Hint>{t("March to September 2026, day by day, on critical stocked parts: real use is taken from the shelf, and orders follow each plan. Limits are updated every month. Each plan starts with stock at its own Max. Some prices are estimated. Press the title to play it.", "Maret sampai September 2026, hari demi hari, pada suku cadang kritis yang distok: pemakaian riil diambil dari rak, dan pesanan mengikuti setiap rencana. Batas diperbarui setiap bulan. Setiap rencana dimulai dengan stok pada Max-nya sendiri. Sebagian harga merupakan taksiran. Tekan judulnya untuk memutarnya.")}</Hint></span>} icon={Scale} />
              <dl className="m-0 grid grid-cols-3 gap-3 px-5 pb-5 pt-3 text-[12px] text-ink-3">
                <div><dd className="m-0 text-[20px] font-semibold tabular-nums text-ready-ink">{pc(rec.fill_units)}%</dd><dt>{t(`critical stocked parts on the shelf when asked, from ${pc(now.fill_units)}%`, `suku cadang kritis yang distok tersedia di rak saat diminta, dari ${pc(now.fill_units)}%`)}</dt></div>
                <div><dd className="m-0 text-[20px] font-semibold tabular-nums text-ink">{num(rec.stockout_days)}</dd><dt>{t(`empty-shelf days, from ${num(now.stockout_days)}`, `hari rak kosong, dari ${num(now.stockout_days)}`)}</dt></div>
                <div><dd className="m-0 text-[20px] font-semibold tabular-nums text-ink">{rp(rec.avg_inv_idr)}</dd><dt>{t(`average stock across all ${num(replay?.stocked ?? 0)} stocked parts, from ${rp(now.avg_inv_idr)}`, `rata-rata stok seluruh ${num(replay?.stocked ?? 0)} suku cadang distok, dari ${rp(now.avg_inv_idr)}`)}</dt></div>
              </dl>
            </Panel>
          )}
        </div>
      </div>
    </div>
  );
}

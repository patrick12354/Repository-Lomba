import Link from "next/link";
import { ShieldCheck } from "@/components/icons";
import { replayProof, trust } from "@/lib/data";
import { ModelExplainer } from "@/components/model-explainer";
import { SHELF_LIFE } from "@/lib/shelf-life";
import { categoryName } from "@/lib/format";
import { cn, num, partName, rp, shortDate } from "@/lib/format";
import { CritTile, Em, PageHead, Panel, PanelHead } from "@/components/ui";
import { TrapTree } from "@/components/trap-tree";
import { AiBrief } from "@/components/ai-brief";
import { LearningLoop } from "@/components/learning-loop";
import { Choices } from "@/components/choices";
import { t } from "@/lib/i18n";
import { getLang, titled } from "@/lib/i18n-server";

export const generateMetadata = titled("Data check", "Cek data");

const assumptions = (): [string, string, (v: string) => string][] => [
  ["as_of_date", t("Data as of", "Data per"), (v) => shortDate(v, true)],
  ["next_ta_default", t("Next turnaround (our assumption, not an official date)", "Turnaround berikutnya (asumsi kami, bukan tanggal resmi)"), (v) => shortDate(v, true)],
  ["ta_buffer_days", t("Extra days allowed before a turnaround", "Cadangan hari sebelum turnaround"), (v) => t(`${v} days`, `${v} hari`)],
  ["holding_rate", t("Yearly cost of holding stock", "Biaya penyimpanan stok per tahun"), (v) => t(`${Math.round(Number(v) * 100)}% of value`, `${Math.round(Number(v) * 100)}% dari nilai`)],
  ["service_level_A", t("Target: on the shelf when needed, A parts", "Target ketersediaan di rak saat dibutuhkan, suku cadang A"), (v) => `${Math.round(Number(v) * 100)}%`],
  ["service_level_B", t("Target: on the shelf when needed, B parts", "Target ketersediaan di rak saat dibutuhkan, suku cadang B"), (v) => `${Math.round(Number(v) * 100)}%`],
  ["service_level_C", t("Target: on the shelf when needed, C parts", "Target ketersediaan di rak saat dibutuhkan, suku cadang C"), (v) => `${Math.round(Number(v) * 100)}%`],
  ["service_level_S", t("Target: on the shelf when needed, S parts", "Target ketersediaan di rak saat dibutuhkan, suku cadang S"), (v) => `${Math.round(Number(v) * 100)}%`],
  ["criticality_order", t("How critical, highest to lowest", "Tingkat kekritisan, dari tertinggi ke terendah"), (v) => v.split(" (")[0].replaceAll(" > ", ", ")],
  ["order_cost_idr", t("Admin cost of one purchase request", "Biaya administrasi satu permintaan pembelian"), (v) => rp(Number(v))],
];

export default async function Page() {
  await getLang();
  const ASSUMPTIONS = assumptions();
  const tr = trust();
  const monthly = tr.backtest.filter((r) => r.method.startsWith("engine_rolling_2026")).sort((a, b) => a.method.localeCompare(b.method)).map((r) => r.auc_all ?? 0);
  const p = tr.proof;
  const lv = tr.levels;
  const lvTot = lv.high + lv.medium + lv.low;

  return (
    <div className="space-y-6">
      <PageHead
        title={t("Can we trust these numbers?", "Bisakah angka-angka ini dipercaya?")}
        actions={<AiBrief page="check" />}
        answer={t(
          <>
            We checked the data before using it and found <Em>{tr.dq.length} problems</Em>. Each one is handled below, with how the system keeps learning and every choice we made, including what we chose not to do.
          </>,
          <>
            Kami memeriksa data sebelum memakainya dan menemukan <Em>{tr.dq.length} masalah</Em>. Masing-masing sudah ditangani di bawah ini, lengkap dengan cara sistem terus belajar dan setiap pilihan yang kami ambil, termasuk apa yang sengaja tidak kami lakukan.
          </>,
        )}
      />

      <div className="grid grid-cols-[minmax(0,1.5fr)_minmax(0,1fr)] items-start gap-6">
        <Panel tour="c-traps" className="overflow-hidden">
          <PanelHead title={t("Problems in the data, and what we did", "Masalah dalam data, dan yang kami lakukan")} className="pb-3" />
          <div className="border-t border-line"><TrapTree traps={tr.dq} /></div>
        </Panel>

        <div className="space-y-6">
          <Panel tour="c-trust" className="p-5">
            <h2 className="m-0 text-[14px] font-semibold">{t("How much each part's data can be trusted", "Seberapa dapat dipercaya data tiap suku cadang")}</h2>
            <div className="mt-3 flex h-7 overflow-hidden rounded-[8px]" role="img" aria-label={t("Trust levels", "Tingkat kepercayaan")}>
              <div className="border-r-2 border-panel bg-ready" style={{ width: `${(lv.high / lvTot) * 100}%` }} />
              <div className="border-r-2 border-panel bg-plan" style={{ width: `${(lv.medium / lvTot) * 100}%` }} />
              <div className="bg-act" style={{ width: `${(lv.low / lvTot) * 100}%` }} />
            </div>
            <div className="mt-3 grid grid-cols-3 gap-3 text-[12px] text-ink-3">
              {(
                [
                  [t("High", "Tinggi"), lv.high, "bg-ready"],
                  [t("Medium", "Sedang"), lv.medium, "bg-plan"],
                  [t("Check first", "Periksa dulu"), lv.low, "bg-act"],
                ] as const
              ).map(([l, n, c]) => (
                <div key={l}>
                  <div className="flex items-center gap-1.5"><span className={cn("h-2.5 w-2.5 rounded-[3px]", c)} />{l}</div>
                  <div className="mt-1 text-[20px] font-semibold leading-none tabular-nums text-ink">{num(n)}</div>
                </div>
              ))}
            </div>
            <h3 className="m-0 mt-5 text-[13px] font-semibold">{t("Count these shelves first: the records do not add up and the value is high", "Hitung rak-rak ini lebih dulu: catatannya tidak cocok dan nilainya tinggi")}</h3>
            <ul className="m-0 mt-1 list-none divide-y divide-line p-0">
              {tr.countFirst.map((c) => (
                <li key={c.material_no} className="flex items-center gap-3 py-2 text-[13px]">
                  <CritTile crit={c.criticality} />
                  <Link href={`/parts/${c.material_no}`} className="min-w-0 flex-1 truncate hover:underline">{partName(c.description)}</Link>
                  <span className="shrink-0 tabular-nums text-ink-3">{rp(c.stock_value)}</span>
                </li>
              ))}
            </ul>
          </Panel>
        </div>
      </div>

      <ModelExplainer rows={tr.backtest} replay={replayProof()} />

      <LearningLoop monthly={monthly} taDate={tr.meta.next_ta_default} />

      <Choices />

      <div className="grid grid-cols-[minmax(0,1.5fr)_minmax(0,1fr)] items-start gap-6">
        {p.engine != null && p.baseline != null && (
          <Panel>
            <PanelHead title={t("Does the forecast pick the right parts?", "Apakah prakiraan memilih suku cadang yang tepat?")} icon={ShieldCheck} />
            <p className="m-0 px-5 pt-1 text-[13px] leading-[1.5] text-ink-2">{t("Take one part that got used and one that did not. Out of 100 such pairs, how often does the method rank the used one higher? Tested on months it never saw.", "Ambil satu suku cadang yang terpakai dan satu yang tidak. Dari 100 pasangan seperti itu, seberapa sering metode ini menempatkan yang terpakai di peringkat lebih tinggi? Diuji pada bulan-bulan yang belum pernah dilihatnya.")}</p>
            <div className="grid grid-cols-2 gap-6 px-5 pb-5 pt-4">
              <Duel title={t("All parts", "Semua suku cadang")} a={{ label: "Sparekit", v: p.engine }} b={{ label: t("Assuming the last 90 days repeat", "Dengan asumsi 90 hari terakhir terulang"), v: p.baseline }} />
              {p.engineColdHoldout != null && p.classicCold != null && <Duel title={t("Parts with no use on record, hold-out test", "Suku cadang tanpa catatan pemakaian, uji hold-out")} a={{ label: "Sparekit", v: p.engineColdHoldout }} b={{ label: t("Classic spare-part formula", "Rumus suku cadang klasik"), v: p.classicCold }} />}
            </div>
          </Panel>
        )}
        <Panel tour="c-assume">
          <PanelHead title={t("Assumptions behind every number", "Asumsi di balik setiap angka")} />
          <dl className="m-0 divide-y divide-line px-5 pb-2 pt-2">
            {ASSUMPTIONS.filter(([k]) => tr.meta[k] != null).map(([k, label, f]) => (
              <div key={k} className="flex items-center justify-between gap-4 py-2 text-[13px]">
                <dt className="text-ink-2">{label}</dt>
                <dd className="m-0 font-medium tabular-nums">{f(tr.meta[k])}</dd>
              </div>
            ))}
            <div className="flex items-center justify-between gap-4 py-2 text-[13px]">
              <dt className="text-ink-2">{t("Downtime cost", "Biaya henti operasi")}</dt>
              <dd className="m-0 text-right font-medium">{t("Not in the data, so it is an assumption", "Tidak ada dalam data, jadi berupa asumsi")}</dd>
            </div>
          </dl>
        </Panel>
      </div>

      <Panel>
        <PanelHead title={t("Typical shelf life, from published guidance", "Umur simpan umum, menurut panduan yang dipublikasikan")} />
        <p className="m-0 px-5 pt-1 text-[13px] leading-[1.5] text-ink-2">{t("Not from this plant's data. Sources disagree, and the datasheet of the actual product wins. Parts not listed are mostly metal, and we found no published limit for them. The data has no receipt dates, so we compare how long stock will last at normal use against these figures.", "Bukan dari data kilang ini. Sumber-sumbernya berbeda pendapat, dan lembar data produk yang sebenarnya menjadi acuan utama. Suku cadang yang tidak tercantum umumnya berbahan logam, dan kami tidak menemukan batas yang dipublikasikan untuknya. Data tidak memuat tanggal penerimaan, jadi kami membandingkan lamanya stok bertahan pada pemakaian normal dengan angka-angka ini.")}</p>
        <ul className="m-0 grid list-none grid-cols-1 gap-x-8 px-5 pb-4 pt-2 lg:grid-cols-3">
          {Object.entries(SHELF_LIFE).map(([k, v]) => (
            <li key={k} className="border-b border-line py-2 text-[13px]">
              <div className="flex justify-between gap-3"><span className="font-medium">{categoryName(k)}</span><span className="shrink-0 tabular-nums">{v.range}</span></div>
              <div className="mt-0.5 text-[12px] leading-snug text-ink-3">{v.note}. <a href={v.url} target="_blank" rel="noreferrer" className="underline underline-offset-2">{v.source}</a></div>
            </li>
          ))}
        </ul>
      </Panel>
    </div>
  );
}

function Duel({ title, a, b }: { title: string; a: { label: string; v: number }; b: { label: string; v: number } }) {
  return (
    <div>
      <h3 className="m-0 text-[13px] font-semibold text-ink">{title}</h3>
      <div className="mt-3 grid grid-cols-2 gap-5">
        <Waffle label={a.label} v={a.v} strong />
        <Waffle label={b.label} v={b.v} />
      </div>
    </div>
  );
}

/** 100 dots; the filled ones are the pairs the method got right. */
function Waffle({ label, v, strong }: { label: string; v: number; strong?: boolean }) {
  const n = Math.round(v * 100);
  return (
    <div>
      <div className="grid grid-cols-10 gap-[3px]" role="img" aria-label={t(`${label}: right ${n} times out of 100`, `${label}: benar ${n} kali dari 100`)}>
        {Array.from({ length: 100 }, (_, i) => (
          <span key={i} className={cn("aspect-square rounded-full", i < n ? (strong ? "bg-ready" : "bg-ink-3") : "bg-ink/[0.08]")} />
        ))}
      </div>
      <div className="mt-2.5 flex items-baseline gap-1.5">
        <span className={cn("text-[20px] font-semibold leading-none tabular-nums", strong ? "text-ready-ink" : "text-ink-2")}>{n}</span>
        <span className="text-[12px] text-ink-3">{t("of 100", "dari 100")}</span>
      </div>
      <div className="mt-1 text-[12.5px] text-ink-2">{label}</div>
    </div>
  );
}

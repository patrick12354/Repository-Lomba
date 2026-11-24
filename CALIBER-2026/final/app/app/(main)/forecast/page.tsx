import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { Activity, MapPin, ShieldCheck, Snowflake, Truck, Wallet } from "@/components/icons";
import { maintenanceAhead, modelProof, needList, outlook, replayProof, unusualUse } from "@/lib/data";
import { MaintenanceAhead } from "@/components/maintenance-ahead";
import { amount, CRITS, chance, cn, num, partName, rp, shortDate } from "@/lib/format";
import { CritTile, Em, PageHead, Panel, PanelHead } from "@/components/ui";
import { PlantChart } from "@/components/demand-chart";
import { AiBrief } from "@/components/ai-brief";
import { NeedTable } from "@/components/need-table";
import { Hint } from "@/components/hint";
import { t } from "@/lib/i18n";
import { getLang, titled } from "@/lib/i18n-server";

export const generateMetadata = titled("Forecast", "Prakiraan");

const bands = () => [
  { key: "very", label: t("Very likely", "Sangat mungkin"), tone: "bg-accent" },
  { key: "maybe", label: t("Possible", "Mungkin"), tone: "bg-accent/40" },
  { key: "unlikely", label: t("Unlikely", "Kecil kemungkinan"), tone: "bg-ink/10" },
];

const pc = (v: number | null | undefined) => (v == null ? "–" : `${Math.round(v * 100)}`);

const patterns = () => [
  { key: "smooth", name: t("Steady", "Stabil"), how: t("Regular use, so use in the last 90 days carries half the estimate.", "Pemakaiannya teratur, jadi pemakaian 90 hari terakhir menyumbang separuh taksiran.") },
  { key: "intermittent", name: t("Intermittent", "Berselang"), how: t("Long gaps, similar amounts each time. The chance of use and the amount are estimated separately.", "Jedanya panjang, jumlahnya mirip setiap kali. Peluang terpakai dan jumlahnya ditaksir terpisah.") },
  { key: "erratic", name: t("Erratic", "Tidak menentu"), how: t("Used often, but the amounts swing. That spread goes into the estimate, so the safety stock comes out bigger.", "Sering dipakai, tetapi jumlahnya naik turun. Sebaran itu masuk ke taksiran, sehingga stok pengamannya lebih besar.") },
  { key: "lumpy", name: t("Lumpy", "Sporadis"), how: t("Long gaps and big swings. An average misleads here, so limits allow for the full spread of use.", "Jedanya panjang dan jumlahnya sangat bervariasi. Rata-rata menyesatkan di sini, jadi batas stok memperhitungkan seluruh sebaran pemakaian.") },
  { key: "single", name: t("Used once", "Sekali pakai"), how: t("One use in 17 months is too little to learn amounts from, so it borrows them from its part type.", "Sekali pakai dalam 17 bulan terlalu sedikit untuk mempelajari jumlahnya, jadi jumlahnya dipinjam dari jenis suku cadangnya.") },
  { key: "none", name: t("Never used", "Belum pernah dipakai"), how: t("No history. The chance comes from how many are installed and how often that equipment breaks, the amount from its part type.", "Tidak ada riwayat. Peluangnya berasal dari jumlah yang terpasang dan seberapa sering peralatannya rusak, jumlahnya dari jenis suku cadangnya.") },
];

function Part({ n, title, sub }: { n: number; title: string; sub: string }) {
  return (
    <div className="flex items-start gap-2.5 pt-2">
      <span className="mt-0.5 grid h-6 w-6 shrink-0 place-items-center rounded-full bg-ink text-[12px] font-semibold text-white">{n}</span>
      <div className="min-w-0">
        <h2 className="m-0 text-[16px] font-semibold leading-tight">{title}</h2>
        <p className="m-0 mt-0.5 text-[13px] leading-snug text-ink-3">{sub}</p>
      </div>
    </div>
  );
}

const STEP_TONE = { none: "bg-panel text-ink", act: "bg-act-soft text-act-ink", plan: "bg-plan-soft text-plan-ink" };

/** One chevron in the flow. Each step overlaps the last, so the row reads as one arrow from left to right. */
function Step({ value, label, sub, tone = "none", hint, first, last }: { value: string; label: string; sub?: string; tone?: keyof typeof STEP_TONE; hint?: string; first?: boolean; last?: boolean }) {
  const notch = 18;
  const clip = `polygon(0 0, calc(100% - ${last ? 0 : notch}px) 0, 100% 50%, calc(100% - ${last ? 0 : notch}px) 100%, 0 100%, ${first ? 0 : notch}px 50%)`;
  return (
    <li className={cn("relative min-w-0 flex-1 drop-shadow-[0_1px_1px_rgb(30_26_20/0.08)]", !first && "-ml-2.5")}>
      <div className={cn("flex h-full flex-col justify-center py-3.5", STEP_TONE[tone], first ? "rounded-l-[16px] pl-5" : "pl-8", last ? "rounded-r-[16px] pr-5" : "pr-7")} style={{ clipPath: clip }}>
        <div className="text-[28px] font-semibold leading-none tracking-[-0.02em] tabular-nums">{value}</div>
        <div className="mt-1.5 text-[12.5px] font-medium leading-snug">{label}</div>
        {sub && <div className="text-[12px] leading-snug opacity-70">{sub}</div>}
      </div>
      {hint && <span className={cn("absolute top-2.5", last ? "right-3" : "right-7")}><Hint>{hint}</Hint></span>}
    </li>
  );
}

export default async function Page() {
  await getLang();
  const BANDS = bands();
  const PATTERNS = patterns();
  const o = outlook();
  const m = modelProof();
  const n = needList();
  const odd = unusualUse(6);
  const rows = o.months.map((x) => ({ month: x.month, routine: x.parts - x.parts_ta, ta: x.parts_ta }));
  const p = o.proof;
  const maintenance = maintenanceAhead();
  const replay = replayProof();
  const now = replay?.today;
  const lean = replay?.sparekit;
  const patternTotal = o.patterns.reduce((a, x) => a + x.n, 0);

  return (
    <div className="space-y-5">
      <PageHead
        title={t("What will we need, and when?", "Apa yang akan kita butuhkan, dan kapan?")}
        actions={<AiBrief page="forecast" />}
        answer={t(
          <>
            Until {shortDate(n.forecastEnds, true)}, we expect about <Em>{num(n.expected)}</Em> parts to be used. <Em>{num(n.likely)}</Em> of them are more likely than not, and <Em tone="act">{num(n.shortLikely)}</Em> of those do not have enough stock. The turnaround on {shortDate(n.taDate, true)} comes on top: <Em tone="act">{num(n.shortKit)}</Em> of its {num(n.kit)} parts will be short.
          </>,
          <>
            Sampai {shortDate(n.forecastEnds, true)}, kami memperkirakan sekitar <Em>{num(n.expected)}</Em> suku cadang akan terpakai. <Em>{num(n.likely)}</Em> di antaranya lebih mungkin terpakai daripada tidak, dan <Em tone="act">{num(n.shortLikely)}</Em> dari jumlah itu stoknya tidak cukup. Turnaround pada {shortDate(n.taDate, true)} menambah kebutuhan: <Em tone="act">{num(n.shortKit)}</Em> dari {num(n.kit)} suku cadangnya akan kurang.
          </>,
        )}
      />

      <Part n={1} title={t("The answer, part by part", "Jawabannya, per suku cadang")} sub={t("What we have against what we will need. Press a part for the full picture.", "Yang kita miliki dibandingkan dengan yang akan kita butuhkan. Tekan sebuah suku cadang untuk gambaran lengkapnya.")} />
      <ol data-tour="f-likely" className="m-0 flex list-none items-stretch p-0" aria-label={t("From the whole catalogue to the parts that run short", "Dari seluruh katalog sampai suku cadang yang akan kurang")}>
        <Step first value={num(patternTotal)} label={t("Parts in the catalogue", "Suku cadang dalam katalog")} sub={t("Every part in the BoM", "Semua suku cadang di BoM")} />
        <Step value={num(n.likely)} label={t(`More likely than not by ${shortDate(n.forecastEnds)}`, `Lebih mungkin terpakai sampai ${shortDate(n.forecastEnds)}`)} sub={t(`of about ${num(n.expected)} expected`, `dari sekitar ${num(n.expected)} yang diperkirakan`)} hint={t(`Parts with at least a 1 in 2 chance of being used in the next 6 months, including parts with no use on record. Parts below that still get used: adding up every part's chance gives about ${num(n.expected)}. In the last 6 months, ${num(n.usedLately)} parts were used in normal work.`, `Suku cadang dengan peluang terpakai minimal 1 dari 2 dalam 6 bulan ke depan, termasuk yang belum memiliki catatan pemakaian. Suku cadang di bawah itu tetap bisa terpakai: jumlah peluang semua suku cadang sekitar ${num(n.expected)}. Dalam 6 bulan terakhir, ${num(n.usedLately)} suku cadang terpakai pada pekerjaan normal.`)} />
        <Step tone="act" value={num(n.shortLikely)} label={t("Run short in normal use", "Kurang pada pemakaian normal")} sub={t(`${num(n.shortBad)} in the bad case`, `${num(n.shortBad)} pada skenario terburuk`)} hint={t("Short means the most likely use is more than the stock on the shelf. The bad case is the high estimate, used to set safety stock.", "Kurang berarti pemakaian yang paling mungkin lebih besar daripada stok di rak. Skenario terburuk adalah taksiran tinggi yang dipakai untuk menetapkan stok pengaman.")} />
        <Step last tone="plan" value={num(n.shortKit)} label={t(`Plus the turnaround, ${shortDate(n.taDate)}`, `Ditambah turnaround, ${shortDate(n.taDate)}`)} sub={t(`of ${num(n.kit)} turnaround parts short`, `dari ${num(n.kit)} suku cadang turnaround kurang`)} hint={t(`The turnaround comes on top of normal use. Of the ${num(n.kit)} parts the last turnaround used, this many will not have enough by then, counting normal use until that day.`, `Turnaround menambah kebutuhan di atas pemakaian normal. Dari ${num(n.kit)} suku cadang yang dipakai pada turnaround sebelumnya, sebanyak ini tidak akan cukup pada saatnya, dengan memperhitungkan pemakaian normal sampai hari itu.`)} />
      </ol>
      <NeedTable rows={n.list} forecastEnds={n.forecastEnds} taDate={n.taDate} />

      <Part n={2} title={t("How we predict parts that are used irregularly", "Cara kami memprakirakan suku cadang yang pemakaiannya tidak teratur")} sub={t("Averages fail here, so we predict the chance of use and the amount separately, then simulate the range. Planned work is counted on its own.", "Rata-rata tidak bisa diandalkan di sini, jadi peluang terpakai dan jumlahnya diprakirakan terpisah, lalu rentangnya disimulasikan. Pekerjaan terencana dihitung tersendiri.")} />
      <Panel tour="f-patterns">
        <PanelHead title={t("Six use patterns, one model", "Enam pola pemakaian, satu model")} aside={<span className="text-[12px] text-ink-3">{t(`${num(patternTotal)} parts, grouped by how they were used in 17 months`, `${num(patternTotal)} suku cadang, dikelompokkan menurut pola pemakaiannya selama 17 bulan`)}</span>} />
        <p className="m-0 px-5 pt-1 text-[13px] leading-[1.5] text-ink-2">{t("The groups describe the parts, they do not pick a method. The same two models and the same simulation run on every part, and what they can lean on changes with its history.", "Kelompok ini menggambarkan suku cadangnya, bukan memilih metode. Dua model dan simulasi yang sama berjalan pada setiap suku cadang, dan yang bisa dijadikan sandaran berubah mengikuti riwayatnya.")}</p>
        <ul className="m-0 grid list-none grid-cols-2 gap-px overflow-hidden rounded-b-[20px] p-0 pt-3 lg:grid-cols-6">
          {PATTERNS.map((x) => {
            const c = o.patterns.find((y) => y.demand_class === x.key)?.n ?? 0;
            return (
              <li key={x.key} className="border-t border-line px-5 py-3 lg:border-l lg:first:border-l-0">
                <div className="text-[20px] font-semibold leading-none tabular-nums">{num(c)}</div>
                <div className="mt-1.5 text-[13px] font-medium">{x.name}</div>
                <p className="m-0 mt-1 text-[12px] leading-snug text-ink-3">{x.how}</p>
              </li>
            );
          })}
        </ul>
      </Panel>

      <Panel tour="f-months">
        <PanelHead
          title={t("Turnaround work is planned on its own", "Pekerjaan turnaround direncanakan tersendiri")}
          aside={
            <span className="flex items-center gap-3 text-[12px] text-ink-3">
              <span className="inline-flex items-center gap-1.5"><span className="h-2 w-2 rounded-full bg-ink-2" />{t("Normal work", "Pekerjaan normal")}</span>
              <span className="inline-flex items-center gap-1.5"><span className="h-2 w-2 rounded-full bg-plan" />{t("Turnaround work", "Pekerjaan turnaround")}</span>
            </span>
          }
        />
        <p className="m-0 px-5 pt-1 text-[13px] leading-[1.5] text-ink-2">{t("Different parts used each month. Orange peaks in Nov–Jan, the last turnaround, so it is planned as one event instead of being spread across every month.", "Jumlah jenis suku cadang yang dipakai setiap bulan. Warna oranye memuncak pada Nov–Jan, saat turnaround terakhir, sehingga turnaround direncanakan sebagai satu kejadian alih-alih disebar ke setiap bulan.")}</p>
        <div className="px-4 pb-3 pt-3"><PlantChart rows={rows} /></div>
      </Panel>

      {maintenance && <MaintenanceAhead {...maintenance} taDate={n.taDate} />}

      <div className="grid grid-cols-3 gap-4">
        <Panel>
          <PanelHead title={t("Chance of use, by how critical", "Peluang terpakai, menurut kekritisan")} />
          <div className="space-y-3 px-5 pb-5 pt-4">
            {CRITS.map((c) => {
              const r = o.likely.filter((l) => l.criticality === c);
              const tot = r.reduce((a, b) => a + b.n, 0);
              return (
                <div key={c} className="grid grid-cols-[auto_minmax(0,1fr)_56px] items-center gap-3">
                  <CritTile crit={c} size="md" />
                  <div className="flex h-6 overflow-hidden rounded-[7px]" role="img" aria-label={t(`Criticality ${c}`, `Kekritisan ${c}`)}>
                    {BANDS.map((b) => {
                      const v = r.find((x) => x.band === b.key)?.n ?? 0;
                      return v ? <div key={b.key} className={cn("h-full border-r-2 border-panel last:border-r-0", b.tone)} style={{ width: `${(v / tot) * 100}%` }} title={`${b.label}: ${v}`} /> : null;
                    })}
                  </div>
                  <span className="text-right text-[12.5px] tabular-nums text-ink-3">{num(tot)}</span>
                </div>
              );
            })}
            <div className="flex flex-wrap gap-4 pt-1 text-[12px] text-ink-3">
              {BANDS.map((b) => (
                <span key={b.key} className="inline-flex items-center gap-1.5"><span className={cn("h-2.5 w-2.5 rounded-[3px]", b.tone)} />{b.label}</span>
              ))}
            </div>
          </div>
        </Panel>

        <Panel>
          <PanelHead title={t("No use on record, likely needed, none on the shelf", "Belum pernah dipakai, kemungkinan dibutuhkan, rak kosong")} icon={Snowflake} />
          <ul className="m-0 mt-2 list-none divide-y divide-line p-0">
            {o.hidden.map((h) => (
              <li key={h.material_no}>
                <Link href={`/parts/${h.material_no}`} className="flex items-center gap-3 px-5 py-2.5 transition-colors hover:bg-ink/[0.02]">
                  <CritTile crit={h.criticality} />
                  <span className="min-w-0 flex-1">
                    <span className="block truncate text-[13.5px] font-medium">{partName(h.description)}</span>
                    <span className="mt-0.5 flex gap-3 text-[12px] text-ink-3">
                      <span className="inline-flex items-center gap-1"><MapPin aria-hidden className="h-3.5 w-3.5" />{t(`installed in ${num(h.n_funcloc)} places`, `terpasang di ${num(h.n_funcloc)} lokasi`)}</span>
                      <span className="inline-flex items-center gap-1"><Truck aria-hidden className="h-3.5 w-3.5" />{t(`${num(h.lt_p90)} days to deliver`, `${num(h.lt_p90)} hari pengiriman`)}</span>
                    </span>
                  </span>
                  <span className="shrink-0 rounded-[7px] bg-watch-soft px-2 py-1 text-[12px] font-medium text-watch-ink">{chance(h.p_move)}</span>
                </Link>
              </li>
            ))}
          </ul>
        </Panel>

        <Panel className="flex flex-col">
          <PanelHead title={t("Unusual use, last 6 months", "Pemakaian tidak biasa, 6 bulan terakhir")} icon={Activity} aside={<span className="text-[12px] tabular-nums text-ink-3">{t(`${num(odd.total)} parts`, `${num(odd.total)} suku cadang`)}</span>} />
          <p className="m-0 mt-1 px-5 text-[12.5px] leading-snug text-ink-3">{t("A normal month with 3 times the part's usual use or more. One-off, or a new normal? Ask before changing its stock limits.", "Bulan biasa dengan pemakaian 3 kali lipat atau lebih dari biasanya. Hanya sekali, atau pola baru? Tanyakan dulu sebelum mengubah batas stoknya.")}</p>
          <ul className="m-0 mt-2 list-none divide-y divide-line p-0">
            {odd.items.map((x) => (
              <li key={x.material_no}>
                <Link href={`/parts/${x.material_no}`} className="flex items-center gap-3 px-5 py-2.5 transition-colors hover:bg-ink/[0.02]">
                  <CritTile crit={x.criticality} />
                  <span className="min-w-0 flex-1">
                    <span className="block truncate text-[13.5px] font-medium">{partName(x.description)}</span>
                    <span className="mt-0.5 block text-[12px] tabular-nums text-ink-3">{t(`${amount(x.unusual!.qty, x.unit)} in ${shortDate(`${x.unusual!.month}-01`).split(" ").slice(1).join(" ")}, usually ${amount(x.unusual!.usual, x.unit)}`, `${amount(x.unusual!.qty, x.unit)} pada ${shortDate(`${x.unusual!.month}-01`).split(" ").slice(1).join(" ")}, biasanya ${amount(x.unusual!.usual, x.unit)}`)}</span>
                  </span>
                  <span className="shrink-0 rounded-[7px] bg-watch-soft px-2 py-1 text-[12px] font-medium tabular-nums text-watch-ink">{num(x.unusual!.ratio, 1)}×</span>
                </Link>
              </li>
            ))}
          </ul>
          <Link href="/todo?view=unusual" className="mt-auto flex items-center justify-between gap-3 border-t border-line px-5 py-3 text-[13px] text-ink-2 transition-colors hover:bg-ink/[0.02]">
            {t("See them all on the To do board", "Lihat semuanya di papan Tugas")}
            <ArrowRight aria-hidden className="h-4 w-4 text-ink-3" />
          </Link>
        </Panel>
      </div>

      <Part n={3} title={t("Why you can believe it", "Mengapa hasil ini bisa dipercaya")} sub={t("Tested on months the model never saw, then replayed on real use.", "Diuji pada bulan-bulan yang belum pernah dilihat model, lalu diputar ulang dengan pemakaian riil.")} />
      <div className="grid grid-cols-2 gap-4">
        <Panel tour="f-score" className="flex flex-col p-5">
          <div className="flex items-center gap-2 text-[14px] font-semibold"><ShieldCheck aria-hidden className="h-4 w-4 text-ink-3" />{t("How often does it pick the right part?", "Seberapa sering model memilih suku cadang yang tepat?")}</div>
          <p className="m-0 mt-1 text-[12.5px] leading-snug text-ink-3">{t("Take one part that got used and one that did not. Out of 100 such pairs, how often does it rank the used one higher?", "Ambil satu suku cadang yang terpakai dan satu yang tidak. Dari 100 pasangan seperti itu, seberapa sering model menempatkan yang terpakai di peringkat lebih tinggi?")}</p>
          <div className="mt-3 space-y-3">
            <Versus label={t("All parts", "Semua suku cadang")} a={p.engine} b={p.baseline} bLabel={t("Simply assuming the last 90 days repeat", "Sekadar mengasumsikan 90 hari terakhir terulang")} />
            <Versus label={t("Parts with no use on record", "Suku cadang tanpa catatan pemakaian")} a={p.engineColdHoldout} b={p.classicCold} bLabel={t("Classic spare-part formula, same test months", "Rumus suku cadang klasik, pada bulan uji yang sama")} />
          </div>
          <p className="m-0 mt-auto pt-3 text-[12px] leading-snug text-ink-3">
            {t(
              <>
                All parts: average of four monthly tests. No use on record: one hold-out test, the only one the classic formula was run on (the four monthly tests give {pc(p.engineCold)}).{m.strict && <> These scores use today&apos;s Min and Max as a clue. Without that clue: {pc(m.strict.auc_all)} for all parts, {pc(m.strict.auc_cold)} for parts with no use on record.</>}{" "}
                On how many units, it is no better than assuming the last 90 days repeat, so stock limits are set from the range of likely use during delivery, not one number. The replay on the right is the test that counts.{p.coverUsed != null && <> The 180-day high estimate alone covered the real use of about {pc(p.coverUsed)}% of the parts that were used.</>}{" "}
                <Link href="/check" className="underline underline-offset-2">See how this was checked</Link>
              </>,
              <>
                Semua suku cadang: rata-rata empat uji bulanan. Tanpa catatan pemakaian: satu uji hold-out, satu-satunya uji yang juga dijalankan dengan rumus klasik (empat uji bulanan memberi {pc(p.engineCold)}).{m.strict && <> Skor ini memakai Min dan Max saat ini sebagai petunjuk. Tanpa petunjuk itu: {pc(m.strict.auc_all)} untuk semua suku cadang, {pc(m.strict.auc_cold)} untuk suku cadang tanpa catatan pemakaian.</>}{" "}
                Untuk jumlah unit, model ini tidak lebih baik daripada asumsi bahwa 90 hari terakhir terulang, sehingga batas stok ditetapkan dari rentang pemakaian yang mungkin terjadi selama masa pengiriman, bukan dari satu angka. Simulasi ulang di sebelah kanan adalah uji yang menentukan.{p.coverUsed != null && <> Taksiran tinggi 180 hari saja sudah menutup pemakaian riil sekitar {pc(p.coverUsed)}% suku cadang yang terpakai.</>}{" "}
                <Link href="/check" className="underline underline-offset-2">Lihat cara pemeriksaannya</Link>
              </>,
            )}
          </p>
        </Panel>

        <Panel tour="f-replay" className="flex flex-col p-5">
          <div className="flex items-center gap-2 text-[14px] font-semibold"><Wallet aria-hidden className="h-4 w-4 text-ink-3" />{t("Would it have worked? Replay of real use, Mar–Sep 2026", "Apakah akan berhasil? Simulasi ulang pemakaian riil, Mar–Sep 2026")}</div>
          {now && lean ? (
            <>
              <div className="mt-3 flex items-baseline gap-2">
                <span className="text-[40px] font-semibold leading-none tracking-[-0.02em] tabular-nums text-ready-ink">{Math.round(lean.fill_units * 100)}%</span>
                <span className="text-[13px] text-ink-3">{t(`of the critical stocked parts requested were on the shelf, up from ${Math.round(now.fill_units * 100)}%`, `suku cadang kritis yang distok dan diminta tersedia di rak, naik dari ${Math.round(now.fill_units * 100)}%`)}</span>
              </div>
              <table className="mt-auto w-full border-collapse text-[12.5px] tabular-nums">
                <thead>
                  <tr className="border-b border-line text-left text-[11.5px] font-medium text-ink-3">
                    <th className="py-1.5 pr-2 font-medium">{t("Stock limits", "Batas stok")}</th>
                    <th className="py-1.5 pr-2 text-right font-medium">{t("On the shelf", "Tersedia di rak")}</th>
                    <th className="py-1.5 pr-2 text-right font-medium">{t("Empty-shelf days", "Hari rak kosong")}</th>
                    <th className="py-1.5 text-right font-medium">{t("Average stock, all stocked parts", "Rata-rata stok, semua yang distok")}</th>
                  </tr>
                </thead>
                <tbody>
                  {([
                    [t("Today's Min and Max", "Min dan Max saat ini"), now, false],
                    ["Sparekit", lean, true],
                  ] as const).map(([label, r, ours]) => (
                    <tr key={label} className={cn("border-b border-line last:border-b-0", ours && "font-semibold text-ready-ink")}>
                      <td className="py-1.5 pr-2 text-ink-2">{ours ? <span className="text-ready-ink">{label}</span> : label}</td>
                      <td className="py-1.5 pr-2 text-right">{Math.round(r.fill_units * 100)}%</td>
                      <td className="py-1.5 pr-2 text-right">{num(r.stockout_days)}</td>
                      <td className="py-1.5 text-right">{rp(r.avg_inv_idr)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <p className="m-0 mt-2 text-[12px] leading-snug text-ink-3">{t(`Availability counts the ${num(replay?.sparekit.parts ?? 0)} critical stocked parts that were used; stock value counts all ${num(replay?.stocked ?? 0)} stocked parts. Non Stock parts are left out, because they are bought per job. Each plan starts with stock at its own Max, and limits are updated monthly. Stock value uses the median price of the same part type where a part has no purchase order. On parts with a PO price alone it rises from ${rp(now.avg_inv_idr_po)} to ${rp(lean.avg_inv_idr_po)}: money moves out of idle parts and into parts that get used.`, `Ketersediaan dihitung pada ${num(replay?.sparekit.parts ?? 0)} suku cadang kritis yang distok dan terpakai; nilai stok dihitung pada seluruh ${num(replay?.stocked ?? 0)} suku cadang yang distok. Suku cadang Non Stock tidak dihitung karena dibeli per pekerjaan. Setiap rencana dimulai dengan stok pada Max-nya sendiri, dan batas diperbarui setiap bulan. Nilai stok memakai harga median jenis suku cadang yang sama jika belum pernah dipesan. Khusus suku cadang berharga PO, nilainya naik dari ${rp(now.avg_inv_idr_po)} menjadi ${rp(lean.avg_inv_idr_po)}: uang berpindah dari suku cadang yang menganggur ke yang benar-benar terpakai.`)}</p>
              <Link href="/replay" className="mt-2 inline-flex items-center gap-1.5 text-[13px] font-medium underline underline-offset-2">{t("Play it month by month", "Putar bulan demi bulan")}<ArrowRight aria-hidden className="h-4 w-4" /></Link>
            </>
          ) : (
            <p className="m-0 mt-3 text-[13px] text-ink-3">{t("The replay has not been run yet.", "Simulasi ulang belum dijalankan.")}</p>
          )}
        </Panel>
      </div>
    </div>
  );
}

function Versus({ label, a, b, bLabel }: { label: string; a: number | null; b: number | null; bLabel: string }) {
  return (
    <div>
      <div className="flex items-baseline justify-between text-[12.5px] text-ink-2">
        <span>{label}</span>
        <span className="tabular-nums"><b className="text-[16px] font-semibold text-ready-ink">{pc(a)}</b> vs {pc(b)}</span>
      </div>
      <div className="relative mt-1 h-2 overflow-hidden rounded-full bg-ink/[0.06]" role="img" aria-label={t(`Sparekit ${pc(a)}, ${bLabel} ${pc(b)}, of 100`, `Sparekit ${pc(a)}, ${bLabel} ${pc(b)}, dari 100`)}>
        <div className="absolute inset-y-0 left-0 rounded-full bg-ready" style={{ width: `${(a ?? 0) * 100}%` }} />
        <div className="absolute inset-y-0 w-0.5 bg-ink" style={{ left: `${(b ?? 0) * 100}%` }} title={bLabel} />
      </div>
      <div className="mt-0.5 text-[11.5px] text-ink-3">{t("Black mark: ", "Tanda hitam: ")}{bLabel}</div>
    </div>
  );
}

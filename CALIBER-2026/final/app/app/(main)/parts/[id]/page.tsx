import { Suspense } from "react";
import Link from "next/link";
import { notFound } from "next/navigation";
import { ArrowDown, ArrowLeft } from "lucide-react";
import { MapPin, Siren, Truck, History, Wrench, BadgeCheck, CircleDashed, ArrowLeftRight, Snowflake, ChartColumn, Wallet, ShieldCheck, type LucideIcon } from "@/components/icons";
import { part, partAnswer, replayPart, taskFor } from "@/lib/data";
import {
  type Action,
  type Crit,
  ACTION_STATUS,
  categoryName,
  chance,
  cn,
  num,
  partName,
  amount,
  plainReason,
  qty,
  rp,
  shortDate,
  CRIT_NAME,
} from "@/lib/format";
import { CritTile, Panel, PanelHead, STATUS_TONE } from "@/components/ui";
import { buyBasis, buyNote } from "@/lib/people";
import { PartAnswer } from "@/components/part-answer";
import { ReviewInTodo, TaskStatus } from "@/components/task-status";
import { RangeGauge } from "@/components/range-gauge";
import { LimitsHistory } from "@/components/limits-history";
import { DemandChart } from "@/components/demand-chart";
import { t } from "@/lib/i18n";
import { getLang, titled } from "@/lib/i18n-server";

export const generateMetadata = titled("Part", "Suku cadang");

export default function Page({ params }: { params: Promise<{ id: string }> }) {
  return (
    <Suspense fallback={<div className="h-[60vh] animate-pulse rounded-[16px] bg-ink/[0.04]" />}>
      <PartDetail params={params} />
    </Suspense>
  );
}

const driverWords = (): Record<string, string> => ({
  fl_pm: t("planned maintenance items on its equipment", "item pemeliharaan terencana pada peralatannya"),
  fl_notif: t("notifications on its equipment", "laporan kerusakan pada peralatannya"),
  fl_emerg: t("emergency notifications on its equipment", "laporan darurat pada peralatannya"),
  inst: t("units installed", "unit terpasang"),
  n_fl: t("places it is installed", "lokasi pemasangan"),
  qty_90: t("units used per month lately", "unit terpakai per bulan belakangan ini"),
  lines_90: t("issues per month lately", "pengeluaran per bulan belakangan ini"),
  n_pr: t("purchase requests per month", "permintaan pembelian per bulan"),
  act_months: t("months it was used", "bulan terpakai"),
  recency: t("days since last use", "hari sejak terakhir dipakai"),
});

type M = Record<string, unknown> & {
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
  n_funcloc: number;
  lt_p50: number;
  lt_p90: number;
  lt_source: string;
  main_supplier: string | null;
  months_active: number;
  last_issue: string | null;
  trust_score: number;
  price_source: string;
  unit_price: number | null;
  stock_value: number | null;
  p_move: number;
  q50: number;
  q90: number;
  q95: number;
  base_qty: number;
  event_qty: number;
  ltd_mean: number;
  ltd_var: number;
  cold_start: number;
  drivers: string | null;
  service_level: number;
  safety_stock: number;
  rop: number;
  hold_cost_yr: number;
  risk_cost_yr: number;
  mrp_type: string;
};

async function PartDetail({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  await getLang();
  const DRIVER_WORDS = driverWords();
  const data = part(Number(id));
  if (!data) notFound();
  const m = data.m as unknown as M;
  const st = ACTION_STATUS[m.action];
  const name = partName(m.description);

  const task = taskFor(m.material_no);
  const answer = partAnswer(m.material_no);
  const replay = replayPart(m.material_no);

  const history = data.months.map((mo) => {
    const h = data.history.find((x) => x.month === mo);
    return { month: mo, routine: h ? Math.max(0, h.qty - h.qty_ta) : 0, ta: h ? h.qty_ta : 0 };
  });
  const donor = data.twins.filter((t) => t.role === "DONOR" && t.stock > t.max_cur).sort((a, b) => b.stock - b.max_cur - (a.stock - a.max_cur))[0];

  let drivers: Record<string, unknown> = {};
  try {
    drivers = m.drivers ? JSON.parse(m.drivers) : {};
  } catch {}
  const notif = Number(drivers.fl_notif_90d ?? 0);


  const why: { icon: LucideIcon; value: string; label: string }[] = [
    { icon: MapPin, value: num(m.n_funcloc), label: t(m.n_funcloc === 1 ? "place it is installed" : "places it is installed", "lokasi pemasangan") },
    { icon: Siren, value: num(notif), label: t("breakdown notices on that equipment, last 90 days", "laporan kerusakan pada peralatan itu, 90 hari terakhir") },
    { icon: Truck, value: t(`${num(m.lt_p90)} days`, `${num(m.lt_p90)} hari`), label: t("slow-case delivery time", "waktu kirim skenario lambat") },
    { icon: History, value: `${m.months_active} / 17`, label: t("months it was used", "bulan terpakai") },
  ];
  for (const [k, v] of Object.entries(drivers)) {
    if (k === "fl_notif_90d" || !DRIVER_WORDS[k] || why.length >= 5) continue;
    if (k === "n_fl" || k === "act_months") continue;
    why.push({ icon: Wrench, value: num(Number(v), 1), label: DRIVER_WORDS[k] });
  }

  const trust = m.trust_score >= 0.7 ? "high" : m.trust_score >= 0.4 ? "medium" : "low";
  const trustLevel = trust === "high" ? t("High", "Tinggi") : trust === "medium" ? t("Medium", "Sedang") : t("Check first", "Periksa dulu");
  const p10 = Math.round(Math.max(0, Math.min(1, m.p_move)) * 10);

  const exposure = m.risk_cost_yr > 0 ? (m.risk_cost_yr / 100) * 5e6 : 0;
  const branches: { href: string; title: string; now: string }[] = [
    { href: "#why", title: t("Why that much?", "Mengapa sebanyak itu?"), now: t(`Used in ${m.months_active} of 17 months, ${chance(m.p_move)} chance of use`, `Terpakai ${m.months_active} dari 17 bulan, peluang terpakai ${chance(m.p_move)}`) },
    { href: "#limits", title: t("Stock limits", "Batas stok"), now: t(`Max ${qty(m.max_cur, m.unit)} in SAP, we suggest ${qty(m.max_new, m.unit)}`, `Max ${qty(m.max_cur, m.unit)} di SAP, kami sarankan ${qty(m.max_new, m.unit)}`) },
    { href: "#cost", title: t("Cost and risk", "Biaya dan risiko"), now: m.hold_cost_yr > 0 ? t(`Keeping it costs ${rp(m.hold_cost_yr)} a year`, `Biaya penyimpanannya ${rp(m.hold_cost_yr)} per tahun`) : t("Nothing on the shelf to pay for", "Tidak ada stok di rak yang perlu dibiayai") },
    { href: "#trust", title: t("Can we trust it?", "Bisakah dipercaya?"), now: t(`Data check: ${trustLevel}`, `Cek data: ${trustLevel}`) },
  ];

  return (
    <div className="space-y-5">
      <Link href="/todo" className="inline-flex items-center gap-1.5 text-[13px] text-ink-3 hover:text-ink">
        <ArrowLeft className="h-4 w-4" aria-hidden />
        {t("To do", "Tugas")}
      </Link>

      <header className="flex items-start gap-3">
        <CritTile crit={m.criticality} size="lg" />
        <div className="min-w-0">
          <h1 className="m-0 font-display text-[26px] font-semibold leading-[1.15] tracking-[-0.012em] sm:text-[30px]">{name}</h1>
          <p className="m-0 mt-1 text-[12.5px] text-ink-3">
            {CRIT_NAME[m.criticality]} · {categoryName(m.category)} · {t("Part no.", "No. part")} {m.material_no} · {m.mrp_type === "Stock Item" ? t("Kept in stock", "Distok") : t("Not kept in stock today", "Saat ini tidak distok")}
            {data.equipment.length > 0 && <> · {t("Used on", "Dipakai di")} {data.equipment.slice(0, 3).join(", ")}</>}
            {data.standby.length > 0 && <> · {t("Standby unit", "Unit siaga")}: {data.standby.slice(0, 2).map((x) => `${x.unit} ${t("with", "dengan")} ${x.standby.join(", ")}`).join("; ")}{t(", so one can run while the other waits", ", jadi satu bisa beroperasi sementara yang lain bersiaga")}</>}
          </p>
        </div>
      </header>

      {task && buyNote(buyBasis(task)) && <p className="m-0 -mb-2 text-[13px] leading-snug text-plan-ink">{buyNote(buyBasis(task))}</p>}
      {answer && <PartAnswer a={answer} task={task} action={task ? <ReviewInTodo id={m.material_no} /> : undefined} status={task ? <TaskStatus id={m.material_no} kind={task.kind} section={task.section} /> : undefined} />}

      <nav aria-label={t("More about this part", "Selengkapnya tentang suku cadang ini")} className="grid grid-cols-2 gap-2 lg:grid-cols-4">
        {branches.map((b) => (
          <a key={b.href} href={b.href} className="group flex items-center gap-2 rounded-[12px] border border-line bg-panel px-3.5 py-2.5 transition-colors hover:border-line-2">
            <span className="min-w-0 flex-1">
              <span className="block text-[13px] font-semibold">{b.title}</span>
              <span className="block truncate text-[12px] text-ink-3" title={b.now}>{b.now}</span>
            </span>
            <ArrowDown aria-hidden className="h-3.5 w-3.5 shrink-0 text-ink-4 transition-transform group-hover:translate-y-0.5" />
          </a>
        ))}
      </nav>

      <div id="why" className="scroll-mt-4 space-y-4">
        <h2 className="m-0 pt-2 text-[16px] font-semibold">{t("Why that much?", "Mengapa sebanyak itu?")}</h2>
        {m.cold_start === 1 && (
          <div className="squircle flex items-start gap-3 rounded-[14px] bg-watch-soft px-4 py-3 text-watch-ink">
            <Snowflake className="mt-0.5 h-5 w-5 shrink-0" aria-hidden />
            <p className="m-0 text-[13.5px] leading-relaxed">
              {t("No use in the last 17 months. The estimate borrows from similar parts on similar equipment. A forecast based only on history would say zero.", "Tidak ada pemakaian dalam 17 bulan terakhir. Taksirannya meminjam data suku cadang serupa pada peralatan serupa. Prakiraan yang hanya berdasarkan riwayat akan menghasilkan nol.")}
            </p>
          </div>
        )}
        <div className="grid gap-4 lg:grid-cols-[minmax(0,1.5fr)_minmax(0,1fr)]">
          <Panel>
            <PanelHead
              title={t("How it was used, last 17 months", "Riwayat pemakaian, 17 bulan terakhir")}
              icon={History}
              aside={
                <span className="flex items-center gap-3 text-[12px] text-ink-3">
                  <span className="inline-flex items-center gap-1.5"><span className="h-2 w-2 rounded-full bg-ink-2" />{t("Normal", "Normal")}</span>
                  <span className="inline-flex items-center gap-1.5"><span className="h-2 w-2 rounded-full bg-plan" />{t("Turnaround", "Turnaround")}</span>
                </span>
              }
            />
            <div className="px-3 pb-4 pt-2 sm:px-4">
              {history.some((h) => h.routine + h.ta > 0) ? (
                <DemandChart rows={history} unit={m.unit} />
              ) : (
                <p className="m-0 px-2 py-10 text-center text-[13.5px] text-ink-3">{t("No use recorded in this window.", "Tidak ada pemakaian tercatat dalam rentang ini.")}</p>
              )}
            </div>
          </Panel>
          <Panel>
            <PanelHead title={t("Next 6 months", "6 bulan ke depan")} icon={ChartColumn} />
            <div className="space-y-5 px-5 pb-5 pt-3">
              <div>
                <div className="flex items-baseline justify-between">
                  <span className="text-[13px] text-ink-2">{t("Chance it is needed", "Peluang dibutuhkan")}</span>
                  <span className="font-display text-[20px] font-semibold">{chance(m.p_move)}</span>
                </div>
                <div className="mt-2 grid grid-cols-10 gap-1.5" aria-hidden>
                  {Array.from({ length: 10 }, (_, i) => (
                    <span key={i} className={cn("aspect-square rounded-full", i < p10 ? STATUS_TONE[st === "ready" ? "watch" : st].solid : "bg-ink/[0.08]")} />
                  ))}
                </div>
              </div>
              <div>
                <div className="flex items-baseline justify-between">
                  <span className="text-[13px] text-ink-2">{t("How many", "Berapa banyak")}</span>
                  <span className="text-[13px] text-ink-3">
                    {t("most likely", "paling mungkin")} <span className="font-semibold text-ink">{qty(m.q50, m.unit)}</span>, {t("bad case", "terburuk")} <span className="font-semibold text-ink">{amount(m.q95, m.unit)}</span>
                  </span>
                </div>
                <QtyRange q50={m.q50} q95={m.q95} stock={m.stock} />
              </div>
            </div>
          </Panel>
        </div>
        <ul className="m-0 grid list-none gap-2.5 p-0 sm:grid-cols-2 lg:grid-cols-5">
          {why.map((w) => (
            <li key={w.label} className="squircle flex items-center gap-3 rounded-[12px] bg-ink/[0.035] px-3.5 py-3">
              <w.icon className="h-5 w-5 shrink-0 text-ink-3" aria-hidden />
              <div className="min-w-0">
                <div className="font-display text-[19px] font-semibold leading-none text-ink">{w.value}</div>
                <div className="mt-1 text-[12px] leading-snug text-ink-3">{w.label}</div>
              </div>
            </li>
          ))}
        </ul>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div id="limits" className="scroll-mt-4">
          <Panel className="h-full">
            <PanelHead title={t("Stock limits", "Batas stok")} />
            <p className="m-0 px-5 pt-1 text-[12.5px] leading-snug text-ink-3">{t("Min is the reorder point: when stock falls to it, order. Max is the upper limit. The black pin is the stock on the shelf today.", "Min adalah reorder point: saat stok turun sampai batas ini, lakukan pemesanan. Max adalah batas atas. Penanda hitam menunjukkan stok di rak hari ini.")}</p>
            <div className="px-5 pb-5 pt-2">
              <RangeGauge stock={m.stock} minCur={m.min_cur} maxCur={m.max_cur} minNew={m.min_new} maxNew={m.max_new} unit={m.unit} status={st} size="lg" />
            </div>
          </Panel>
        </div>
        <div id="cost" className="scroll-mt-4">
          <Panel className="h-full">
            <PanelHead title={t("Cost and risk", "Biaya dan risiko")} icon={Wallet} />
            <dl className="m-0 divide-y divide-line px-5 pb-3 pt-2 text-[13px]">
              <div className="flex justify-between gap-4 py-2"><dt className="text-ink-2">{t("Value on the shelf", "Nilai di rak")}</dt><dd className="m-0 font-medium tabular-nums">{m.stock_value ? rp(m.stock_value) : t("Nothing", "Tidak ada")}</dd></div>
              <div className="flex justify-between gap-4 py-2"><dt className="text-ink-2">{t("Keeping it, per year", "Biaya penyimpanan per tahun")}</dt><dd className="m-0 font-medium tabular-nums">{rp(m.hold_cost_yr)}</dd></div>
              {task?.value != null && <div className="flex justify-between gap-4 py-2"><dt className="text-ink-2">{task.kind === "reduce" || task.kind === "dispose" ? t("Money to free", "Dana yang bisa dibebaskan") : t("Cost of this action", "Biaya tindakan ini")}</dt><dd className="m-0 font-medium tabular-nums">{rp(task.value)}</dd></div>}
              <div className="flex justify-between gap-4 py-2"><dt className="text-ink-2">{t("If it runs out, per year", "Jika kehabisan, per tahun")} <span className="text-ink-3">{t(`(assumes ${rp(5e6)} a day for an A part)`, `(dengan asumsi ${rp(5e6)} per hari untuk suku cadang A)`)}</span></dt><dd className="m-0 shrink-0 font-medium tabular-nums">{rp(exposure)}</dd></div>
            </dl>
          </Panel>
        </div>
      </div>

      {replay ? (
        <Panel className="p-5">
          <div className="flex flex-wrap items-baseline justify-between gap-3">
            <h2 className="m-0 text-[14px] font-semibold">{t("How its limits moved, replay of March to September 2026", "Pergerakan batas stoknya, simulasi ulang Maret sampai September 2026")}</h2>
            <Link href="/replay" className="text-[12.5px] text-ink-2 underline underline-offset-2">{t("See the whole replay", "Lihat seluruh simulasi ulang")}</Link>
          </div>
          <div className="mt-2"><LimitsHistory part={replay} /></div>
        </Panel>
      ) : (
        <p className="m-0 text-[12.5px] leading-snug text-ink-3">{t("The replay of March to September 2026 covers critical stocked parts that were used in those months, so this part has no month-by-month history. ", "Simulasi ulang Maret sampai September 2026 mencakup suku cadang kritis yang distok dan terpakai pada bulan-bulan itu, jadi suku cadang ini tidak memiliki riwayat bulanan. ")}<Link href="/replay" className="underline underline-offset-2">{t("See the replay", "Lihat simulasi ulang")}</Link>.</p>
      )}

      <div id="trust" className="grid scroll-mt-4 gap-4 lg:grid-cols-2">
        <Panel>
          <PanelHead title={t("Can we trust it?", "Bisakah dipercaya?")} icon={ShieldCheck} aside={<span className={cn("text-[12.5px] font-semibold", trust === "high" ? "text-ready-ink" : trust === "medium" ? "text-plan-ink" : "text-act-ink")}>{trustLevel}</span>} />
          <ul className="m-0 list-none space-y-2.5 p-5 pt-3 text-[13px]">
            <Check ok={m.price_source === "po"} yes={t("Price from purchase orders", "Harga dari pesanan pembelian")} no={t("Price estimated from its category", "Harga ditaksir dari kategorinya")} />
            <Check ok={m.lt_source === "material"} yes={t("Delivery time from this part's own orders", "Waktu kirim dari pesanan suku cadang ini sendiri")} no={t("Delivery time from the average of its category", "Waktu kirim dari rata-rata kategorinya")} />
            {m.lt_p90 > 365 && <Check ok={false} yes="" no={t(`Slow-case delivery is over a year (${num(m.lt_p90)} days). Confirm with procurement: the order may carry a planned date, not the supplier's time`, `Waktu kirim skenario lambat lebih dari setahun (${num(m.lt_p90)} hari). Konfirmasikan ke bagian pengadaan: pesanan itu mungkin memuat tanggal rencana, bukan waktu dari pemasok`)} />}
            <Check ok={m.trust_score >= 0.5} yes={t("Stock record looks consistent", "Catatan stok tampak konsisten")} no={t("Count the shelf before ordering", "Hitung isi rak sebelum memesan")} />
          </ul>
        </Panel>
        {donor && (
          <section className="squircle rounded-[16px] bg-twin-soft p-5 text-twin-ink">
            <div className="flex items-center gap-2">
              <ArrowLeftRight className="h-5 w-5" aria-hidden />
              <h2 className="m-0 text-[14px] font-semibold">{t("Same part, another number (duplicate)", "Suku cadang sama, nomor berbeda (kembar)")}</h2>
            </div>
            <p className="m-0 mt-2 text-[13.5px] leading-relaxed">
              {t(
                <>Part no. {donor.material_no} holds <span className="font-semibold">{amount(donor.stock - donor.max_cur, m.unit)}</span> above its Max. Move it before buying new.</>,
                <>No. part {donor.material_no} menyimpan <span className="font-semibold">{amount(donor.stock - donor.max_cur, m.unit)}</span> di atas Max-nya. Pindahkan stok itu sebelum membeli yang baru.</>,
              )}
            </p>
            <Link href={`/parts/${donor.material_no}`} className="mt-3 inline-flex text-[13px] font-medium underline decoration-twin/40 underline-offset-4">
              {t("Open the duplicate part", "Buka suku cadang kembar")}
            </Link>
          </section>
        )}
      </div>

      <details className="group squircle rounded-[16px] border border-line bg-panel">
        <summary className="flex cursor-pointer list-none items-center justify-between px-5 py-4 text-[14px] font-semibold">
          {t("Show the math", "Tampilkan perhitungannya")}
          <span className="text-[12.5px] font-normal text-ink-3 group-open:hidden">{t("Every number behind this recommendation", "Semua angka di balik rekomendasi ini")}</span>
        </summary>
        <div className="border-t border-line px-5 py-4">
          <dl className="m-0 grid grid-cols-2 gap-x-6 gap-y-3 text-[13px] sm:grid-cols-4">
            {[
              [t("Target availability", "Target ketersediaan"), `${(m.service_level * 100).toFixed(0)}%`],
              [t("Safety stock (extra kept as a cushion)", "Safety stock (stok pengaman)"), num(m.safety_stock, 1)],
              [t("Reorder point, the new Min (order when stock falls to it)", "Reorder point, yaitu Min baru (pesan saat stok turun sampai batas ini)"), num(m.rop, 1)],
              [t("New Max (upper limit)", "Max baru (batas atas)"), num(m.max_new, 1)],
              [t("Chance of use in 6 months", "Peluang terpakai dalam 6 bulan"), `${(m.p_move * 100).toFixed(0)}%`],
              [t("Expected use: likely / high / bad case", "Perkiraan pemakaian: mungkin / tinggi / terburuk"), `${num(m.q50, 1)} / ${num(m.q90, 1)} / ${num(m.q95, 1)}`],
              [t("Next 6 months: routine + turnaround", "6 bulan ke depan: rutin + turnaround"), `${num(m.base_qty, 1)} + ${num(m.event_qty, 1)}`],
              [t("Use while waiting for delivery", "Pemakaian selama menunggu kiriman"), `${num(m.ltd_mean, 1)} ± ${num(Math.sqrt(m.ltd_var), 1)}`],
              [t("Delivery: usual / slow case", "Waktu kirim: biasa / lambat"), t(`${num(m.lt_p50)} / ${num(m.lt_p90)} days`, `${num(m.lt_p50)} / ${num(m.lt_p90)} hari`)],
              [t("Unit price", "Harga satuan"), m.unit_price ? `${rp(m.unit_price)} (${m.price_source === "po" ? t("from purchase orders", "dari pesanan pembelian") : t("estimate", "taksiran")})` : t("n/a", "t/a")],
              [t("Main supplier", "Pemasok utama"), m.main_supplier ?? t("n/a", "t/a")],
              [t("Last used", "Terakhir dipakai"), m.last_issue ? shortDate(m.last_issue, true) : t("never", "belum pernah")],
            ].map(([k, v]) => (
              <div key={k}>
                <dt className="text-ink-3">{k}</dt>
                <dd className="m-0 mt-0.5 font-medium tabular-nums text-ink">{v}</dd>
              </div>
            ))}
          </dl>
          <p className="m-0 mt-4 rounded-[10px] bg-ink/[0.035] px-3 py-2.5 text-[13px] leading-relaxed text-ink-2">{plainReason(m.reason)}</p>
          {m.action === "REORDER" && task && (task.kind === "order" || task.kind === "expedite") && Math.ceil(m.order_qty) !== task.qty && (
            <p className="m-0 mt-2 text-[12.5px] leading-snug text-ink-3">
              {t(
                `This reason covers normal use only: ${amount(m.order_qty, m.unit)} refills stock to the new Max. The task at the top is ${amount(task.qty, task.unit)} because it is set against ${task.ta_gap > 0 ? "the turnaround need" : "what is still needed"}.`,
                `Alasan ini hanya mencakup pemakaian normal: ${amount(m.order_qty, m.unit)} mengisi stok sampai Max baru. Tugas di atas berjumlah ${amount(task.qty, task.unit)} karena diukur terhadap ${task.ta_gap > 0 ? "kebutuhan turnaround" : "kebutuhan yang masih tersisa"}.`,
              )}
            </p>
          )}
        </div>
      </details>
    </div>
  );
}

function Check({ ok, yes, no }: { ok: boolean; yes: string; no: string }) {
  return (
    <li className={cn("flex items-center gap-2.5", ok ? "text-ink-2" : "text-plan-ink")}>
      {ok ? <BadgeCheck className="h-4 w-4 shrink-0 text-ready" aria-hidden /> : <CircleDashed className="h-4 w-4 shrink-0 text-plan" aria-hidden />}
      {ok ? yes : no}
    </li>
  );
}

function QtyRange({ q50, q95, stock }: { q50: number; q95: number; stock: number }) {
  const top = Math.max(q95, stock, 1) * 1.15;
  const x = (v: number) => `${(v / top) * 100}%`;
  return (
    <div className="relative mt-3 h-10" aria-hidden>
      <div className="absolute inset-x-0 top-3 h-2 rounded-full bg-ink/[0.06]" />
      <div className="absolute top-3 h-2 rounded-full bg-ink/20" style={{ left: 0, width: x(q95) }} />
      <div className="absolute top-3 h-2 rounded-full bg-ink-2" style={{ left: 0, width: x(q50) }} />
      <div className="absolute top-0 h-6 w-[3px] -translate-x-1/2 rounded-full bg-ready" style={{ left: x(stock) }} />
      <span className="absolute top-[26px] whitespace-nowrap text-[11px] font-medium text-ready-ink" style={{ left: `clamp(0px, calc(${x(stock)} - 24px), calc(100% - 52px))` }}>
        {t("on shelf", "di rak")}
      </span>
    </div>
  );
}


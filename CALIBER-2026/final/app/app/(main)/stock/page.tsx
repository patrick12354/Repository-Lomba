import { Suspense } from "react";
import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { Coins, Hourglass } from "@/components/icons";
import { agingAhead, health, stockLibrary } from "@/lib/data";
import { DecideSteps } from "@/components/decide-steps";
import { Hint } from "@/components/hint";
import { ACTION_STATUS, ACTION_VERB, cn, num, partName, pct, amount, rp, shortDate } from "@/lib/format";
import { Chip, CritTile, Em, PageHead, Panel, PanelHead, STATUS_TONE } from "@/components/ui";
import { StockLibrary, StockTabs, SupplyFlow } from "@/components/stock-library";
import { AiBrief } from "@/components/ai-brief";
import { t } from "@/lib/i18n";
import { getLang, titled } from "@/lib/i18n-server";

export const generateMetadata = titled("Stock", "Stok");

const healthRows = () => [
  { key: "STOCKOUT", label: t("Empty, still used", "Kosong, masih dipakai"), status: "act" as const },
  { key: "BELOW_MIN", label: t("Below Min", "Di bawah Min"), status: "plan" as const },
  { key: "OK", label: t("Healthy", "Sehat"), status: "ready" as const },
  { key: "OVER_MAX", label: t("Above Max", "Di atas Max"), status: "excess" as const },
  { key: "NON_MOVING", label: t("Unused 17 months", "Tak terpakai 17 bulan"), status: "idle" as const },
  { key: "OBSOLETE_CANDIDATE", label: t("Possibly obsolete", "Mungkin usang"), status: "idle" as const },
];

const healthHint = (): Record<string, string> => ({
  STOCKOUT: t("Nothing on the shelf, but the plant used it in the last 17 months.", "Rak kosong, padahal kilang memakainya dalam 17 bulan terakhir."),
  BELOW_MIN: t("Stock is under the low line in SAP, so an order should already be out.", "Stok di bawah batas bawah SAP, jadi seharusnya pesanan sudah dikirim."),
  OK: t("Stock sits between Min and Max.", "Stok berada di antara Min dan Max."),
  OVER_MAX: t("More than the upper limit in SAP. The extra is money on the shelf.", "Melebihi batas atas di SAP. Kelebihannya adalah uang yang mengendap di rak."),
  NON_MOVING: t("In stock, but not used at all in the 17 months of data.", "Ada stoknya, tetapi sama sekali tidak terpakai selama 17 bulan data."),
  OBSOLETE_CANDIDATE: t("Not used in 17 months, and none of its equipment has maintenance or breakdowns planned. Check if it is still needed.", "Tidak terpakai selama 17 bulan, dan tidak ada peralatannya yang dijadwalkan pemeliharaan atau tercatat rusak. Periksa apakah masih diperlukan."),
});

const agingRows = () => [
  { key: "lt3", label: t("Under 3", "Kurang dari 3") },
  { key: "3to6", label: "3–6" },
  { key: "6to12", label: "6–12" },
  { key: "gt12", label: t("Over 12", "Lebih dari 12") },
  { key: "never", label: t("No use", "Tak terpakai") },
];

export default async function Page() {
  await getLang();
  const HEALTH = healthRows();
  const HEALTH_HINT = healthHint();
  const AGING = agingRows();
  const h = health();
  const lib = stockLibrary();
  const ahead = agingAhead();
  const by = Object.fromEntries(h.byHealth.map((b) => [b.health, b]));
  const totalN = h.byHealth.reduce((a, b) => a + b.n, 0);
  const totalV = h.byHealth.reduce((a, b) => a + (b.value ?? 0), 0);
  const q = (critical: number, state: string) => h.quadrant.find((x) => x.critical === critical && x.state === state) ?? { n: 0, value: 0 };
  const agingMax = Math.max(1, ...h.aging.map((a) => a.n));
  const top = h.topOver.slice(0, 5);
  const topMax = Math.max(1, ...top.map((t) => t.over_value));
  const bucket = (...keys: string[]) => h.aging.filter((a) => keys.includes(a.bucket)).reduce((acc, a) => ({ n: acc.n + a.n, value: acc.value + (a.value ?? 0) }), { n: 0, value: 0 });
  const slow = bucket("6to12");
  const dead = bucket("gt12", "never");

  const bar = (label: string, value: (key: string) => number, total: number, title: (key: string, v: number) => string) => (
    <div className="grid grid-cols-[92px_minmax(0,1fr)] items-center gap-3">
      <span className="text-[12px] font-medium text-ink-3">{label}</span>
      <div className="flex h-5 overflow-hidden rounded-[6px]" role="img" aria-label={t(`Stock items by condition, ${label.toLowerCase()}`, `Jumlah stok menurut kondisi, ${label.toLowerCase()}`)}>
        {HEALTH.map((s) => {
          const v = value(s.key);
          return v > 0 ? <div key={s.key} className={cn("h-full border-r-2 border-panel last:border-r-0", STATUS_TONE[s.status].solid, s.key === "OBSOLETE_CANDIDATE" && "opacity-60")} style={{ width: `${(v / total) * 100}%` }} title={title(s.key, v)} /> : null;
        })}
      </div>
    </div>
  );
  const labelOf = (key: string) => HEALTH.find((s) => s.key === key)?.label ?? key;

  return (
    <div className="space-y-4">
      <DecideSteps current="stock" />
      <PageHead
        title={t("Where is money stuck, and where are we exposed?", "Di mana uang tertahan, dan di mana kita rawan?")}
        actions={<AiBrief page="stock" />}
        answer={t(
          <>
            <Em tone="excess">{rp(h.totals.over_value)}</Em> sits above Max, yet <Em tone="act">{num(h.critZero)}</Em> critical stocked parts are empty and {num(h.critBelowMin)} more are below Min.{" "}
            <Hint>Max and Min are the stock limits in SAP. Critical means criticality A or B. Empty parts were all used in the last 17 months. Non Stock parts are left out, because they are bought per job and are normally empty. Rupiah counts only the {num(h.priced.n)} of {num(h.priced.all)} parts with a PO price.{h.pctSpendAboveMax != null && <> {pct(h.pctSpendAboveMax, 0)} of the {rp(h.spendTotal)} spent on purchase orders went to parts that are over their limit today.</>}</Hint>
          </>,
          <>
            Sebanyak <Em tone="excess">{rp(h.totals.over_value)}</Em> berada di atas Max, tetapi <Em tone="act">{num(h.critZero)}</Em> suku cadang kritis yang distok justru kosong dan {num(h.critBelowMin)} lainnya di bawah Min.{" "}
            <Hint>Max dan Min adalah batas stok di SAP. Kritis berarti kekritisan A atau B. Semua suku cadang yang kosong terpakai dalam 17 bulan terakhir. Suku cadang Non Stock tidak dihitung karena dibeli per pekerjaan dan memang biasanya kosong. Nilai rupiah hanya menghitung {num(h.priced.n)} dari {num(h.priced.all)} suku cadang yang memiliki harga PO.{h.pctSpendAboveMax != null && <> Sebesar {pct(h.pctSpendAboveMax, 0)} dari {rp(h.spendTotal)} belanja pesanan pembelian dipakai untuk suku cadang yang hari ini melebihi batasnya.</>}</Hint>
          </>,
        )}
      />

      <div data-tour="s-flow"><SupplyFlow flow={lib.flow} suppliers={lib.suppliers} /></div>

      <Suspense>
        <StockTabs
          overview={
            <div className="space-y-4">
              <Panel tour="s-health">
                <PanelHead title={<span className="flex items-center gap-1">{t("Stock health", "Kesehatan stok")}<Hint>{t(`The ${num(totalN)} parts kept in stock, worth ${rp(totalV)} at known prices. Top bar counts parts, bottom bar counts money. Parts not used in 17 months are ${pct((by.NON_MOVING?.n ?? 0) / totalN)} of the parts but hold ${pct((by.NON_MOVING?.value ?? 0) / totalV)} of the money.`, `${num(totalN)} suku cadang yang distok, senilai ${rp(totalV)} menurut harga yang diketahui. Batang atas menghitung jumlah suku cadang, batang bawah menghitung nilai uang. Suku cadang yang tidak terpakai selama 17 bulan hanya ${pct((by.NON_MOVING?.n ?? 0) / totalN)} dari jumlah suku cadang, tetapi menahan ${pct((by.NON_MOVING?.value ?? 0) / totalV)} dari nilai uangnya.`)}</Hint></span>} icon={Coins} className="pt-4" aside={<span className="text-[12px] text-ink-3">{t(`Unused: ${pct((by.NON_MOVING?.n ?? 0) / totalN)} of parts, ${pct((by.NON_MOVING?.value ?? 0) / totalV)} of money`, `Tak terpakai: ${pct((by.NON_MOVING?.n ?? 0) / totalN)} dari jumlah, ${pct((by.NON_MOVING?.value ?? 0) / totalV)} dari nilai`)}</span>} />
                <div className="space-y-1.5 px-5 pb-4 pt-3">
                  {bar(t("Parts", "Jumlah"), (k) => by[k]?.n ?? 0, totalN, (k, v) => `${labelOf(k)}: ${num(v)}`)}
                  {bar(t("Money", "Nilai"), (k) => by[k]?.value ?? 0, totalV, (k, v) => `${labelOf(k)}: ${rp(v)}`)}
                  <ul className="m-0 grid list-none grid-cols-6 gap-x-4 p-0 pt-2.5">
                    {HEALTH.map((s) => (
                      <li key={s.key} className="flex min-w-0 flex-col">
                        <div className="flex items-start gap-1.5 text-[12px] leading-snug text-ink-3">
                          <span className={cn("mt-[3px] h-2.5 w-2.5 shrink-0 rounded-[3px]", STATUS_TONE[s.status].solid, s.key === "OBSOLETE_CANDIDATE" && "opacity-60")} />
                          <span>{s.label}</span>{HEALTH_HINT[s.key] && <Hint>{HEALTH_HINT[s.key]}</Hint>}
                        </div>
                        <div className="mt-auto pt-1 text-[18px] font-semibold leading-none tabular-nums">{num(by[s.key]?.n ?? 0)} <span className="text-[12px] font-normal text-ink-3">{t("parts", "item")}</span></div>
                        <div className="mt-0.5 text-[12px] tabular-nums text-ink-3">{by[s.key]?.value ? rp(by[s.key].value) : rp(0)}</div>
                      </li>
                    ))}
                  </ul>
                </div>
              </Panel>

              <div className="grid grid-cols-[minmax(0,1fr)_minmax(0,1.15fr)_minmax(0,0.9fr)] gap-4">
                <Panel tour="s-quad" className="flex flex-col">
                  <PanelHead title={<span className="flex items-center gap-1">{t("What to deal with first", "Apa yang ditangani lebih dulu")}<Hint>{t("Parts split by how much they matter (A and B are critical) and whether we hold too little or too much. Press a box to see its tasks.", "Suku cadang dikelompokkan menurut tingkat kepentingannya (A dan B kritis) dan apakah stoknya terlalu sedikit atau terlalu banyak. Tekan salah satu kotak untuk melihat tugasnya.")}</Hint></span>} className="pt-4" />
                  <div className="grid flex-1 grid-cols-[auto_1fr_1fr] grid-rows-[auto_1fr_1fr] gap-1.5 px-4 pb-4 pt-2">
                    <span />
                    <span className="text-center text-[12px] font-medium text-ink-3">{t("Too little stock", "Stok terlalu sedikit")}</span>
                    <span className="text-center text-[12px] font-medium text-ink-3">{t("Too much stock", "Stok terlalu banyak")}</span>
                    <span className="rotate-180 self-center justify-self-center text-[12px] font-medium text-ink-3 [writing-mode:vertical-rl]">{t("Critical (A, B)", "Kritis (A, B)")}</span>
                    <Quad title={t("Fix now", "Segera atasi")} n={q(1, "short").n} value={q(1, "short").value} status="act" href="/todo?crit=A,B&kind=expedite,order" />
                    <Quad title={t("Check before cutting", "Periksa sebelum dikurangi")} n={q(1, "excess").n} value={q(1, "excess").value} status="excess" href="/todo?crit=A,B&kind=reduce" />
                    <span className="rotate-180 self-center justify-self-center text-[12px] font-medium text-ink-3 [writing-mode:vertical-rl]">{t("Less critical (C, S)", "Kurang kritis (C, S)")}</span>
                    <Quad title={t("Order when convenient", "Pesan saat sempat")} n={q(0, "short").n} value={q(0, "short").value} status="plan" href="/todo?crit=C,S&kind=order" />
                    <Quad title={t("Free up the cash", "Bebaskan dananya")} n={q(0, "excess").n} value={q(0, "excess").value} status="idle" href="/todo?crit=C,S&kind=reduce,dispose" />
                  </div>
                </Panel>

                <Panel>
                  <PanelHead title={<span className="flex items-center gap-1">{t("Where the most extra money sits", "Di mana kelebihan dana terbesar")}<Hint>{t("Value of the stock above each part's Max, with what we suggest for it.", "Nilai stok di atas Max tiap suku cadang, beserta saran tindakannya.")}</Hint></span>} className="pt-4" />
                  <ul className="m-0 list-none space-y-2.5 px-5 pb-4 pt-3">
                    {top.map((x) => (
                      <li key={x.material_no}>
                        <div className="flex items-center gap-2 text-[13px]">
                          <CritTile crit={x.criticality} />
                          <Link href={`/parts/${x.material_no}`} className="min-w-0 flex-1 truncate hover:underline">{partName(x.description)}</Link>
                          <span className="shrink-0 font-semibold tabular-nums">{rp(x.over_value)}</span>
                        </div>
                        <div className="mt-1 flex items-center gap-2 pl-[30px]">
                          <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-ink/[0.06]">
                            <div className="h-full rounded-full bg-excess/80" style={{ width: `${(x.over_value / topMax) * 100}%` }} />
                          </div>
                          <Chip status={ACTION_STATUS[x.action]} label={ACTION_VERB[x.action]} />
                        </div>
                      </li>
                    ))}
                  </ul>
                </Panel>

                <Panel className="flex flex-col">
                  <PanelHead title={<span className="flex items-center gap-1">{t("Months since last used", "Bulan sejak terakhir dipakai")}<Hint>{t("Parts on the shelf, by months since they were last used. \"No use\" means none in the 17 months of data. No use for 6 months is slow stock, 12 months is dead stock.", "Suku cadang di rak, dikelompokkan menurut berapa bulan sejak terakhir dipakai. \"Tak terpakai\" berarti tidak ada pemakaian selama 17 bulan data. Tidak terpakai 6 bulan disebut stok lambat, 12 bulan disebut stok mati.")}</Hint></span>} icon={Hourglass} className="pt-4" />
                  <div className="grid flex-1 grid-cols-5 items-end gap-2 px-5 pb-4 pt-3">
                    {AGING.map((a) => {
                      const n = h.aging.find((x) => x.bucket === a.key)?.n ?? 0;
                      return (
                        <div key={a.key} className="flex h-full flex-col items-center justify-end gap-1">
                          <div className="flex h-[128px] w-full flex-col items-center justify-end gap-1">
                            <span className="text-[13px] font-semibold tabular-nums">{num(n)}</span>
                            <div className={cn("w-full rounded-t-[5px]", a.key === "never" || a.key === "gt12" ? "bg-idle" : "bg-ink-2/70")} style={{ height: `${Math.max(3, (n / agingMax) * 100) * 0.8}%` }} />
                          </div>
                          <span className="whitespace-nowrap text-[11px] text-ink-3">{a.label}</span>
                        </div>
                      );
                    })}
                  </div>
                </Panel>
              </div>
            </div>
          }
          library={<StockLibrary shelves={lib.shelves} />}
          slow={
            <div className="grid grid-cols-3 gap-4">
              <StaleList title={t("Becoming slow", "Mulai lambat")} sub={t(`${num(slow.n)} parts · ${rp(slow.value)}`, `${num(slow.n)} suku cadang · ${rp(slow.value)}`)} hint={t(`Last used 6 to 12 months ago. ${num(ahead.soon.slow)} more join in the next 3 months if nothing uses them. Value counts parts with a known price.`, `Terakhir dipakai 6 sampai 12 bulan lalu. ${num(ahead.soon.slow)} lagi akan menyusul dalam 3 bulan ke depan jika tidak ada yang memakainya. Nilai hanya menghitung suku cadang yang harganya diketahui.`)} rows={h.slowing} href="/todo?kind=reduce" cta={t("See them on the To do board", "Lihat di papan Tugas")} />
              <StaleList title={t("Dead stock", "Stok mati")} sub={t(`${num(dead.n)} parts · ${rp(dead.value)}`, `${num(dead.n)} suku cadang · ${rp(dead.value)}`)} hint={t(`No use in over a year. ${num(ahead.soon.dead)} more join in the next 3 months if nothing uses them. Value counts parts with a known price.`, `Tidak terpakai lebih dari setahun. ${num(ahead.soon.dead)} lagi akan menyusul dalam 3 bulan ke depan jika tidak ada yang memakainya. Nilai hanya menghitung suku cadang yang harganya diketahui.`)} rows={h.dead} href="/todo?kind=dispose" cta={t("Review them on the To do board", "Tinjau di papan Tugas")} />
              <StaleList title={t("Will age before it is used", "Akan menua sebelum terpakai")} sub={t(`${num(ahead.outlast.n)} parts · ${rp(ahead.outlast.value)}`, `${num(ahead.outlast.n)} suku cadang · ${rp(ahead.outlast.value)}`)} hint={t("At normal use, the stock lasts longer than the typical shelf life of its part type, so part of it may age before it is used. Value counts parts with a known price. Shelf life is a published guide, see Data check.", "Dengan pemakaian normal, stoknya bertahan lebih lama daripada umur simpan umum jenis suku cadang tersebut, sehingga sebagian bisa menua sebelum terpakai. Nilai hanya menghitung suku cadang yang harganya diketahui. Umur simpan mengacu pada panduan yang dipublikasikan, lihat Cek data.")} rows={ahead.outlast.rows} href="/check" cta={t("See the shelf life guide", "Lihat panduan umur simpan")} />
            </div>
          }
        />
      </Suspense>
    </div>
  );
}

function StaleList({ title, sub, hint, rows, href, cta }: { title: string; sub: string; hint: string; rows: ReturnType<typeof health>["dead"]; href: string; cta: string }) {
  return (
    <Panel className="flex flex-col">
      <div className="px-5 pt-4">
        <h2 className="m-0 flex items-center gap-1 text-[14px] font-semibold">{title}<Hint>{hint}</Hint></h2>
        <p className="m-0 mt-0.5 text-[12.5px] text-ink-3">{sub}</p>
      </div>
      <ul className="m-0 mt-2 list-none divide-y divide-line p-0">
        {rows.map((r) => (
          <li key={r.material_no}>
            <Link href={`/parts/${r.material_no}`} className="flex items-center gap-2.5 px-5 py-2 transition-colors hover:bg-ink/[0.02]">
              <CritTile crit={r.criticality} />
              <span className="min-w-0 flex-1">
                <span className="block truncate text-[13px] font-medium">{partName(r.description)}</span>
                <span className="block text-[12px] tabular-nums text-ink-3">{amount(r.stock, r.unit)} · {r.last_issue ? t(`last used ${shortDate(r.last_issue, true)}`, `terakhir dipakai ${shortDate(r.last_issue, true)}`) : t("never used in 17 months", "tidak pernah dipakai dalam 17 bulan")}</span>
              </span>
              <span className="shrink-0 text-[13px] font-semibold tabular-nums">{rp(r.stock_value)}</span>
            </Link>
          </li>
        ))}
      </ul>
      <Link href={href} className="mt-auto flex items-center justify-between gap-3 border-t border-line px-5 py-2.5 text-[13px] text-ink-2 transition-colors hover:bg-ink/[0.02]">
        {cta}
        <ArrowRight aria-hidden className="h-4 w-4 text-ink-3" />
      </Link>
    </Panel>
  );
}

function Quad({ title, n, value, status, href }: { title: string; n: number; value: number | null; status: "act" | "excess" | "plan" | "idle"; href: string }) {
  const tone = STATUS_TONE[status];
  return (
    <Link href={href} className={cn("flex min-h-[92px] flex-col justify-between rounded-[12px] p-3 transition-opacity duration-150 hover:opacity-90", tone.soft)}>
      <span className={cn("text-[13px] font-semibold", tone.ink)}>{title}</span>
      <span>
        <span className={cn("block text-[22px] font-semibold leading-none tabular-nums", tone.ink)}>{num(n)} <span className="text-[12px] font-normal">{t("parts", "item")}</span></span>
        <span className={cn("mt-1 block text-[12px] opacity-80", tone.ink)}>{t(`${value ? rp(value) : rp(0)} on the shelf`, `${value ? rp(value) : rp(0)} di rak`)}</span>
      </span>
    </Link>
  );
}

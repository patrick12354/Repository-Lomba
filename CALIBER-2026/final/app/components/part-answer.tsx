import type { ReactNode } from "react";
import type { PartAnswer as Answer, Task } from "@/lib/data";
import { amount, cn, daysBetween, num, rp, shortDate, type Status } from "@/lib/format";
import { STATUS_TONE } from "./ui";
import { Hint } from "./hint";
import { t } from "@/lib/i18n";

type Mile = { key: string; label: string; date: string; tone: string };

function miles(a: Answer): Mile[] {
  const out: Mile[] = [{ key: "today", label: t("Today", "Hari ini"), date: a.asOf, tone: "bg-ink" }];
  if (a.orderBy) out.push({ key: "order", label: a.orderBy < a.asOf ? t("Last safe order day passed", "Batas aman pemesanan sudah lewat") : a.orderBy === a.asOf ? t("Order today", "Pesan hari ini") : t("Last safe order day", "Batas aman pemesanan"), date: a.orderBy, tone: "bg-plan" });
  if (a.arrives) out.push({ key: "arrive", label: a.orderBy && a.orderBy <= a.asOf ? t("Arrives if ordered today", "Tiba jika dipesan hari ini") : t("Arrives if ordered then", "Tiba jika dipesan pada batas itu"), date: a.arrives, tone: "bg-watch" });
  if (a.ta) out.push({ key: "ta", label: t("Turnaround starts", "Turnaround dimulai"), date: a.ta.date, tone: "bg-act" });
  if (a.aging.slowOn && a.aging.slowOn > a.asOf) out.push({ key: "slow", label: t("Slow stock if unused", "Menjadi stok lambat jika tak terpakai"), date: a.aging.slowOn, tone: "bg-idle" });
  if (a.aging.deadOn && a.aging.deadOn > a.asOf) out.push({ key: "dead", label: t("Dead stock if unused", "Menjadi stok mati jika tak terpakai"), date: a.aging.deadOn, tone: "bg-idle" });
  return out.sort((x, y) => x.date.localeCompare(y.date));
}

function agingLine(a: Answer): string {
  const g = a.aging;
  const used = g.lastUsed ? t(`Last used ${shortDate(g.lastUsed, true)}.`, `Terakhir dipakai ${shortDate(g.lastUsed, true)}.`) : t("No use in the 17 months of data.", "Tidak ada pemakaian dalam 17 bulan data.");
  const cover = a.have <= 0 ? t("Nothing on the shelf to age.", "Tidak ada stok di rak yang bisa menua.") : g.coverMonths != null ? t(`At normal use, ${amount(a.have, a.unit)} lasts about ${num(Math.round(g.coverMonths))} months.`, `Dengan pemakaian normal, ${amount(a.have, a.unit)} cukup untuk sekitar ${num(Math.round(g.coverMonths))} bulan.`) : t("It has no regular use, so the stock would sit on the shelf.", "Tidak ada pemakaian rutin, jadi stoknya akan mengendap di rak.");
  const shelf = !g.shelf || a.have <= 0 ? "" : g.outlasts ? t(` That is past its typical shelf life of ${g.shelf.range}, so part of it may age before it is used.`, ` Itu melewati umur simpan umumnya, yaitu ${g.shelf.range}, sehingga sebagian bisa menua sebelum terpakai.`) : t(` Its typical shelf life is ${g.shelf.range}.`, ` Umur simpan umumnya ${g.shelf.range}.`);
  return `${used} ${cover}${shelf}`;
}

function inMonths(from: string, to: string): string {
  const d = daysBetween(from, to);
  return d < 60 ? t(`in ${d} days`, `${d} hari lagi`) : t(`in ${Math.round(d / 30.4)} months`, `${Math.round(d / 30.4)} bulan lagi`);
}

function Big({ label, value, tone, hint }: { label: ReactNode; value: string; tone?: string; hint?: ReactNode }) {
  return (
    <div className="min-w-0">
      <div className="flex items-center gap-1 text-[12.5px] text-ink-3">{label}{hint && <Hint>{hint}</Hint>}</div>
      <div className={cn("mt-0.5 text-[26px] font-semibold leading-tight tracking-[-0.015em] tabular-nums", tone)}>{value}</div>
    </div>
  );
}

const Op = ({ children }: { children: ReactNode }) => <span aria-hidden className="self-end pb-1.5 text-[18px] text-ink-4">{children}</span>;

/** The one answer for a part: have against need, the gap, and what to do. Timeline and aging fold away. */
export function PartAnswer({ a, task, compact, action, status }: { a: Answer; task: Task | null; compact?: boolean; action?: ReactNode; status?: ReactNode }) {
  const verdict = headline(a, task);
  const tone = STATUS_TONE[verdict.status];
  // Against the turnaround when the part is in it, else against normal use until the forecast ends.
  const need = a.ta ? a.ta.total : a.likely6;
  const gap = Math.max(0, need - a.have);
  const by = a.ta ? shortDate(a.ta.date, true) : shortDate(a.forecastEnds, true);
  const top = Math.max(need, a.have, 1);
  const routineW = a.ta ? (a.ta.routine / top) * 100 : (a.likely6 / top) * 100;
  const jobW = a.ta ? (a.ta.need / top) * 100 : 0;
  const haveX = Math.min(100, (a.have / top) * 100);

  return (
    <section aria-label={t("What we have and what we need", "Yang kita miliki dan yang kita butuhkan")} className={compact ? "" : "rounded-[20px] border border-line bg-panel p-5 shadow-card"}>
      <div className={cn("grid items-start gap-x-3 gap-y-3", compact ? "grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)]" : "grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)_auto_minmax(0,1fr)]")}>
        <Big label={t("We have", "Stok kita")} value={amount(a.have, a.unit)} hint={t(`Stock on the shelf on ${shortDate(a.asOf, true)}, the last day of the data.`, `Stok di rak pada ${shortDate(a.asOf, true)}, hari terakhir data.`)} />
        <Op>vs</Op>
        <Big
          label={t(`We need by ${by}`, `Kebutuhan s.d. ${by}`)}
          value={amount(need, a.unit)}
          hint={
            a.ta
              ? t(
                  `Normal use from today until the turnaround (${amount(a.ta.routine, a.unit)}, most likely estimate) plus what the turnaround job used last time (${amount(a.ta.need, a.unit)}).`,
                  `Pemakaian normal dari hari ini sampai turnaround (${amount(a.ta.routine, a.unit)}, taksiran paling mungkin) ditambah pemakaian pekerjaan turnaround sebelumnya (${amount(a.ta.need, a.unit)}).`,
                )
              : t(
                  `Most likely use until ${shortDate(a.forecastEnds, true)}. Bad case ${amount(a.bad6, a.unit)}. The last turnaround did not use this part.`,
                  `Pemakaian paling mungkin sampai ${shortDate(a.forecastEnds, true)}. Skenario terburuk ${amount(a.bad6, a.unit)}. Turnaround sebelumnya tidak memakai suku cadang ini.`,
                )
          }
        />
        {!compact && <Op>=</Op>}
        <div className={compact ? "col-span-3" : undefined}>
          <Big label={gap > 0 ? t("Short by", "Kurang") : t("Enough", "Cukup")} value={gap > 0 ? amount(gap, a.unit) : t(`${amount(a.have - need, a.unit)} spare`, `sisa ${amount(a.have - need, a.unit)}`)} tone={gap > 0 ? "text-act-ink" : "text-ready-ink"} />
        </div>
      </div>

      <div className="relative mt-4">
        <div className="flex h-3.5 overflow-hidden rounded-full bg-ink/[0.06]" role="img" aria-label={t(`Need ${amount(need, a.unit)}, have ${amount(a.have, a.unit)}`, `Butuh ${amount(need, a.unit)}, punya ${amount(a.have, a.unit)}`)}>
          <div className="h-full bg-ink-3/60" style={{ width: `${routineW}%` }} />
          {jobW > 0 && <div className="h-full bg-plan" style={{ width: `${jobW}%` }} />}
        </div>
        <div className="absolute -top-1 h-[22px] w-[3px] -translate-x-1/2 rounded-full bg-ink ring-2 ring-panel" style={{ left: `${haveX}%` }} title={t("What we have", "Stok kita")} />
      </div>
      <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-[12px] text-ink-3">
        <span className="inline-flex items-center gap-1.5"><i className="h-2.5 w-2.5 rounded-[3px] bg-ink-3/60" />{a.ta ? t("Normal use until then", "Pemakaian normal sampai saat itu") : t(`Normal use until ${shortDate(a.forecastEnds)}`, `Pemakaian normal sampai ${shortDate(a.forecastEnds)}`)} {amount(a.ta ? a.ta.routine : a.likely6, a.unit)}</span>
        {a.ta && <span className="inline-flex items-center gap-1.5"><i className="h-2.5 w-2.5 rounded-[3px] bg-plan" />{t("Turnaround job", "Pekerjaan turnaround")} {amount(a.ta.need, a.unit)}</span>}
        <span className="inline-flex items-center gap-1.5"><i className="h-3 w-[3px] rounded-full bg-ink" />{t("We have", "Stok kita")}</span>
      </div>

      <div className={cn("mt-4 flex flex-wrap items-center justify-between gap-x-4 gap-y-2 rounded-[12px] px-3.5 py-2.5", tone.soft)}>
        <div className="min-w-0">
          <div className={cn("text-[15px] font-semibold leading-snug", tone.ink)}>{verdict.text}</div>
          {verdict.sub && <div className={cn("mt-0.5 text-[12.5px] leading-snug opacity-80", tone.ink)}>{verdict.sub}</div>}
        </div>
        {action}
      </div>
      {status && <div className="mt-2">{status}</div>}

      <details className="group mt-3 border-t border-line pt-2.5">
        <summary className="flex cursor-pointer list-none items-center justify-between gap-3 text-[12.5px] font-medium text-ink-2 hover:text-ink">
          {t("Dates and aging", "Tanggal dan penuaan stok")}
          <span className="font-normal text-ink-3 group-open:hidden">{a.orderBy ? `${a.orderBy < a.asOf ? t("Order day passed", "Batas pemesanan sudah lewat") : a.orderBy === a.asOf ? t("Order today", "Pesan hari ini") : t(`Order by ${shortDate(a.orderBy, true)}`, `Pesan paling lambat ${shortDate(a.orderBy, true)}`)} · ` : ""}{a.aging.deadOn && a.aging.deadOn > a.asOf ? t(`dead stock ${shortDate(a.aging.deadOn, true)} if unused`, `menjadi stok mati ${shortDate(a.aging.deadOn, true)} jika tak terpakai`) : t("no aging risk", "tidak ada risiko penuaan")}</span>
        </summary>
        <ol className={cn("m-0 mt-3 grid list-none gap-1 p-0", compact && "grid-cols-2 gap-y-3")} style={compact ? undefined : { gridTemplateColumns: `repeat(${miles(a).length}, minmax(0, 1fr))` }}>
          {miles(a).map((m, i, all) => (
            <li key={m.key} className="relative min-w-0 text-[12px] leading-snug">
              {!compact && i < all.length - 1 && <span aria-hidden className="absolute -right-1 left-3 top-[5px] h-0.5 bg-line-2" />}
              <span aria-hidden className={cn("relative block h-3 w-3 rounded-full ring-2 ring-panel", m.tone)} />
              <span className="mt-1.5 block font-medium text-ink">{m.label}</span>
              <span className="block tabular-nums text-ink-3">{shortDate(m.date, true)}{m.key !== "today" && m.date > a.asOf ? ` · ${inMonths(a.asOf, m.date)}` : ""}</span>
            </li>
          ))}
        </ol>
        <p className="m-0 mt-3 text-[12.5px] leading-[1.5] text-ink-2">
          {agingLine(a)} {t(`Next 6 months: most likely ${amount(a.likely6, a.unit)}, bad case ${amount(a.bad6, a.unit)}.`, `6 bulan ke depan: paling mungkin ${amount(a.likely6, a.unit)}, skenario terburuk ${amount(a.bad6, a.unit)}.`)}
          {a.aging.shelf && a.have > 0 && <> <Hint>{t(`Shelf life is a published guide (${a.aging.shelf.source}), not from this plant. ${a.aging.shelf.note}. Check the product's datasheet.`, `Umur simpan mengacu pada panduan yang dipublikasikan (${a.aging.shelf.source}), bukan dari kilang ini. ${a.aging.shelf.note}. Periksa lembar data produknya.`)}</Hint></>}
        </p>
      </details>
    </section>
  );
}

function headline(a: Answer, task: Task | null): { text: string; sub?: string; status: Status } {
  const cost = task?.value != null ? rp(task.value) : null;
  const money = (extra: string) => [cost, extra].filter(Boolean).join(" · ");
  if (!task) return { text: t("Nothing to do. Stock fits the expected use.", "Tidak perlu tindakan. Stok sesuai dengan perkiraan pemakaian."), status: "ready" };
  const lead = num(Math.round(a.lead));
  if (task.kind === "expedite") {
    const after = a.arrives && a.ta && a.arrives > a.ta.date;
    return {
      text: t(`Rush ${amount(task.qty, task.unit)} now`, `Percepat pesanan ${amount(task.qty, task.unit)} sekarang`),
      sub: money(t(`Normal delivery takes up to ${lead} days${after ? " and arrives after the turnaround starts" : ", too close to the turnaround"}`, `Pengiriman biasa memakan waktu hingga ${lead} hari${after ? " dan baru tiba setelah turnaround dimulai" : ", terlalu mepet dengan turnaround"}`)),
      status: "act",
    };
  }
  if (task.kind === "order") {
    const now = !task.order_by || task.order_by <= a.asOf;
    // The turnaround plan shows its own later date, so say why this order cannot wait for it.
    const earlier = now && a.taOrderBy && a.taOrderBy > a.asOf ? a.taOrderBy : null;
    return {
      text: t(`Order ${amount(task.qty, task.unit)} ${now ? "now" : `by ${shortDate(task.order_by, true)}`}`, `Pesan ${amount(task.qty, task.unit)} ${now ? "sekarang" : `paling lambat ${shortDate(task.order_by, true)}`}`),
      sub: money(
        earlier
          ? t(`Delivery up to ${lead} days. Stock is already below the reorder point for normal use, so it cannot wait for the turnaround's last safe day, ${shortDate(earlier, true)}`, `Pengiriman hingga ${lead} hari. Stok sudah di bawah reorder point untuk pemakaian normal, jadi tidak bisa menunggu batas aman turnaround, ${shortDate(earlier, true)}`)
          : t(`Delivery up to ${lead} days`, `Pengiriman hingga ${lead} hari`),
      ),
      status: "plan",
    };
  }
  if (task.kind === "twin" && task.twin) return { text: t(`Move ${amount(task.qty, task.unit)} from duplicate part ${task.twin.donor}`, `Pindahkan ${amount(task.qty, task.unit)} dari suku cadang kembar ${task.twin.donor}`), sub: t("It holds extra stock, so no purchase is needed. Confirm they are interchangeable first", "Suku cadang itu memiliki kelebihan stok, jadi tidak perlu membeli. Pastikan dulu keduanya bisa saling menggantikan"), status: "twin" };
  if (task.kind === "reduce") return { text: t("Stop buying", "Hentikan pembelian"), sub: money(t(`${amount(task.qty, task.unit)} is more than the new Max`, `${amount(task.qty, task.unit)} melebihi Max baru`)), status: "excess" };
  if (task.kind === "dispose") return { text: t("Check if it is still needed", "Periksa apakah masih diperlukan"), sub: money(t("No use in 17 months and no work planned on its equipment", "Tidak terpakai selama 17 bulan dan tidak ada pekerjaan terencana pada peralatannya")), status: "idle" };
  return { text: t("Keep an eye on it. No order yet", "Pantau dulu. Belum perlu memesan"), sub: task.unusual ? t(`Recent use was ${num(task.unusual.ratio, 1)} times its usual month`, `Pemakaian terakhir ${num(task.unusual.ratio, 1)} kali lipat dari bulan biasanya`) : undefined, status: "watch" };
}

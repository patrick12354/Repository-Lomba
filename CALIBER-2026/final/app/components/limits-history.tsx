"use client";

import { useMemo, useRef, useState, type PointerEvent } from "react";
import type { ReplayPart } from "@/lib/data";
import { cn, monthLabel, num, pct, unitName } from "@/lib/format";
import { Hint } from "./hint";
import { t } from "@/lib/i18n";

const DAY0 = Date.UTC(2026, 2, 1);
const W = 520;
const H = 250;
const PAD = { left: 44, right: 8, top: 10, bottom: 24 };
const INK = { band: "#1e8a5a", stock: "#2f6fb5", failed: "#d8402a", served: "#8a8a90", order: "#16171a" };

const dateOf = (d: number) => new Date(DAY0 + d * 86_400_000);
const monthOf = (d: number) => dateOf(d).toISOString().slice(0, 7);
const qtyText = (v: number) => (Math.abs(v) >= 100 || Number.isInteger(v) ? num(v) : num(v, 1));
const dayText = (d: number) => dateOf(d).toLocaleDateString(t("en-GB", "id-ID"), { day: "numeric", month: "short", timeZone: "UTC" });

/** A round axis top, so both charts of a part share one readable scale. */
function niceTop(v: number) {
  const base = 10 ** Math.floor(Math.log10(Math.max(v, 1)));
  const top = [1, 1.5, 2, 3, 4, 5, 6, 8, 10].map((m) => m * base).find((x) => x >= v);
  return top ?? 10 * base;
}

/** Stock, Min and Max for one part over the replay, under today's limits and under ours, plus what each monthly update saw. */
export function LimitsHistory({ part }: { part: ReplayPart }) {
  const [hover, setHover] = useState<number | null>(null);
  const days = part.use.length;
  const months = useMemo(() => Array.from(new Set(part.use.map((_, d) => monthOf(d)))), [part.use]);
  const top = niceTop(Math.max(...part.maxs, part.max_today, ...part.today, ...part.sparekit, 1));
  const unit = unitName(part.unit);
  const shortToday = part.short_today.reduce((a, s) => a + s[1], 0);
  const shortOurs = part.short_sparekit.reduce((a, s) => a + s[1], 0);

  // The largest move in Min across the monthly updates, so the page can say what changed at that update.
  const moves = part.mins.slice(1).map((v, i) => ({ i: i + 1, delta: v - part.mins[i] }));
  const biggest = moves.reduce((b, m) => (Math.abs(m.delta) > Math.abs(b.delta) ? m : b), { i: 0, delta: 0 });
  const b = biggest.i;

  return (
    <div>
      <p className="m-0 text-[13px] leading-[1.5] text-ink-2">
        {t(
          <>Asked for {qtyText(part.requested)} {unit} over seven months. Today&apos;s limits left <b className={cn("font-semibold", shortToday > 0 && "text-act-ink")}>{qtyText(shortToday)}</b> unserved, ours left <b className={cn("font-semibold", shortOurs > 0 ? "text-act-ink" : "text-ready-ink")}>{qtyText(shortOurs)}</b>.</>,
          <>Diminta {qtyText(part.requested)} {unit} selama tujuh bulan. Batas saat ini menyisakan <b className={cn("font-semibold", shortToday > 0 && "text-act-ink")}>{qtyText(shortToday)}</b> tidak terlayani, batas kami menyisakan <b className={cn("font-semibold", shortOurs > 0 ? "text-act-ink" : "text-ready-ink")}>{qtyText(shortOurs)}</b>.</>,
        )}
      </p>

      <div className="mt-3 grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Band
          title={t("Today's limits in SAP", "Batas saat ini di SAP")}
          note={part.max_today > 0 ? t(`Fixed at ${qtyText(part.min_today)} to ${qtyText(part.max_today)}`, `Tetap ${qtyText(part.min_today)} sampai ${qtyText(part.max_today)}`) : t("No limits set, so nothing is reordered", "Tanpa batas, jadi tidak ada pemesanan ulang")}
          mins={months.map(() => part.min_today)}
          maxs={months.map(() => part.max_today)}
          stock={part.today}
          use={part.use}
          short={part.short_today}
          orders={part.orders_today}
          top={top}
          days={days}
          hover={hover}
          setHover={setHover}
          unit={unit}
        />
        <Band
          title={t("Sparekit limits, updated monthly", "Batas Sparekit, diperbarui bulanan")}
          note={t(`Min moved between ${qtyText(Math.min(...part.mins))} and ${qtyText(Math.max(...part.mins))}`, `Min bergerak antara ${qtyText(Math.min(...part.mins))} dan ${qtyText(Math.max(...part.mins))}`)}
          mins={part.mins}
          maxs={part.maxs}
          stock={part.sparekit}
          use={part.use}
          short={part.short_sparekit}
          orders={part.orders_sparekit}
          top={top}
          days={days}
          hover={hover}
          setHover={setHover}
          unit={unit}
        />
      </div>

      <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-[12px] text-ink-3">
        <span className="inline-flex items-center gap-1.5"><i className="h-2.5 w-3.5 rounded-[2px]" style={{ background: INK.band, opacity: 0.25 }} />{t("Between Min and Max", "Antara Min dan Max")}</span>
        <span className="inline-flex items-center gap-1.5"><i className="h-0.5 w-3.5" style={{ background: INK.stock }} />{t("Stock on the shelf", "Stok di rak")}</span>
        <span className="inline-flex items-center gap-1.5"><i className="h-2 w-2 rounded-full" style={{ background: INK.served }} />{t("Request served", "Permintaan terlayani")}</span>
        <span className="inline-flex items-center gap-1.5"><i className="h-2 w-2 rounded-full" style={{ background: INK.failed }} />{t("Request not fully served", "Permintaan tidak terlayani penuh")}</span>
        <span className="inline-flex items-center gap-1.5"><svg aria-hidden width="10" height="9" viewBox="0 0 10 9"><path d="M5 0 10 9H0Z" fill={INK.order} /></svg>{t("Order placed", "Pesanan dibuat")}</span>
      </div>

      <div className="mt-4 overflow-x-auto">
        <table className="w-full min-w-[640px] border-collapse text-[12.5px] tabular-nums">
          <thead>
            <tr className="border-b border-line text-[12px] text-ink-3">
              <th className="py-1.5 pr-3 text-left font-medium">{t("Update on the 1st", "Pembaruan tanggal 1")}</th>
              {months.map((m) => <th key={m} className="px-1 py-1.5 text-right font-medium">{monthLabel(m)}</th>)}
            </tr>
          </thead>
          <tbody>
            <tr className="border-b border-line text-ink-3">
              <td className="py-1.5 pr-3">{t("Min to Max in SAP", "Min sampai Max di SAP")}</td>
              {months.map((m) => <td key={m} className="px-1 py-1.5 text-right">{qtyText(part.min_today)}–{qtyText(part.max_today)}</td>)}
            </tr>
            <tr className="border-b border-line font-medium">
              <td className="py-1.5 pr-3">{t("Min to Max, Sparekit", "Min sampai Max, Sparekit")}</td>
              {months.map((m, i) => {
                const d = i ? part.mins[i] - part.mins[i - 1] : 0;
                return (
                  <td key={m} className={cn("px-1 py-1.5 text-right", d > 0 && "text-plan-ink", d < 0 && "text-ready-ink")}>
                    {qtyText(part.mins[i])}–{qtyText(part.maxs[i])}{d > 0 ? " ▲" : d < 0 ? " ▼" : ""}
                  </td>
                );
              })}
            </tr>
            <tr className="border-b border-line text-ink-2">
              <td className="py-1.5 pr-3">{t("Chance of use, next 6 months", "Peluang terpakai, 6 bulan ke depan")}</td>
              {months.map((m, i) => <td key={m} className="px-1 py-1.5 text-right">{pct(part.chance[i], 0)}</td>)}
            </tr>
            <tr className="border-b border-line text-ink-2">
              <td className="py-1.5 pr-3">{t(`Use while waiting for delivery, ${unit}`, `Pemakaian selama menunggu kiriman, ${unit}`)}</td>
              {months.map((m, i) => <td key={m} className="px-1 py-1.5 text-right">{qtyText(part.use_in_delivery[i])}</td>)}
            </tr>
            <tr className="text-ink-2">
              <td className="py-1.5 pr-3">{t("Usual delivery time, days", "Waktu kirim biasa, hari")}</td>
              {months.map((m, i) => <td key={m} className="px-1 py-1.5 text-right">{qtyText(part.delivery[i])}</td>)}
            </tr>
          </tbody>
        </table>
      </div>

      <p className="m-0 mt-2 flex items-start gap-1 text-[12.5px] leading-[1.5] text-ink-2">
        <span>
          {b > 0 && biggest.delta !== 0
            ? t(
                `Biggest change: on 1 ${monthLabel(months[b])} Min went ${biggest.delta > 0 ? "up" : "down"} from ${qtyText(part.mins[b - 1])} to ${qtyText(part.mins[b])}. `,
                `Perubahan terbesar: pada 1 ${monthLabel(months[b])} Min ${biggest.delta > 0 ? "naik" : "turun"} dari ${qtyText(part.mins[b - 1])} menjadi ${qtyText(part.mins[b])}. `,
              ) + changedInputs(part, b)
            : t("Min stayed the same across the updates.", "Min tetap sama pada setiap pembaruan.")}
        </span>
        <Hint>{t("Min covers use while waiting for delivery plus a cushion for the part's target. Max adds one order size, up to a year of expected use. Stock can sit below Min while an order is on its way.", "Min menutup pemakaian selama menunggu kiriman ditambah cadangan sesuai target suku cadang. Max menambahkan satu ukuran pesanan, paling banyak setara satu tahun perkiraan pemakaian. Stok bisa berada di bawah Min saat pesanan sedang dalam perjalanan.")}</Hint>
      </p>
    </div>
  );
}

/** Only the inputs that visibly moved at update `b`, so the sentence never says "from 100% to 100%". */
function changedInputs(part: ReplayPart, b: number) {
  const pair = (from: string, to: string) => (from === to ? null : t(`from ${from} to ${to}`, `dari ${from} menjadi ${to}`));
  const chance = pair(pct(part.chance[b - 1], 0), pct(part.chance[b], 0));
  const use = pair(qtyText(part.use_in_delivery[b - 1]), qtyText(part.use_in_delivery[b]));
  const days = pair(qtyText(part.delivery[b - 1]), qtyText(part.delivery[b]));
  const items = [
    chance && t(`the chance of use went ${chance}`, `peluang terpakai berubah ${chance}`),
    use && t(`use while waiting for delivery went ${use}`, `pemakaian selama menunggu kiriman berubah ${use}`),
    days && t(`delivery time went ${days} days`, `waktu kirim berubah ${days} hari`),
  ].filter(Boolean);
  if (!items.length) return t("The figures above stayed about the same, so the move came from the spread of past requests.", "Angka di atas kurang lebih tetap, jadi perubahannya berasal dari sebaran permintaan sebelumnya.");
  return t(`At that update, ${items.join(", and ")}.`, `Pada pembaruan itu, ${items.join(", dan ")}.`);
}

function Band({ title, note, mins, maxs, stock, use, short, orders, top, days, hover, setHover, unit }: {
  title: string;
  note: string;
  mins: number[];
  maxs: number[];
  stock: number[];
  use: number[];
  short: number[][];
  orders: number[][];
  top: number;
  days: number;
  hover: number | null;
  setHover: (d: number | null) => void;
  unit: string;
}) {
  const ref = useRef<SVGSVGElement>(null);
  const x = (d: number) => PAD.left + (d / days) * (W - PAD.left - PAD.right);
  const y = (v: number) => H - PAD.bottom - (v / top) * (H - PAD.top - PAD.bottom);
  const firsts = use.map((_, d) => d).filter((d) => d === 0 || monthOf(d) !== monthOf(d - 1));
  const ends = [...firsts.slice(1), days];
  const failed = new Map(short.map((s) => [s[0], s[1]]));

  let path = "";
  stock.forEach((v, d) => {
    path += d === 0 ? `M${x(0).toFixed(1)} ${y(v).toFixed(1)}` : `H${x(d).toFixed(1)}V${y(v).toFixed(1)}`;
  });
  path += `H${x(days).toFixed(1)}`;

  const move = (e: PointerEvent<SVGSVGElement>) => {
    const box = ref.current?.getBoundingClientRect();
    if (!box) return;
    const px = ((e.clientX - box.left) / box.width) * W;
    const d = Math.round(((px - PAD.left) / (W - PAD.left - PAD.right)) * days);
    setHover(d >= 0 && d < days ? d : null);
  };
  const monthIndex = hover == null ? 0 : firsts.filter((f) => f <= hover).length - 1;

  return (
    <figure className="relative m-0 min-w-0 rounded-[14px] border border-line p-3">
      <figcaption className="flex items-baseline justify-between gap-3">
        <span className="text-[13px] font-semibold">{title}</span>
        <span className="truncate text-[12px] text-ink-3">{note}</span>
      </figcaption>
      <svg ref={ref} viewBox={`0 0 ${W} ${H}`} className="mt-1 block h-auto w-full touch-none" role="img" aria-label={`${title}. ${note}`} onPointerMove={move} onPointerLeave={() => setHover(null)}>
        {[0, 0.5, 1].map((f) => (
          <g key={f}>
            <line x1={PAD.left} x2={W - PAD.right} y1={y(top * f)} y2={y(top * f)} stroke="rgb(30 26 20 / 0.08)" />
            <text x={PAD.left - 6} y={y(top * f) + 4} fontSize={11} textAnchor="end" fill="#6f6f73">{qtyText(top * f)}</text>
          </g>
        ))}
        {firsts.map((f, i) => (
          <g key={f}>
            {maxs[i] > 0 && <rect x={x(f)} y={y(maxs[i])} width={x(ends[i]) - x(f)} height={Math.max(1, y(mins[i]) - y(maxs[i]))} fill={INK.band} fillOpacity={0.2} />}
            {i > 0 && <line x1={x(f)} x2={x(f)} y1={PAD.top} y2={H - PAD.bottom} stroke="rgb(30 26 20 / 0.06)" />}
            <text x={(x(f) + x(ends[i])) / 2} y={H - 7} fontSize={11} textAnchor="middle" fill="#6f6f73">{monthLabel(monthOf(f)).split(" ")[0]}</text>
          </g>
        ))}
        <path d={path} fill="none" stroke={INK.stock} strokeWidth={2} strokeLinejoin="round" />
        {orders.map(([d]) => <path key={d} d={`M${x(d)} ${y(stock[d]) - 12}l5 9h-10z`} fill={INK.order} />)}
        {use.map((u, d) => (u > 0 ? <circle key={d} cx={x(d)} cy={y(0)} r={failed.has(d) ? 5 : 3.5} fill={failed.has(d) ? INK.failed : INK.served} stroke="#fff" strokeWidth={1.5} /> : null))}
        {hover != null && <line x1={x(hover)} x2={x(hover)} y1={PAD.top} y2={H - PAD.bottom} stroke="#16171a" strokeOpacity={0.35} />}
      </svg>
      {hover != null && (
        <div className="pointer-events-none absolute z-10 rounded-[10px] bg-ink px-3 py-2 text-[12px] leading-snug text-white" style={{ left: `${Math.min(62, Math.max(8, (x(hover) / W) * 100))}%`, top: 34 }}>
          <div className="font-medium">{dayText(hover)}</div>
          <div className="text-white/75">{t("On the shelf", "Di rak")}: {qtyText(stock[hover])} {unit}</div>
          <div className="text-white/75">{t("Min to Max", "Min sampai Max")}: {qtyText(mins[monthIndex])}–{qtyText(maxs[monthIndex])}</div>
          {use[hover] > 0 && <div className="text-white/75">{t("Asked for", "Diminta")}: {qtyText(use[hover])}{failed.has(hover) && <>, {t(`${qtyText(failed.get(hover)!)} not served`, `${qtyText(failed.get(hover)!)} tidak terlayani`)}</>}</div>}
        </div>
      )}
    </figure>
  );
}

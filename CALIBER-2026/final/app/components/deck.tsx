"use client";

import { t } from "@/lib/i18n";
import type { ReactNode } from "react";
import Link from "next/link";
import { ArrowUpRight } from "lucide-react";
import { type LucideIcon } from "@/components/icons";
import { type Crit, CRITS, cn } from "@/lib/format";
import { CritTile } from "./ui";
import { Hint } from "./hint";

/** Metric card: icon, label, one number. The whole card is the link when there is somewhere to go. */
export function MetricCard({ icon: Icon, label, sub, value, unit, href, glow, className }: { icon: LucideIcon; label: string; sub: string; value: ReactNode; unit?: string; href?: string; glow?: boolean; className?: string }) {
  const body = (
    <>
      <span className={cn("grid h-12 w-12 shrink-0 place-items-center rounded-[14px]", glow ? "bg-white text-ink" : "bg-panel-2 text-ink-2")}>
        <Icon aria-hidden className="h-7 w-7" strokeWidth={1.9} />
      </span>
      <div className="min-w-0 flex-1">
        <div className="text-[28px] font-semibold leading-none tracking-[-0.02em] tabular-nums">
          {value}
          {unit && <span className={cn("ml-1 text-[14px] font-normal tracking-normal", glow ? "text-white/70" : "text-ink-3")}>{unit}</span>}
        </div>
        <div className="mt-1.5 flex items-center gap-1 text-[13px] font-medium leading-tight">
          <span className="min-w-0">{label}</span>
          <span onClick={(e) => { e.preventDefault(); e.stopPropagation(); }} className={cn("shrink-0", glow && "[&_button]:text-white/70 [&_button:hover]:bg-white/15 [&_button:hover]:text-white")}>
            <Hint>{sub}</Hint>
          </span>
        </div>
      </div>
      {href && <ArrowUpRight aria-hidden className={cn("absolute right-3 top-3 h-4 w-4 transition-transform duration-200 group-hover:-translate-y-0.5 group-hover:translate-x-0.5", glow ? "text-white/70" : "text-ink-4")} />}
    </>
  );
  const cls = cn("group relative flex min-h-[92px] items-center gap-3.5 rounded-[18px] px-4 py-3.5 transition-colors duration-150", glow ? "glow-card" : "border border-line bg-panel shadow-card", href && !glow && "hover:border-line-2", className);
  return href ? <Link href={href} className={cls}>{body}</Link> : <div className={cls}>{body}</div>;
}

/** Tick gauge from the machine hall: 48 ticks, the filled share in machine orange. */
export function TickGauge({ value, caption }: { value: number; caption: string }) {
  const n = 48;
  const R = 104;
  const cx = 130;
  const cy = 122;
  return (
    <div className="relative">
      <svg viewBox="0 0 260 132" className="block h-auto w-full" role="img" aria-label={t(`${value} percent ready`, `${value} persen siap`)}>
        {Array.from({ length: n }, (_, i) => {
          const t = i / (n - 1);
          const a = Math.PI * (1 - t);
          return (
            <line
              key={i}
              x1={(cx + Math.cos(a) * (R - 24)).toFixed(1)}
              y1={(cy - Math.sin(a) * (R - 24)).toFixed(1)}
              x2={(cx + Math.cos(a) * R).toFixed(1)}
              y2={(cy - Math.sin(a) * R).toFixed(1)}
              strokeWidth={5}
              strokeLinecap="round"
              className={t * 100 <= value ? "stroke-accent" : "stroke-ink/10"}
            />
          );
        })}
      </svg>
      <div className="absolute inset-x-0 bottom-[6%] text-center">
        <div className="text-[36px] font-semibold leading-none tracking-[-0.02em] tabular-nums">{value}%</div>
        <div className="mt-1 text-[12px] text-ink-3">{caption}</div>
      </div>
    </div>
  );
}

/** Thin dial with one needle, for the control deck. */
export function NeedleGauge({ value }: { value: number }) {
  const R = 92;
  const cx = 110;
  const cy = 102;
  const a = Math.PI * (1 - value / 100);
  const pt = (an: number, r: number) => [+(cx + Math.cos(an) * r).toFixed(1), +(cy - Math.sin(an) * r).toFixed(1)];
  const [ax, ay] = pt(Math.PI, R);
  const [bx, by] = pt(a, R);
  const [ex, ey] = pt(0, R);
  const [nx, ny] = pt(a, R + 11);
  const [ix, iy] = pt(Math.PI, R - 16);
  const [jx, jy] = pt(a, R - 16);
  return (
    <svg viewBox="0 0 220 112" className="block h-auto w-full" role="img" aria-label={t(`Needle at ${value} percent`, `Jarum di ${value} persen`)}>
      <path d={`M${ix} ${iy} A${R - 16} ${R - 16} 0 0 1 ${jx} ${jy} L${cx} ${cy} Z`} fill="rgb(255 255 255 / .55)" />
      <path d={`M${ax} ${ay} A${R} ${R} 0 0 1 ${ex} ${ey}`} stroke="rgb(0 0 0 / .16)" strokeWidth={1.5} fill="none" />
      <path d={`M${bx} ${by} A${R} ${R} 0 0 1 ${ex} ${ey}`} stroke="#16171a" strokeWidth={4} fill="none" strokeLinecap="round" />
      <line x1={cx} y1={cy} x2={nx} y2={ny} stroke="#16171a" strokeWidth={1.4} />
      <circle cx={cx} cy={cy} r={3.5} fill="#16171a" />
      <circle cx={nx} cy={ny} r={2.5} fill="#16171a" />
    </svg>
  );
}

export function CritRows({ byCrit }: { byCrit: { crit: Crit; ready: number; total: number }[] }) {
  return (
    <ul className="m-0 list-none p-0">
      {CRITS.map((c) => {
        const b = byCrit.find((x) => x.crit === c);
        if (!b || !b.total) return null;
        return (
          <li key={c} className="flex items-center justify-between gap-3 border-t border-line py-2 text-[13px] text-ink-2">
            <span className="flex items-center gap-2">
              <CritTile crit={c} />
              {t(`${b.ready} of ${b.total} ready`, `${b.ready} dari ${b.total} siap`)}
            </span>
            <b className="font-semibold tabular-nums text-ink">{Math.round((b.ready / b.total) * 100)}%</b>
          </li>
        );
      })}
    </ul>
  );
}


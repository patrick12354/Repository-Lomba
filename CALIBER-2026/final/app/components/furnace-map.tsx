"use client";

import { cn } from "@/lib/format";

type Furnace = { equipment: string; total: number; short: number };

const C = Math.cos(Math.PI / 6);
const S = 0.5;
const UNIT = 30;

// world (x across, y along the bank, z up) → screen
const iso = (x: number, y: number, z: number) => [(x - y) * C * UNIT, (x + y) * S * UNIT - z * UNIT] as const;
const poly = (pts: (readonly [number, number])[]) => pts.map((p) => `${p[0].toFixed(1)},${p[1].toFixed(1)}`).join(" ");

const READY = { top: "#cdeedb", front: "#9fd9b6", side: "#7cc59c" };
const SHORT = { top: "#fbd0cb", front: "#f08f85", side: "#dc675c" };
const EMPTY = { top: "#e6eaed", front: "#d3d9de", side: "#bfc7ce" };

function Box({ x0, x1, y0, y1, z0, z1, c }: { x0: number; x1: number; y0: number; y1: number; z0: number; z1: number; c: typeof READY }) {
  if (z1 - z0 < 0.001) return null;
  return (
    <g>
      <polygon points={poly([iso(x1, y0, z0), iso(x1, y1, z0), iso(x1, y1, z1), iso(x1, y0, z1)])} fill={c.side} />
      <polygon points={poly([iso(x0, y1, z0), iso(x1, y1, z0), iso(x1, y1, z1), iso(x0, y1, z1)])} fill={c.front} />
      <polygon points={poly([iso(x0, y0, z1), iso(x1, y0, z1), iso(x1, y1, z1), iso(x0, y1, z1)])} fill={c.top} />
    </g>
  );
}

/**
 * Twelve cracking furnaces as an isometric bank, receding to the right.
 * Height = turnaround parts installed there; the red cap is the share that is short.
 */
export function FurnaceMap({ furnaces, selected, onSelect }: { furnaces: Furnace[]; selected: string | null; onSelect: (e: string | null) => void }) {
  const max = Math.max(1, ...furnaces.map((f) => f.total));
  const H = 3.4;
  const D = 1.5; // depth (x)
  const W = 0.86; // width (y)
  const P = 1.22; // pitch along the bank
  const n = furnaces.length;

  // bounds
  const pts = [iso(0, 0.6, 0), iso(D, 0.6, 0), iso(0, -(n - 1) * P - W, H + 0.9), iso(D, -(n - 1) * P - W, 0), iso(0, 0.6, H)];
  const minX = Math.min(...pts.map((p) => p[0])) - 10;
  const maxX = Math.max(...pts.map((p) => p[0])) + 16;
  const minY = Math.min(...pts.map((p) => p[1])) - 18;
  const maxY = Math.max(...pts.map((p) => p[1])) + 26;

  const order = furnaces.map((f, i) => ({ f, i })).reverse(); // far first
  return (
    <svg viewBox={`${minX} ${minY} ${maxX - minX} ${maxY - minY}`} className="h-auto w-full" role="img" aria-label="Turnaround parts per furnace, red share is short">
      {/* ground slab */}
      <polygon
        points={poly([iso(-0.3, 0.5, 0), iso(D + 0.3, 0.5, 0), iso(D + 0.3, -(n - 1) * P - W - 0.3, 0), iso(-0.3, -(n - 1) * P - W - 0.3, 0)])}
        className="fill-ink/[0.04]"
      />
      {order.map(({ f, i }) => {
        const y1 = -i * P;
        const y0 = y1 - W;
        const h = f.total > 0 ? 0.5 + (f.total / max) * (H - 0.5) : 0.35;
        const hs = f.total > 0 ? (h * f.short) / f.total : 0;
        const active = selected === f.equipment;
        const dim = selected && !active;
        const label = iso(D + 0.15, y1 + 0.05, 0);
        const cap = iso(D * 0.5, y0 + W / 2, h);
        return (
          <g
            key={f.equipment}
            role="button"
            tabIndex={0}
            aria-pressed={active}
            aria-label={`${f.equipment}: ${f.short} of ${f.total} turnaround parts short`}
            onClick={() => onSelect(active ? null : f.equipment)}
            onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && (e.preventDefault(), onSelect(active ? null : f.equipment))}
            className={cn("cursor-pointer outline-none transition-opacity duration-200", dim && "opacity-35")}
          >
            <title>{`${f.equipment}: ${f.short} of ${f.total} parts short`}</title>
            {f.total === 0 ? (
              <Box x0={0} x1={D} y0={y0} y1={y1} z0={0} z1={h} c={EMPTY} />
            ) : (
              <>
                <Box x0={0} x1={D} y0={y0} y1={y1} z0={0} z1={h - hs} c={READY} />
                <Box x0={0} x1={D} y0={y0} y1={y1} z0={h - hs} z1={h} c={SHORT} />
              </>
            )}
            {active && (
              <polygon
                points={poly([iso(0, y0, h), iso(D, y0, h), iso(D, y1, h), iso(0, y1, h)])}
                fill="none"
                stroke="#0f1e2d"
                strokeWidth={1.5}
              />
            )}
            {f.short > 0 && (
              <text x={cap[0]} y={cap[1] - 8} textAnchor="middle" className="fill-act-ink font-display text-[12px] font-semibold">
                {f.short}
              </text>
            )}
            <text x={label[0] + 3} y={label[1] + 14} className="fill-ink-3 text-[10.5px]" textAnchor="start">
              {f.equipment.replace("BF-", "")}
            </text>
          </g>
        );
      })}
    </svg>
  );
}

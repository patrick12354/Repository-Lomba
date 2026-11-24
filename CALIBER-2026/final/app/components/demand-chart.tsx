"use client";

import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis, CartesianGrid } from "recharts";
import { monthLabel, num, unitName } from "@/lib/format";
import { t } from "@/lib/i18n";

type Row = { month: string; routine: number; ta: number };

/** Monthly issues, routine vs turnaround, stacked. */
export function DemandChart({ rows, unit }: { rows: Row[]; unit: string }) {
  return (
    <div className="h-[200px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={rows} margin={{ top: 8, right: 4, bottom: 0, left: -18 }} barCategoryGap="22%">
          <CartesianGrid vertical={false} stroke="rgb(15 30 45 / 0.07)" />
          <XAxis dataKey="month" tickFormatter={monthLabel} tick={{ fontSize: 11, fill: "#5f6c78" }} tickLine={false} axisLine={false} interval="preserveStartEnd" minTickGap={18} />
          <YAxis tick={{ fontSize: 11, fill: "#5f6c78" }} tickLine={false} axisLine={false} allowDecimals={false} width={44} />
          <Tooltip
            cursor={{ fill: "rgb(15 30 45 / 0.04)" }}
            content={({ active, payload, label }) =>
              active && payload?.length ? (
                <div className="rounded-[10px] border border-line bg-panel px-3 py-2 text-[12px] shadow-[0_8px_20px_-8px_rgb(15_30_45/0.25)]">
                  <div className="font-medium text-ink">{monthLabel(String(label))}</div>
                  <div className="mt-1 text-ink-2">{t("Routine", "Rutin")}: {num(Number(payload[0]?.value ?? 0), 1)} {unitName(unit)}</div>
                  <div className="text-ink-2">{t("Turnaround", "Turnaround")}: {num(Number(payload[1]?.value ?? 0), 1)} {unitName(unit)}</div>
                </div>
              ) : null
            }
          />
          <Bar dataKey="routine" stackId="a" fill="#3a4855" radius={[0, 0, 0, 0]} isAnimationActive={false} />
          <Bar dataKey="ta" stackId="a" fill="#d98a00" radius={[3, 3, 0, 0]} isAnimationActive={false} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

/** Plant-wide parts used per month, routine vs turnaround work. */
export function PlantChart({ rows }: { rows: { month: string; routine: number; ta: number }[] }) {
  return (
    <div className="h-[240px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={rows} margin={{ top: 8, right: 4, bottom: 0, left: -12 }} barCategoryGap="20%">
          <CartesianGrid vertical={false} stroke="rgb(15 30 45 / 0.07)" />
          <XAxis dataKey="month" tickFormatter={monthLabel} tick={{ fontSize: 11, fill: "#5f6c78" }} tickLine={false} axisLine={false} interval="preserveStartEnd" minTickGap={14} />
          <YAxis tick={{ fontSize: 11, fill: "#5f6c78" }} tickLine={false} axisLine={false} width={44} />
          <Tooltip
            cursor={{ fill: "rgb(15 30 45 / 0.04)" }}
            content={({ active, payload, label }) =>
              active && payload?.length ? (
                <div className="rounded-[10px] border border-line bg-panel px-3 py-2 text-[12px] shadow-[0_8px_20px_-8px_rgb(15_30_45/0.25)]">
                  <div className="font-medium text-ink">{monthLabel(String(label))}</div>
                  <div className="mt-1 text-ink-2">{t(`Routine work: ${num(Number(payload[0]?.value ?? 0))} parts`, `Pekerjaan rutin: ${num(Number(payload[0]?.value ?? 0))} suku cadang`)}</div>
                  <div className="text-ink-2">{t(`Turnaround work: ${num(Number(payload[1]?.value ?? 0))} parts`, `Pekerjaan turnaround: ${num(Number(payload[1]?.value ?? 0))} suku cadang`)}</div>
                </div>
              ) : null
            }
          />
          <Bar dataKey="routine" stackId="a" fill="#3a4855" isAnimationActive={false} />
          <Bar dataKey="ta" stackId="a" fill="#d98a00" radius={[3, 3, 0, 0]} isAnimationActive={false} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

import { type Status, amount, cn, qty } from "@/lib/format";
import { STATUS_TONE } from "./ui";
import { t } from "@/lib/i18n";

/**
 * Stock against the old and new Min–Max on one track.
 * Grey outline = today's range, coloured band = the new range, ink pin = stock on the shelf.
 */
export function RangeGauge({
  stock,
  minCur,
  maxCur,
  minNew,
  maxNew,
  unit,
  status,
  size = "sm",
}: {
  stock: number;
  minCur: number;
  maxCur: number;
  minNew: number;
  maxNew: number;
  unit: string;
  status: Status;
  size?: "sm" | "lg";
}) {
  const top = Math.max(stock, maxCur, maxNew, 1) * 1.12;
  const x = (v: number) => `${Math.min(100, (v / top) * 100)}%`;
  const w = (a: number, b: number) => `${Math.max(1.2, ((Math.max(b, a) - a) / top) * 100)}%`;
  const lg = size === "lg";
  return (
    <div className={cn("w-full", lg ? "pt-7" : "pt-0.5")}>
      <div className={cn("relative rounded-full bg-ink/[0.06]", lg ? "h-4" : "h-2")}>
        <div className="absolute inset-y-[-3px] rounded-full border border-dashed border-ink-3/60" style={{ left: x(minCur), width: w(minCur, maxCur) }} title={t(`Current range ${minCur}–${maxCur}`, `Rentang saat ini ${minCur}–${maxCur}`)} />
        <div className={cn("absolute inset-y-0 rounded-full opacity-80", STATUS_TONE[status].solid)} style={{ left: x(minNew), width: w(minNew, maxNew) }} title={t(`New range ${minNew}–${maxNew}`, `Rentang baru ${minNew}–${maxNew}`)} />
        <div className={cn("absolute top-1/2 -translate-x-1/2 -translate-y-1/2 rounded-full bg-ink ring-2 ring-panel", lg ? "h-7 w-[5px]" : "h-4 w-[3px]")} style={{ left: x(stock) }}>
          {lg && (
            <span className={cn("absolute bottom-full mb-1.5 whitespace-nowrap rounded-[6px] bg-ink px-1.5 py-0.5 text-[11.5px] font-semibold text-white", stock / top < 0.2 ? "left-0" : stock / top > 0.8 ? "right-0" : "left-1/2 -translate-x-1/2")}>
              {t(`${amount(stock, unit)} on the shelf`, `${amount(stock, unit)} di rak`)}
            </span>
          )}
        </div>
      </div>
      {lg && (
        <div className="mt-4 flex flex-wrap gap-x-5 gap-y-1.5 text-[12.5px] text-ink-3">
          <span className="inline-flex items-center gap-1.5">
            <span className="h-2.5 w-5 rounded-full border border-dashed border-ink-3/70" />
            {t(`In SAP today: Min ${qty(minCur, unit)}, Max ${qty(maxCur, unit)}`, `Di SAP saat ini: Min ${qty(minCur, unit)}, Max ${qty(maxCur, unit)}`)}
          </span>
          <span className="inline-flex items-center gap-1.5">
            <span className={cn("h-2.5 w-5 rounded-full opacity-80", STATUS_TONE[status].solid)} />
            {t("We suggest: ", "Kami sarankan: ")}<span className="font-semibold text-ink">Min {qty(minNew, unit)}, Max {qty(maxNew, unit)}</span>
          </span>
        </div>
      )}
    </div>
  );
}

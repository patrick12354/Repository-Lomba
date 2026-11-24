import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { health, scenario, taskCounts } from "@/lib/data";
import { cn, num, rp } from "@/lib/format";
import { t } from "@/lib/i18n";

type Step = "plan" | "stock" | "act";

/** Stock plan, then what it means for the shelf, then the tasks: one path through three pages. */
export function DecideSteps({ current }: { current: Step }) {
  const s = scenario();
  const h = health();
  const tc = taskCounts();
  const fix = h.quadrant.find((q) => q.critical === 1 && q.state === "short")?.n ?? 0;
  const steps: { key: Step; href: string; title: string; now: string }[] = [
    { key: "plan", href: "/what-if", title: t("Choose the stock plan", "Pilih rencana stok"), now: t(`Recommended: hold ${rp(s.optimized.budget_idr)}, not ${rp(s.current.budget_idr)}`, `Disarankan: simpan ${rp(s.optimized.budget_idr)}, bukan ${rp(s.current.budget_idr)}`) },
    { key: "stock", href: "/stock", title: t("See what is short or extra", "Lihat yang kurang atau berlebih"), now: t(`${num(fix)} critical parts too low, ${rp(h.totals.over_value)} above Max`, `${num(fix)} suku cadang kritis terlalu sedikit, ${rp(h.totals.over_value)} di atas Max`) },
    { key: "act", href: "/todo", title: t("Approve and act", "Setujui dan jalankan"), now: t(`${num(tc.urgent)} urgent, ${rp(tc.toBuy)} of suggested buying`, `${num(tc.urgent)} mendesak, usulan pembelian ${rp(tc.toBuy)}`) },
  ];
  return (
    <nav aria-label={t("How to decide", "Cara memutuskan")} className="grid shrink-0 grid-cols-3 gap-2">
      {steps.map((x, i) => {
        const on = x.key === current;
        return (
          <Link key={x.key} href={x.href} aria-current={on ? "step" : undefined} className={cn("flex min-w-0 items-center gap-2.5 rounded-[12px] border px-3 py-2 transition-colors", on ? "border-ink bg-panel" : "border-line bg-panel/60 hover:border-line-2")}>
            <span className={cn("grid h-6 w-6 shrink-0 place-items-center rounded-full text-[12px] font-semibold tabular-nums", on ? "bg-ink text-white" : "bg-ink/[0.07] text-ink-2")}>{i + 1}</span>
            <span className="min-w-0 flex-1">
              <span className={cn("block truncate text-[13px]", on ? "font-semibold" : "font-medium text-ink-2")}>{x.title}</span>
              <span className="block truncate text-[12px] text-ink-3" title={x.now}>{x.now}</span>
            </span>
            {i < 2 && <ArrowRight aria-hidden className="h-3.5 w-3.5 shrink-0 text-ink-4" />}
          </Link>
        );
      })}
    </nav>
  );
}

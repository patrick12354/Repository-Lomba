import type { ReactNode } from "react";
import { Shell } from "@/components/shell";
import { asOf, readiness, taskCounts } from "@/lib/data";
import { machineByPlural } from "@/lib/machines";
import { shortDate } from "@/lib/format";
import { getLang } from "@/lib/i18n-server";

/** Everything behind the login: the sidebar, the footer and the assistant. */
export default async function MainLayout({ children }: { children: ReactNode }) {
  await getLang();
  const r = readiness();
  const machines = r.classes.flatMap((c) => {
    const m = machineByPlural(c.cls);
    return m ? [{ slug: m.slug, name: m.plural, short: c.short }] : [];
  });
  const ab = r.byCrit.filter((c) => c.crit === "A" || c.crit === "B");
  const abPct = Math.round((ab.reduce((n, c) => n + c.ready, 0) / Math.max(1, ab.reduce((n, c) => n + c.total, 0))) * 100);
  return (
    <Shell asOf={shortDate(asOf(), true)} taDays={r.daysToTa} taDate={shortDate(r.taDate, true)} urgent={taskCounts().urgent} machines={machines} abPct={abPct}>
      {children}
    </Shell>
  );
}

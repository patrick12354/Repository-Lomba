import { replayProof, scenario } from "@/lib/data";
import { ScenarioView, type Replay } from "@/components/scenario-view";
import { DecideSteps } from "@/components/decide-steps";
import { getLang, titled } from "@/lib/i18n-server";

export const generateMetadata = titled("What if", "Simulasi");

export default async function Page() {
  await getLang();
  const r = replayProof();
  const replay: Replay = r ? { fillToday: r.today.fill_units, fill: r.sparekit.fill_units, stockToday: r.today.avg_inv_idr, stock: r.sparekit.avg_inv_idr, daysToday: r.today.stockout_days, days: r.sparekit.stockout_days } : null;
  return (
    <div className="space-y-4">
      <DecideSteps current="plan" />
      <ScenarioView initial={scenario()} replay={replay} />
    </div>
  );
}

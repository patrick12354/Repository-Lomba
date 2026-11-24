import { readiness, maxProof, maxFacts, outlook, health } from "@/lib/data";
import { PlantView } from "@/components/plant-view";
import { getLang } from "@/lib/i18n-server";

export default async function Page() {
  await getLang();
  const h = health();
  return <PlantView initial={readiness()} proof={maxProof(4)} facts={maxFacts()} months={outlook().months} overValue={h.totals.over_value} pctAbove={h.pctSpendAboveMax ?? 0} />;
}

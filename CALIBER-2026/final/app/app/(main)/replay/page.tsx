import { notFound } from "next/navigation";
import { replayView } from "@/lib/data";
import { ReplayView } from "@/components/replay-view";
import { getLang, titled } from "@/lib/i18n-server";

export const generateMetadata = titled("Replay", "Simulasi ulang");

export default async function Page() {
  await getLang();
  const data = replayView();
  if (!data) notFound();
  return <ReplayView {...data} />;
}

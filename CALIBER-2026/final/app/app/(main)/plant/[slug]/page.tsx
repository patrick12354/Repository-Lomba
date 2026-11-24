import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { machineView, proof } from "@/lib/data";
import { machineBySlug } from "@/lib/machines";
import { MachineDetail } from "@/components/machine-detail";
import { t } from "@/lib/i18n";
import { getLang } from "@/lib/i18n-server";

type Props = { params: Promise<{ slug: string }>; searchParams: Promise<{ date?: string; scale?: string; unit?: string; shock?: string }> };

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  await getLang();
  const m = machineBySlug((await params).slug);
  return { title: m?.plural ?? t("Machine", "Mesin") };
}

/* Blocking on purpose: a stream boundary here delays hydration, and the 3D stage waits on hydration. */
export const instant = false;

export default async function Page({ params, searchParams }: Props) {
  const { slug } = await params;
  await getLang();
  const sp = await searchParams;
  const machine = machineBySlug(slug);
  if (!machine) notFound();
  const scale = Number(sp.scale ?? 1);
  const unit = sp.unit && sp.unit.startsWith(`${machine.prefix}-`) ? sp.unit : undefined;
  const view = machineView(machine.prefix, sp.date, scale, unit, Number(sp.shock ?? 0));
  return <MachineDetail machine={machine} view={view} unit={unit ?? null} query={{ date: sp.date, scale: sp.scale, shock: sp.shock }} hit={Math.round((proof()?.engine ?? 0) * 100)} />;
}

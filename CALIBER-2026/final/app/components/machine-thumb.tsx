import type { MachineSlug } from "@/lib/machines";

/** Still renders of each model, captured once from the stage so the picker costs no WebGL. */
export function MachineThumb({ slug }: { slug: MachineSlug }) {
  // eslint-disable-next-line @next/next/no-img-element
  return <img src={`/machines/${slug}.png`} alt="" className="h-full w-full object-cover" />;
}

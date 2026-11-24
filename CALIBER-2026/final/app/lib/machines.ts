/** The five equipment families the 3D plant knows. Prefix matches `material_location.equipment`. */
export type MachineSlug = "pump" | "compressor" | "turbine" | "furnace" | "exchanger";

import { bi, t } from "./i18n";

/** `key` is the English class name the data layer uses; name, plural and tagline follow the language. */
export type Machine = { slug: MachineSlug; prefix: string; key: string; name: string; plural: string; tagline: string };

const machine = (slug: MachineSlug, prefix: string, name: [string, string], plural: [string, string], tagline: [string, string]): Machine => ({
  slug,
  prefix,
  key: plural[0],
  get name() {
    return t(name[0], name[1]);
  },
  get plural() {
    return t(plural[0], plural[1]);
  },
  get tagline() {
    return t(tagline[0], tagline[1]);
  },
});

export const MACHINES: Machine[] = [
  machine("furnace", "BF", ["Cracking furnace", "Tungku perengkahan"], ["Furnaces", "Tungku"], ["Twelve radiant boxes BF-101 to BF-112", "Dua belas kotak radiasi, BF-101 sampai BF-112"]),
  machine("compressor", "KC", ["Centrifugal compressor", "Kompresor sentrifugal"], ["Compressors", "Kompresor"], ["Charge gas and refrigeration trains", "Rangkaian gas umpan dan refrigerasi"]),
  machine("pump", "PP", ["Centrifugal pump", "Pompa sentrifugal"], ["Pumps", "Pompa"], ["Process and utility duty", "Layanan proses dan utilitas"]),
  machine("turbine", "KT", ["Steam turbine", "Turbin uap"], ["Turbines", "Turbin"], ["Drivers for the big machines", "Penggerak mesin-mesin besar"]),
  machine("exchanger", "HE", ["Shell and tube exchanger", "Penukar panas shell and tube"], ["Heat exchangers", "Penukar panas"], ["Coolers, condensers, reboilers", "Pendingin, kondensor, reboiler"]),
];

export const machineBySlug = (s: string) => MACHINES.find((m) => m.slug === s);
/** Matches the English class name from the data layer (`Readiness.classes[].cls`). */
export const machineByPlural = (p: string) => MACHINES.find((m) => m.key === p);
/** A class name from the data layer, in the current language. */
export const className = (cls: string) => machineByPlural(cls)?.plural ?? cls;

/** Words for the zones on a model; keys are `materials.category`. */
export const ZONE_LABEL: Record<string, string> = bi({
  BEARING: ["Bearings", "Bantalan"],
  IMPELLER: ["Impeller", "Impeler"],
  "O-RING": ["O-rings and seals", "O-ring dan seal"],
  GASKET: ["Gaskets", "Gasket"],
  STUDBOLT: ["Studbolts", "Baut tanam"],
  OIL: ["Lube oil", "Oli pelumas"],
  GREASE: ["Grease", "Gemuk"],
  TERMINAL: ["Terminals", "Terminal"],
  FLANGE: ["Flanges", "Flensa"],
  COUPLING: ["Coupling", "Kopling"],
  SEAL: ["Labyrinth seal", "Seal labirin"],
  "FILTER ELEMENT": ["Filter elements", "Elemen filter"],
  FIREBRICK: ["Firebrick", "Bata tahan api"],
  "CERAMIC FIBER": ["Ceramic fiber", "Serat keramik"],
  ANCHOR: ["Refractory anchors", "Angkur refraktori"],
  CASTABLE: ["Castable", "Castable"],
  PIPE: ["Pipe", "Pipa"],
  ELBOW: ["Elbows", "Elbow"],
  VALVE: ["Valves", "Katup"],
  SCREW: ["Screws", "Sekrup"],
});

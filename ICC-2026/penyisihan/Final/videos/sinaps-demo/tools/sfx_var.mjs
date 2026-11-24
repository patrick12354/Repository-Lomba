// Varian nada dari SFX dasar (ffmpeg asetrate), supaya urutan bunyi bisa "bernada" dan tidak identik.
// mar1..mar6 = marimba pentatonik (0,2,4,7,9,12 semitone); pop_hi/pop_lo, tock, bubble_hi, glass_hi.
import { execFileSync } from "node:child_process";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
const D = join(dirname(fileURLToPath(import.meta.url)), "..", "assets/audio/sfx");
const shift = (src, n, out) => execFileSync("ffmpeg", ["-y", "-v", "error", "-i", join(D, `${src}.mp3`), "-af", `asetrate=44100*2^(${n}/12),aresample=44100`, "-b:a", "128k", join(D, `${out}.mp3`)]);
[0, 2, 4, 7, 9, 12].forEach((n, i) => shift("marimba", n, `mar${i + 1}`));
shift("pop", 4, "pop_hi"); shift("pop", -4, "pop_lo"); shift("tick", -5, "tock");
shift("bubble", 5, "bubble_hi"); shift("glass_tap", 7, "glass_hi");
console.log("varian sfx ok");

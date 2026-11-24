// Naskah tanpa rekaman: frame STORYBOARD bertanda "- vo: sintetis" mendapat assets/audio/vo/<id>.json berisi
// perkiraan waktu tiap kata saat presenter membacanya (format sama dengan keluaran tools/vo.mjs, tanpa .mp3),
// lalu "- duration:" frame itu diisi = akhir naskah + EKOR. Dengan begitu build.mjs --cut memperlakukannya
// persis seperti frame ber-VO: tiap kalimat = satu beat, animasi mendarat di awal kalimat.
// Jalankan setelah mengubah naskah: node tools/naskah.mjs && node tools/build.mjs --cut
import { readFileSync, writeFileSync, existsSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const EKOR = 1.0;
// tempo presenter: ~2,6 kata/dtk untuk kata pendek; angka dibaca per digit ("29.444" = dua puluh sembilan ribu ...)
const lama = (w) => {
  const core = w.replace(/[^\p{L}\p{N}]/gu, "");
  const dig = (core.match(/\d/g) || []).length;
  const huruf = core.length - dig;
  return 0.1 + huruf * 0.048 + dig * 0.34 + (/×/.test(w) ? 0.3 : 0);
};
const jeda = (w) => (/[.?!]["”']?$/.test(w) ? 0.55 : /[,;:]$/.test(w) ? 0.25 : 0.05);

const path = join(ROOT, "STORYBOARD.md");
let sb = readFileSync(path, "utf8");
const blok = [...sb.matchAll(/^## Frame (\d+)([a-z]?):[^\n]*\n([\s\S]*?)(?=^## |(?![\s\S]))/gm)];
for (const [all, n, sfx, body] of blok) {
  if (!/^- vo: sintetis$/m.test(body)) continue;
  const id = `f${n.padStart(2, "0")}${sfx}`;
  const text = body.match(/^- voiceover: "(.*)"$/m)[1];
  if (existsSync(join(ROOT, "assets/audio/vo", `${id}.mp3`))) throw new Error(`${id}: sudah ada rekaman VO, hapus "- vo: sintetis"`);
  let t = 0;
  const words = text.split(/\s+/).map((w) => {
    const s = t, e = s + lama(w);
    t = e + jeda(w);
    return { w, s: +s.toFixed(2), e: +e.toFixed(2) };
  });
  const end = words.at(-1).e;
  writeFileSync(join(ROOT, "assets/audio/vo", `${id}.json`), JSON.stringify({ text, end, sintetis: true, words }, null, 1));
  const dur = (end + EKOR).toFixed(1);
  sb = sb.replace(all, all.replace(/^- duration: [\d.]+s$/m, `- duration: ${dur}s`));
  console.log(`${id}: ${words.length} kata, naskah ${end.toFixed(1)} dtk -> duration ${dur}s`);
}
writeFileSync(path, sb);

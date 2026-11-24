// Teks film (SRT) dari timestamp kata VO ElevenLabs — waktunya persis sama dengan audio di index.html.
// Angka yang diucapkan ("delapan belas koma lima persen") ditulis sebagai angka ("18,5%") supaya mudah dibaca.
// Hasil: publish/sinaps-demo.id.srt   Jalankan: node tools/captions.mjs (setelah node tools/build.mjs)
import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const frames = JSON.parse(readFileSync(join(ROOT, ".hyperframes-frames.json"), "utf8"));
const MAXC = 42; // karakter per baris teks

const NUM = [
  ["lima puluh delapan tahun", "58 tahun"],
  ["empat setengah jam", "4,5 jam"],
  ["satu koma sembilan juta", "1,9 juta"],
  ["delapan belas koma lima persen", "18,5%"],
  ["tujuh puluh empat persen", "74%"],
  ["nol koma delapan", "0,8"],
  ["seratus ribu", "100.000"],
  ["enam belas kali", "16 kali"],
  ["seribu lima ratus lima", "1.505"],
  ["dua koma lima D", "2,5D"],
  ["sembilan puluh tujuh koma delapan persen", "97,8%"],
  ["empat puluh tujuh persen", "47%"],
  ["empat ratus tiga puluh dua", "432"],
].map(([a, b]) => [a.toLowerCase().split(" "), b]);
const bare = (w) => w.toLowerCase().replace(/[^\p{L}\p{N}]/gu, "");

const words = [];
for (const f of frames) {
  const vo = JSON.parse(readFileSync(join(ROOT, "assets/audio/vo", `${f.id}.json`), "utf8"));
  const t0 = f.start + f.voAt; // sama dengan data-start audio VO di index.html
  const ws = vo.words.map((x) => ({ w: x.w, s: t0 + x.s, e: t0 + x.e }));
  for (let i = 0; i < ws.length; i++) {
    const hit = NUM.find(([seq]) => seq.every((q, k) => ws[i + k] && bare(ws[i + k].w) === bare(q)));
    if (hit) {
      const last = ws[i + hit[0].length - 1];
      const punct = last.w.match(/[^\p{L}\p{N}%]+$/u)?.[0] ?? "";
      words.push({ w: hit[1] + punct, s: ws[i].s, e: last.e, frame: f.id });
      i += hit[0].length - 1;
    } else words.push({ ...ws[i], frame: f.id });
  }
}

// potong jadi cue: maks 2 baris x MAXC, pecah di tanda baca, jeda panjang, atau ganti frame
const cues = [];
let cur = [];
const flush = () => { if (cur.length) cues.push(cur); cur = []; };
words.forEach((wd, i) => {
  const prev = cur.at(-1);
  if (prev && (prev.frame !== wd.frame || wd.s - prev.e > 0.7)) flush();
  const text = [...cur, wd].map((x) => x.w).join(" ");
  if (text.length > MAXC * 2 - 4) flush();
  cur.push(wd);
  const len = cur.map((x) => x.w).join(" ").length;
  if (/[.?!]$/.test(wd.w) || (/[,:]$/.test(wd.w) && len > 30)) flush();
});
flush();

const wrap = (t) => {
  if (t.length <= MAXC) return t;
  const ws = t.split(" ");
  let best = 1, bd = 1e9;
  for (let k = 1; k < ws.length; k++) {
    const a = ws.slice(0, k).join(" "), b = ws.slice(k).join(" ");
    const d = Math.abs(a.length - b.length) + (a.length > MAXC || b.length > MAXC ? 1000 : 0);
    if (d < bd) { bd = d; best = k; }
  }
  return ws.slice(0, best).join(" ") + "\n" + ws.slice(best).join(" ");
};
const ts = (t) => {
  const ms = Math.round(t * 1000), h = Math.floor(ms / 3600000), m = Math.floor(ms / 60000) % 60, s = Math.floor(ms / 1000) % 60;
  return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")},${String(ms % 1000).padStart(3, "0")}`;
};
const out = cues.map((c, i) => {
  const s = c[0].s, next = cues[i + 1]?.[0].s ?? Infinity;
  const e = Math.min(Math.max(c.at(-1).e + 0.25, s + 1.0), next - 0.05);
  return `${i + 1}\n${ts(s)} --> ${ts(e)}\n${wrap(c.map((x) => x.w).join(" "))}\n`;
}).join("\n");
mkdirSync(join(ROOT, "publish"), { recursive: true });
writeFileSync(join(ROOT, "publish", "sinaps-demo.id.srt"), out);
console.log(`${cues.length} cue -> publish/sinaps-demo.id.srt`);

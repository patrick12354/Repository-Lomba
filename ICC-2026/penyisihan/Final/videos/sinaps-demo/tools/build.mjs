// Generator: src/frames/*.tpl -> compositions/frames/*.html, lalu index.html dari src/index.tpl.
// (sumber berekstensi .tpl supaya Studio tidak menyisipkan data-hf-id ke dalamnya)
//
// Direktif di sumber frame:
//   <!-- @base -->                        token warna, @font-face, gaya dasar (di dalam <style>)
//   <!-- @include dika p=f03 smile=0 -->  isi src/parts/dika.svg, {{kunci}} diganti nilai atribut
//   /* @helpers */                        helper JS bersama (src/helpers.js) + data VO frame ini
//   <!-- @sfx pop@1.2 whoosh@0:0.5 punch_hit@~juta+0.1:0.6 -->  efek suara: nama@waktu-lokal[:volume] atau nama@~kata[.n][±detik][:volume] (berjangkar kata VO)
// Isi root frame otomatis dibungkus <div class="scene"><div class="dolly"> (scene = target transisi, dolly = kamera/drift).
// Waktu: frame >1 mulai 0,5 dtk lebih awal (T0 = 0,5) supaya transisi menimpa frame sebelumnya.
// Jalankan: node tools/build.mjs   (edit di src/, jangan di compositions/frames/ atau index.html)
//
// Mode potong untuk presentasi langsung: node tools/build.mjs --cut
//   frame 1..CUT_LAST saja, tanpa audio, ke compositions/cut/ + index.html (versi utama). Mode penuh menulis index-full.html.
//   Tiap kalimat VO jadi satu "beat": semua animasi kalimat itu dipadatkan ke awal kalimat
//   (muncul dulu), lalu layar diam selama kalimat itu dulu diucapkan (presenter bicara).
//   Kalimat dipisah di . ? ! : ; atau di kata yang ditulis di data-split="kata kata" pada root frame.
import { readFileSync, writeFileSync, readdirSync, mkdirSync, existsSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { execFileSync } from "node:child_process";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const SRC = join(ROOT, "src");
const CUT = process.argv.includes("--cut");
const CUT_LAST = 13;
const OUT = join(ROOT, "compositions", CUT ? "cut" : "frames");
mkdirSync(OUT, { recursive: true });
const TR = 0.5; // durasi tumpang-tindih transisi
// beat (mode potong): animasi mulai LEAD dtk sebelum kalimat, dipadatkan K kali (maks CAP dtk);
// tiap beat menambah GAP dtk supaya presenter mulai bicara setelah animasinya mendarat
const LEAD = 0.5, GAP = 0.35, K = 0.25, CAP = 1.3;
const voWords = (id) => {
  const f = join(ROOT, "assets/audio/vo", `${id}.json`);
  return existsSync(f) ? JSON.parse(readFileSync(f, "utf8")).words : [];
};
const clean = (s) => s.replace(/[^\p{L}\p{N}-]/gu, "");
function beats(words, split) {
  let bi = -1, s0 = 0;
  const vow = words.map((x, i) => {
    if (i === 0 || /[.?!:;]["”']?$/.test(words[i - 1].w) || split.has(clean(x.w).toLowerCase())) { bi++; s0 = x.s; }
    const base = s0 + bi * GAP - (bi > 0 ? LEAD : 0);
    return [clean(x.w), +(base + Math.min(CAP, (x.s - s0) * K)).toFixed(3)];
  });
  return { vow, n: bi + 1 };
}

const parseAttrs = (s) =>
  Object.fromEntries([...s.matchAll(/([\w-]+)=("[^"]*"|\S*)/g)].map(([, k, v]) => [k, v.replace(/^"|"$/g, "")]));

function partial(name, attrs) {
  const file = join(SRC, "parts", `${name}.svg`);
  if (!existsSync(file)) throw new Error(`partial tidak ada: ${name}`);
  let txt = readFileSync(file, "utf8");
  const m = txt.match(/^<!-- defaults: (.*?) -->\r?\n?/);
  const vals = { ...(m ? parseAttrs(m[1]) : {}), ...attrs };
  if (m) txt = txt.slice(m[0].length);
  return txt.replace(/\{\{([\w-]+)\}\}/g, (_, k) => {
    if (!(k in vals)) throw new Error(`${name}: nilai {{${k}}} tidak diberikan`);
    return vals[k];
  });
}

// ---- storyboard: urutan, durasi, offset VO ----
const sb = readFileSync(join(ROOT, "STORYBOARD.md"), "utf8");
// nomor frame boleh bersufiks huruf (11a, 11b) untuk scene sisipan; urutan = urutan di STORYBOARD
const frames = [...sb.matchAll(/^## Frame (\d+)([a-z]?):[^\n]*\n([\s\S]*?)(?=^## |(?![\s\S]))/gm)].map(([, n, sfx, body], i) => ({
  n: Number(n),
  z: i + 1,
  id: `f${String(n).padStart(2, "0")}${sfx}`,
  src: body.match(/^- src: (.+)$/m)?.[1].trim(),
  dur: parseFloat(body.match(/^- duration: ([\d.]+)s/m)?.[1] ?? "0"),
  voAt: parseFloat(body.match(/^- vo_at: ([\d.]+)/m)?.[1] ?? "0.5"),
})).filter((f) => !CUT || f.n <= CUT_LAST);
const tplOf = (id) => readdirSync(join(SRC, "frames")).find((x) => x.startsWith(id.slice(1) + "-") && x.endsWith(".tpl"));
const idOf = (file) => `f${file.match(/^(\d+[a-z]?)-/)[1]}`;
for (const f of frames) {
  if (CUT) f.src = f.src?.replace("compositions/frames/", "compositions/cut/");
  const words = voWords(f.id);
  if (!CUT) { f.vow = words.map((x) => [clean(x.w), +x.s.toFixed(3)]); continue; }
  const tpl = tplOf(f.id);
  const sp = tpl ? readFileSync(join(SRC, "frames", tpl), "utf8").match(/data-split="([^"]*)"/)?.[1] ?? "" : "";
  const b = beats(words, new Set(sp.toLowerCase().split(/\s+/).filter(Boolean)));
  f.vow = b.vow;
  f.beats = b.n;
  f.dur = +(f.dur + b.n * GAP).toFixed(2);
}
let t = 0;
for (const f of frames) {
  f.start = t;
  f.T0 = f.z === 1 ? 0 : TR;
  t += f.dur;
}
const TOTAL = t;
const byId = Object.fromEntries(frames.map((f) => [f.id, f]));

const base = readFileSync(join(SRC, "base.css"), "utf8");
const helpers = readFileSync(join(SRC, "helpers.js"), "utf8");

function expand(html, id, depth = 0) {
  if (depth > 4) throw new Error("include terlalu dalam");
  return html
    .replace(/<!-- @base -->/g, base.replaceAll("__ID__", id))
    .replace(/<!-- @include ([\w-]+)(.*?)-->/g, (_, name, rest) => expand(partial(name, parseAttrs(rest)), id, depth + 1));
}

const sfxCues = [];
const files = readdirSync(join(SRC, "frames")).filter((f) => f.endsWith(".tpl") && (!CUT || byId[idOf(f)]));
for (const file of files) {
  const id = idOf(file);
  const f = byId[id];
  let src = readFileSync(join(SRC, "frames", file), "utf8").replace(/\r\n/g, "\n"); // CRLF dari editor Windows mematahkan regex di bawah
  // isi root dibungkus .scene > .dolly
  src = src.replace(/(<div id="f\d+[a-z]?" data-composition-id="f\d+[a-z]?"[^>]*>)([\s\S]*?)(\n<\/div>\s*\n(?:<!-- @sfx[^\n]*-->\n)*<script>)/, (_, open, body, close) =>
    body.includes('class="scene"') ? open + body + close : `${open}\n<div class="scene"><div class="dolly">${body}\n</div></div>${close}`);
  // data VO
  const vow = f?.vow ?? [];
  const h = helpers
    .replace("__ID__", id).replace("__T0__", String(f?.T0 ?? 0)).replace("__DUR__", String(f?.dur ?? 0))
    .replace("__VOAT__", String(f?.voAt ?? 0.5)).replace("__VOW__", JSON.stringify(vow));
  src = src.replace("/* @helpers */", h);
  // isyarat SFX (mode potong: tanpa audio)
  if (!CUT) for (const m of src.matchAll(/<!-- @sfx (.*?)-->/g))
    for (const tok of m[1].trim().split(/\s+/)) {
      let [, name, at, vol] = tok.match(/^([\w-]+)@([\d.]+)(?::([\d.]+))?$/) ?? [];
      if (!name) {
        // nama@~kata[.n][+/-detik][:vol] -> waktu lokal kata ke-n di VO frame ini (pencocokan sama dengan w() di helpers)
        const m2 = tok.match(/^([\w-]+)@~([\p{L}\p{N}-]+?)(?:\.(\d+))?([+-][\d.]+)?(?::([\d.]+))?$/u);
        if (!m2) throw new Error(`${id}: isyarat sfx salah: ${tok}`);
        const re = new RegExp(m2[2], "i");
        let c = 0, hit;
        for (const [ww, ss] of vow) if (re.test(ww) && ++c === Number(m2[3] ?? 1)) { hit = ss; break; }
        if (hit === undefined) throw new Error(`${id}: sfx ${tok}: kata tidak ada di VO`);
        [name, vol] = [m2[1], m2[5]];
        at = (f?.T0 ?? 0) + (f?.voAt ?? 0.5) + hit + Number(m2[4] ?? 0);
      }
      if (!existsSync(join(ROOT, "assets/audio/sfx", `${name}.mp3`))) throw new Error(`${id}: sfx ${name} tidak ada`);
      if (f) sfxCues.push({ id, name, t: f.start - f.T0 + Number(at), vol: vol ? Number(vol) : 0.5 });
    }
  const out = expand(src, id);
  writeFileSync(join(OUT, file.replace(/\.tpl$/, ".html")), `<!-- DIBANGKITKAN oleh tools/build.mjs dari src/frames/${file} — jangan edit langsung -->\n${out}`);
}
console.log(`built ${files.length} frame(s)`);

if (CUT) {
  // index-cut.html: hanya host frame, tanpa musik/VO/SFX
  const hosts = frames.filter((f) => f.src && existsSync(join(ROOT, f.src))).map((f) => {
    const s0 = f.start - f.T0, d = f.dur + f.T0;
    return `      <div id="${f.id}" class="clip" style="z-index:${f.z}" data-composition-id="${f.id}" data-composition-src="${f.src}" data-start="${s0.toFixed(2)}" data-duration="${d.toFixed(2)}" data-track-index="1" data-track-kind="graphics" data-width="1920" data-height="1080"></div>`;
  });
  const tpl = readFileSync(join(SRC, "index.tpl"), "utf8");
  writeFileSync(join(ROOT, "index.html"), tpl
    .replace("<!-- DIBANGKITKAN oleh tools/build.mjs dari src/index.tpl -->", "<!-- DIBANGKITKAN oleh tools/build.mjs --cut: versi presentasi (frame 1-13, tanpa audio) -->")
    .replace(/\n\s*<audio id="music-bed"[^\n]*/, "").replace(/\n\s*<!-- carve[^\n]*/, "")
    .replace("<!-- @frames -->", hosts.join("\n")).replace("<!-- @audio -->", "").replace(/\{\{total\}\}/g, TOTAL.toFixed(2)));
  console.log(`index (potong): ${hosts.length} frame, total ${TOTAL.toFixed(2)}s`);
  for (const f of frames) console.log(`  ${f.id} ${f.beats} beat, ${f.dur}s`);
  process.exit(0);
}

// ---- index.html ----
const hosts = [], audio = [];
for (const f of frames) {
  if (!f.src || !existsSync(join(ROOT, f.src))) continue;
  const s0 = f.start - f.T0, d = f.dur + f.T0;
  hosts.push(`      <div id="${f.id}" class="clip" style="z-index:${f.z}" data-composition-id="${f.id}" data-composition-src="${f.src}" data-start="${s0.toFixed(2)}" data-duration="${d.toFixed(2)}" data-track-index="1" data-width="1920" data-height="1080"></div>`);
  const vo = join(ROOT, "assets/audio/vo", `${f.id}.mp3`);
  if (existsSync(vo)) {
    const vd = JSON.parse(readFileSync(vo.replace(/\.mp3$/, ".json"), "utf8")).end + 0.3;
    audio.push(`      <audio id="vo-${f.id}" src="assets/audio/vo/${f.id}.mp3" data-start="${(f.start + f.voAt).toFixed(2)}" data-duration="${vd.toFixed(2)}" data-track-index="2" data-volume="1" data-audio-group="voiceover"></audio>`);
  }
}
// SFX: durasi asli berkas, jalur (track) dibagi supaya klip di satu jalur tidak tumpang-tindih
const sfxLen = {};
const lenOf = (name) => (sfxLen[name] ??= parseFloat(execFileSync("ffprobe", ["-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", join(ROOT, "assets/audio/sfx", `${name}.mp3`)]).toString()));
const laneEnd = [];
sfxCues.sort((a, b) => a.t - b.t).forEach((c, i) => {
  const s0 = Math.max(0, c.t), d = lenOf(c.name);
  let lane = laneEnd.findIndex((e) => e <= s0 - 0.01);
  if (lane < 0) lane = laneEnd.push(0) - 1;
  laneEnd[lane] = s0 + d;
  audio.push(`      <audio id="sfx-${String(i).padStart(2, "0")}-${c.name}" src="assets/audio/sfx/${c.name}.mp3" data-start="${s0.toFixed(2)}" data-duration="${d.toFixed(2)}" data-track-index="${4 + lane}" data-volume="${c.vol}" data-audio-group="sfx"></audio>`);
});
writeFileSync(join(ROOT, ".hyperframes-frames.json"), JSON.stringify(frames, null, 1));
const tpl = readFileSync(join(SRC, "index.tpl"), "utf8");
writeFileSync(
  join(ROOT, "index-full.html"),
  tpl.replace("<!-- @frames -->", hosts.join("\n")).replace("<!-- @audio -->", audio.join("\n")).replace(/\{\{total\}\}/g, TOTAL.toFixed(2)),
);
console.log(`index: ${hosts.length} frame, ${audio.length} audio, total ${TOTAL.toFixed(2)}s`);

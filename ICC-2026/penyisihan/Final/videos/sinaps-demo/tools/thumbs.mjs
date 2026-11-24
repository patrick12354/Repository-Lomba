// 5 pilihan thumbnail YouTube (1280x720) dari aset film: tokoh SVG, logo, slice MRI, rekaman MVP.
// Hasil: publish/thumbnail-1..5.png (+ sumber HTML di publish/thumbs-src/). Jalankan: node tools/thumbs.mjs
import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { execFileSync } from "node:child_process";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const OUT = join(ROOT, "publish");
const SRC = join(OUT, "thumbs-src");
mkdirSync(SRC, { recursive: true });
const CHROME = "C:/Program Files/Google/Chrome/Application/chrome.exe";

// partial SVG sama seperti tools/build.mjs
const parseAttrs = (s) => Object.fromEntries([...s.matchAll(/([\w-]+)=("[^"]*"|\S*)/g)].map(([, k, v]) => [k, v.replace(/^"|"$/g, "")]));
const part = (name, attrs = {}) => {
  let txt = readFileSync(join(ROOT, "src/parts", `${name}.svg`), "utf8");
  const m = txt.match(/^<!-- defaults: (.*?) -->\r?\n?/);
  const vals = { ...(m ? parseAttrs(m[1]) : {}), ...attrs };
  if (m) txt = txt.slice(m[0].length);
  return txt.replace(/\{\{([\w-]+)\}\}/g, (_, k) => vals[k]);
};
const A = "../../assets";
const fonts = readFileSync(join(ROOT, "assets/fonts/fonts.css"), "utf8").replaceAll("url('../fonts/", `url('${A}/fonts/`);

// otak dari titik neuron (deterministik): sebagian padam merah
let seed = 77;
const rnd = () => ((seed = (seed * 1664525 + 1013904223) >>> 0) / 4294967296);
const inBrain = (x, y) => ((x - 300) / 270) ** 2 + ((y - 230) / 190) ** 2 < 1 || ((x - 400) / 110) ** 2 + ((y - 420) / 70) ** 2 < 1;
let brain = "";
const pts = [];
while (pts.length < 330) { const x = rnd() * 600, y = rnd() * 520; if (inBrain(x, y)) pts.push([x, y, 3 + rnd() * 5, rnd() < 0.45]); }
pts.forEach(([x, y], i) => pts.slice(i + 1).filter(([a, b]) => (a - x) ** 2 + (b - y) ** 2 < 2200).slice(0, 2).forEach(([a, b]) => { brain += `<line x1="${x.toFixed(0)}" y1="${y.toFixed(0)}" x2="${a.toFixed(0)}" y2="${b.toFixed(0)}" stroke="#2c5560" stroke-width="2"/>`; }));
pts.forEach(([x, y, r, dead]) => { brain += `<circle cx="${x.toFixed(0)}" cy="${y.toFixed(0)}" r="${r.toFixed(1)}" fill="${dead ? "#ff3b3b" : "#5eead4"}" opacity="${dead ? 0.95 : 0.85}"/>`; });

const CSS = `
${fonts}
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1280px;height:720px;overflow:hidden;background:#0b1f25}
.T{position:absolute;inset:0;overflow:hidden;font-family:'Geist',sans-serif}
.h{position:absolute;font-family:'Oswald',sans-serif;font-weight:700;text-transform:uppercase;line-height:.9;color:#fff;-webkit-text-stroke:18px #0b1f25;paint-order:stroke fill;filter:drop-shadow(0 10px 0 rgba(0,0,0,.35))}
.h span{display:block}
.y{color:#fde047}.r{color:#ff5757}.g{color:#4ade80}.k{color:#0b1f25;-webkit-text-stroke-color:#fff}
.q{position:absolute;width:120px;height:120px;border-radius:50%;background:#fff;border:8px solid #ef4444;display:grid;place-items:center;font:700 92px/1 'Oswald',sans-serif;color:#ef4444;box-shadow:0 12px 0 rgba(0,0,0,.3)}
.pill{position:absolute;display:flex;align-items:center;gap:12px;padding:12px 22px;border-radius:999px;background:#fff;font:700 30px 'Geist',sans-serif;color:#0b1f25;box-shadow:0 8px 0 rgba(0,0,0,.25)}
.sl{position:absolute;width:300px;height:300px;border-radius:14px;border:5px solid #fff;box-shadow:0 14px 30px rgba(0,0,0,.5)}
.arm-scratch .dika-arm-r{transform-box:view-box;transform-origin:212px 272px;transform:rotate(-168deg)}
.arm-point .dika-arm-r{transform-box:view-box;transform-origin:212px 272px;transform:rotate(-120deg)}
.arm-up .dika-arm-l{transform-box:view-box;transform-origin:108px 272px;transform:rotate(40deg)}
.arm-up .dika-arm-r{transform-box:view-box;transform-origin:212px 272px;transform:rotate(-40deg)}
`;

const logo = part("logo", { p: "tl", w: 96 });
const T = [];
// 1 — koas bingung
T.push(`<div class="T" style="background:radial-gradient(circle at 72% 45%,#2a8c9c,#0f3a43 55%,#0b1f25)">
  <img class="sl" src="${A}/mri/sub-654/flair_z15.png" style="left:690px;top:40px;transform:rotate(-14deg)"/>
  <img class="sl" src="${A}/mri/sub-654/adc_z15.png" style="left:900px;top:20px;transform:rotate(9deg)"/>
  <img class="sl" src="${A}/mri/sub-654/dwi_z16.png" style="left:1010px;top:230px;transform:rotate(18deg)"/>
  <div class="arm-scratch" style="position:absolute;left:600px;top:110px">${part("dika", { p: "t1", w: 560, smile: 0, worried: 1, brows: 0, wbrows: 1, sweat: 1 })}</div>
  <div class="q" style="left:560px;top:470px;transform:rotate(-14deg)">?</div>
  <div class="q" style="left:1120px;top:120px;transform:rotate(12deg)">?</div>
  <div class="q" style="left:1150px;top:470px;transform:rotate(-8deg);width:96px;height:96px;font-size:72px">?</div>
  <div class="h" style="left:46px;top:60px;font-size:150px"><span class="y">Koas</span><span>bingung</span><span style="font-size:118px">baca MRI?!</span></div>
  <div class="pill" style="left:52px;top:600px">${logo.replace('width="96"', 'width="44"')}SINAPS jawabannya</div>
</div>`);
// 2 — chatbot ngarang vs SINAPS
T.push(`<div class="T" style="background:#0b1f25">
  <div style="position:absolute;inset:0;background:linear-gradient(135deg,#991b1b,#450a0a);clip-path:polygon(0 0,58% 0,42% 100%,0 100%)"></div>
  <div style="position:absolute;inset:0;background:linear-gradient(135deg,#1f6b7a,#0f3a43);clip-path:polygon(58% 0,100% 0,100% 100%,42% 100%)"></div>
  <div class="h" style="left:40px;top:34px;font-size:96px"><span>Chatbot</span><span class="r" style="font-size:210px">74%</span><span style="font-size:72px">ngarang</span></div>
  <div style="position:absolute;left:60px;top:500px;width:430px;padding:20px 24px;border-radius:24px;background:#fff;font:600 28px/1.3 'Geist',sans-serif;color:#22252b;transform:rotate(-4deg);box-shadow:0 12px 0 rgba(0,0,0,.3)">"Otak normal, tidak ada infark." <b style="color:#16a34a">yakin 96%</b><div style="position:absolute;right:-70px;top:-70px;font:700 150px/1 'Oswald';color:#ef4444;-webkit-text-stroke:10px #fff;paint-order:stroke fill">✕</div></div>
  <div style="position:absolute;left:574px;top:296px;width:132px;height:132px;border-radius:50%;background:#fde047;border:8px solid #0b1f25;display:grid;place-items:center;font:700 64px/1 'Oswald';color:#0b1f25;box-shadow:0 10px 0 rgba(0,0,0,.35)">VS</div>
  <div class="h" style="right:46px;top:34px;font-size:96px;text-align:right"><span>SINAPS</span><span class="g" style="font-size:210px">0</span><span style="font-size:58px">dari 432 jawaban</span></div>
  <div style="position:absolute;left:820px;top:430px">${part("sina", { p: "t2", w: 300, smile: 1 })}</div>
</div>`);
// 3 — 1,9 juta neuron
T.push(`<div class="T" style="background:radial-gradient(circle at 75% 50%,#3b0b0b,#0b1220 62%)">
  <svg style="position:absolute;left:640px;top:90px" width="620" height="540" viewBox="0 0 600 520">${brain}</svg>
  <div class="h" style="left:44px;top:70px;font-size:200px"><span class="y" style="-webkit-text-stroke-width:12px;letter-spacing:.02em;line-height:1.05;margin-bottom:-6px">1,9 juta</span><span style="font-size:112px">neuron hilang</span><span class="r" style="font-size:132px">tiap menit!</span></div>
  <svg style="position:absolute;left:1110px;top:40px" width="130" height="130" viewBox="-60 -60 120 120"><circle r="52" fill="#fff" stroke="#ef4444" stroke-width="10"/><line x1="0" y1="0" x2="0" y2="-34" stroke="#0b1f25" stroke-width="8" stroke-linecap="round"/><line x1="0" y1="0" x2="24" y2="10" stroke="#ef4444" stroke-width="7" stroke-linecap="round"/></svg>
  <div class="pill" style="left:50px;top:612px;background:#ef4444;color:#fff">stroke · waktu = otak</div>
</div>`);
// 4 — radiolog langka
const crowd = [[560, 380], [650, 430], [740, 395], [830, 450], [600, 540], [700, 570], [800, 545], [520, 470], [890, 380], [930, 520], [480, 590], [990, 440]]
  .map(([x, y], i) => `<div style="position:absolute;left:${x - 60}px;top:${y - 40}px">${part("mhs", { w: 96, q: i % 2 ? 1 : 0, skin: ["#d39a76", "#e2b08e", "#a96f4c", "#c48d68"][i % 4], hair: ["#1d2430", "#3b2a20", "#5a3a28"][i % 3] })}</div>`).join("");
T.push(`<div class="T" style="background:radial-gradient(circle at 30% 60%,#fff7c2,#fde047 60%,#f59e0b)">
  <div style="position:absolute;left:40px;top:150px">${part("dika", { p: "t4", w: 360, hair: "#9aa3a8", brow: "#6b7280", glasses: 1, skin: "#e2b08e", skin2: "#c48d68", scrub: "#5c4a7a", smile: 0, worried: 1, brows: 0, wbrows: 1, sweat: 1 })}</div>
  ${crowd}
  <div class="h k" style="right:40px;top:40px;font-size:118px;text-align:right"><span>Radiolog</span><span>cuma</span><span class="r" style="font-size:230px;-webkit-text-stroke-color:#fff">0,8</span></div>
  <div class="pill" style="right:46px;top:540px;font-size:34px;background:#0b1f25;color:#fff">per 100.000 penduduk</div>
  <div class="pill" style="right:46px;top:620px;font-size:34px;background:#ef4444;color:#fff">16× lebih sedikit dari Eropa</div>
</div>`);
// 5 — latihan MRI, langsung dinilai
T.push(`<div class="T" style="background:linear-gradient(135deg,#195764,#0b1f25)">
  <div style="position:absolute;left:470px;top:170px;width:780px;height:490px;border-radius:22px;overflow:hidden;border:6px solid #fff;transform:rotate(-3deg);box-shadow:0 26px 50px rgba(0,0,0,.5);background:#000">
    <img src="${A}/rec/skor_akhir.jpg" style="position:absolute;left:-150px;top:-60px;width:1050px"/>
  </div>
  <svg style="position:absolute;left:600px;top:250px" width="330" height="330" viewBox="0 0 330 330"><ellipse cx="160" cy="170" rx="120" ry="140" fill="none" stroke="#fde047" stroke-width="14" stroke-dasharray="40 14"/></svg>
  <svg style="position:absolute;left:380px;top:420px" width="260" height="160" viewBox="0 0 260 160"><path d="M10,140 C80,130 150,90 210,40" fill="none" stroke="#fde047" stroke-width="18" stroke-linecap="round"/><path d="M168,30 L230,22 L214,82 Z" fill="#fde047"/></svg>
  <div class="pill" style="left:1010px;top:150px;background:#fde047;font-size:40px;transform:rotate(4deg)">Dice 0,48</div>
  <div class="arm-point" style="position:absolute;left:30px;top:330px">${part("dika", { p: "t5", w: 330, smile: 1 })}</div>
  <div class="h" style="left:40px;top:28px;font-size:118px"><span class="y">Latihan MRI</span><span style="font-size:96px">langsung dinilai!</span></div>
  <div class="pill" style="right:40px;bottom:30px">${logo.replace('width="96"', 'width="44"')}SINAPS</div>
</div>`);

T.forEach((body, i) => {
  const html = `<!doctype html><html><head><meta charset="utf-8"><link href="https://fonts.googleapis.com/css2?family=Oswald:wght@700&display=block" rel="stylesheet"><style>${CSS}</style></head><body>${body}</body></html>`;
  const file = join(SRC, `thumbnail-${i + 1}.html`);
  writeFileSync(file, html);
  execFileSync(CHROME, ["--headless=new", "--disable-gpu", "--hide-scrollbars", "--allow-file-access-from-files", "--window-size=1280,720", "--virtual-time-budget=6000", `--screenshot=${join(OUT, `thumbnail-${i + 1}.png`)}`, pathToFileURL(file).href], { stdio: "ignore" });
  console.log(`thumbnail-${i + 1}.png`);
});

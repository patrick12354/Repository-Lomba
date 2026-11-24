// Lembar isyarat presenter untuk versi potong: kapan tiap beat mendarat dan kalimat yang diucapkan selama jedanya.
// Jalankan setelah `node tools/build.mjs --cut`: node tools/cues.mjs > PRESENTASI.md
import { readFileSync } from "node:fs";
const idx = readFileSync("index.html", "utf8");
const mmss = (t) => { const s = Math.round(t); return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`; };
const lines = ["# Isyarat presenter — SINAPS (versi potong, tanpa suara)", "",
  "Tiap baris = satu beat: animasinya mendarat di waktu itu, lalu layar diam sampai beat berikutnya.",
  "Ucapkan kalimatnya setelah animasi berhenti. Total " + mmss(+idx.match(/data-duration="([\d.]+)"/)[1]) + ".", "",
  "| Waktu | Jeda | Ucapkan |", "| --- | --- | --- |"];
const rows = [];
for (const m of idx.matchAll(/id="(f\d+[a-z]?)"[^>]*data-composition-src="([^"]+)" data-start="([\d.]+)"/g)) {
  const [, id, src, st] = m;
  const h = readFileSync(src, "utf8");
  const T0 = +h.match(/T0 = ([\d.]+)/)[1], VA = +h.match(/VO_AT = ([\d.]+)/)[1];
  const vow = JSON.parse(h.match(/VOW = (\[.*?\]);/)[1]);
  const words = JSON.parse(readFileSync(`assets/audio/vo/${id}.json`, "utf8")).words;
  let cur = null;
  words.forEach((x, i) => {
    if (!cur || vow[i][1] - vow[i - 1][1] > 0.6) { cur = { t: +st + T0 + VA + vow[i][1], text: [] }; rows.push(cur); }
    cur.text.push(x.w);
  });
}
rows.forEach((r, i) => {
  const next = rows[i + 1]?.t ?? +idx.match(/data-duration="([\d.]+)"/)[1];
  lines.push(`| ${mmss(r.t)} | ${(next - r.t).toFixed(0)} dtk | ${r.text.join(" ")} |`);
});
console.log(lines.join("\n"));

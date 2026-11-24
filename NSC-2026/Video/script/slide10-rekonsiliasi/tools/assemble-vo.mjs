// Trim tail silence, tempo 1.04, place lines on the timeline -> assets/vo.wav + assets/vo-timing.json
import fs from "node:fs";
import { execFileSync, spawnSync } from "node:child_process";
const TEMPO = 1.04, LEAD = 0.4;
const GAPS = [0.3, 0.25, 0.4, 0.2, 0.4, 0.25, 0.4, 0.25, 0.35, 0.2, 0.35];
const man = JSON.parse(fs.readFileSync("assets/vo/manifest.json", "utf8"));
let t = LEAD; const timing = []; const inputs = []; const filters = [];
man.forEach((l, i) => {
  const f = `assets/vo/${l.id}.mp3`;
  const r = require_log(f);
  const starts = [...r.matchAll(/silence_start: ([0-9.]+)/g)].map((m) => +m[1]);
  const ends = [...r.matchAll(/silence_end: ([0-9.]+)/g)].map((m) => +m[1]);
  // tail silence = last silence_start whose end ~ file end
  let end = l.duration;
  if (starts.length && ends.at(-1) >= l.duration - 0.05) end = starts.at(-1);
  end = Math.min(l.duration, end + 0.06);
  const dur = end / TEMPO;
  inputs.push("-i", f);
  filters.push(`[${i}:a]atrim=0:${end.toFixed(3)},atempo=${TEMPO},adelay=${Math.round(t * 1000)}|${Math.round(t * 1000)}[a${i}]`);
  // word timings (scaled)
  const a = l.alignment, words = []; let w = null;
  a.characters.forEach((c, k) => {
    if (/\s/.test(c)) { if (w) { words.push(w); w = null; } return; }
    if (!w) w = { w: "", s: +(t + a.character_start_times_seconds[k] / TEMPO).toFixed(3) };
    w.w += c; w.e = +(t + a.character_end_times_seconds[k] / TEMPO).toFixed(3);
  });
  if (w) words.push(w);
  timing.push({ id: l.id, text: l.text, start: +t.toFixed(3), end: +(t + dur).toFixed(3), words });
  t += dur + (GAPS[i] ?? 0);
});
function require_log(f) {
  return spawnSync("ffmpeg", ["-hide_banner", "-i", f, "-af", "silencedetect=n=-40dB:d=0.2", "-f", "null", "-"], { encoding: "utf8" }).stderr;
}
const mix = filters.join(";") + ";" + man.map((_, i) => `[a${i}]`).join("") + `amix=inputs=${man.length}:normalize=0,loudnorm=I=-16:TP=-1.5:LRA=7[out]`;
execFileSync("ffmpeg", ["-y", "-hide_banner", "-loglevel", "error", ...inputs, "-filter_complex", mix, "-map", "[out]", "-ar", "48000", "assets/vo.wav"], { stdio: "inherit" });
fs.writeFileSync("assets/vo-timing.json", JSON.stringify(timing, null, 1));
for (const x of timing) console.log(x.id, x.start, "->", x.end);

// Regenerate the voiceover with the ElevenLabs voice clone (voice in voice-lines.json) (character timestamps -> word timings).
// Usage: node scripts/make-voice-11labs.mjs              -> all lines missing a wav
//        node scripts/make-voice-11labs.mjs 05-overview  -> force one line
//        node scripts/make-voice-11labs.mjs --pauses     -> no TTS, re-apply the "pauses" of every line
// Raw TTS goes to assets/voice/raw/; assets/voice/NN-name.wav (+ .words.json) is the raw line with the
// line's "pauses" ([{ after: "<word as spoken>", s: seconds }]) cut in as silence, word timings shifted.
// Key: ELEVEN_LABS in videos/.env. Voice + settings: scripts/voice-lines.json ("elevenlabs").
import { readFileSync, writeFileSync, existsSync, mkdirSync } from "node:fs";
import { execFileSync } from "node:child_process";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

const root = fileURLToPath(new URL("..", import.meta.url));
const env = readFileSync(join(root, "../.env"), "utf8");
const key = env.match(/^ELEVEN_LABS\s*=\s*"?([^"\r\n]+)"?/m)?.[1]?.trim();
if (!key) throw new Error("ELEVEN_LABS missing in videos/.env");
const { elevenlabs: cfg, lines } = JSON.parse(readFileSync(join(root, "scripts/voice-lines.json"), "utf8"));
const pausesOnly = process.argv.includes("--pauses");
const only = process.argv.slice(2).filter((a) => !a.startsWith("--"));
const dir = join(root, "assets/voice"), rawDir = join(dir, "raw");
mkdirSync(rawDir, { recursive: true });

function applyPauses(l) {
  const words = JSON.parse(readFileSync(join(rawDir, `${l.id}.words.json`), "utf8"));
  const cuts = (l.pauses ?? []).map((p) => {
    const i = words.findIndex((w) => w.text === p.after);
    if (i < 0 || !words[i + 1]) throw new Error(`${l.id}: no word "${p.after}" with a word after it`);
    return { i, at: (words[i].end + words[i + 1].start) / 2, s: p.s };
  }).sort((a, b) => a.at - b.at);
  let shift = 0, k = 0;
  const out = words.map((w, j) => { while (k < cuts.length && cuts[k].i < j) shift += cuts[k++].s; return { ...w, start: +(w.start + shift).toFixed(3), end: +(w.end + shift).toFixed(3) }; });
  const raw = join(rawDir, `${l.id}.wav`), wav = join(dir, `${l.id}.wav`);
  if (!cuts.length) execFileSync("cp", [raw, wav]);
  else {
    const edges = [0, ...cuts.map((c) => c.at)];
    const parts = edges.map((a, n) => `[0]atrim=${a}${n + 1 < edges.length ? `:${edges[n + 1]}` : ""},asetpts=N/SR/TB[p${n}]`);
    const sil = cuts.map((c, n) => `aevalsrc=0:d=${c.s}:s=48000:c=mono[s${n}]`);
    const seq = edges.map((_, n) => `[p${n}]${n < cuts.length ? `[s${n}]` : ""}`).join("");
    execFileSync("ffmpeg", ["-loglevel", "error", "-y", "-i", raw, "-filter_complex", [...parts, ...sil, `${seq}concat=n=${edges.length + cuts.length}:v=0:a=1`].join(";"), "-ar", "48000", "-ac", "1", wav]);
  }
  writeFileSync(join(dir, `${l.id}.words.json`), JSON.stringify(out, null, 2));
}
if (pausesOnly) { for (const l of lines) applyPauses(l); process.exit(0); }

function toWords({ characters, character_start_times_seconds: s, character_end_times_seconds: e }) {
  const words = [];
  let cur = null;
  let tag = false; // eleven_v3 audio tags like [excited] are aligned too; they are not spoken words
  characters.forEach((c, i) => {
    if (c === "[") tag = true;
    if (tag) { if (c === "]") tag = false; return; }
    if (/\s/.test(c)) { if (cur) words.push(cur); cur = null; return; }
    if (!cur) cur = { text: "", start: s[i], end: e[i] };
    cur.text += c; cur.end = e[i];
  });
  if (cur) words.push(cur);
  return words.map((w, i) => ({ id: `w${i}`, text: w.text, start: +w.start.toFixed(3), end: +w.end.toFixed(3) }));
}

for (const l of lines) {
  const wav = join(rawDir, `${l.id}.wav`);
  if (only.length ? !only.includes(l.id) : existsSync(wav)) continue;
  console.log("tts", l.id);
  const res = await fetch(`https://api.elevenlabs.io/v1/text-to-speech/${cfg.voice}/with-timestamps?output_format=mp3_44100_128`, {
    method: "POST",
    headers: { "xi-api-key": key, "content-type": "application/json" },
    body: JSON.stringify({ text: l.text, model_id: cfg.model, voice_settings: cfg.settings, seed: cfg.seed }),
  });
  if (!res.ok) throw new Error(`${l.id}: ${res.status} ${await res.text()}`);
  const j = await res.json();
  const mp3 = wav.replace(/\.wav$/, ".mp3");
  writeFileSync(mp3, Buffer.from(j.audio_base64, "base64"));
  execFileSync("ffmpeg", ["-loglevel", "error", "-y", "-i", mp3, "-ar", "48000", "-ac", "1", wav]);
  execFileSync("rm", [mp3]);
  writeFileSync(join(rawDir, `${l.id}.words.json`), JSON.stringify(toWords(j.alignment), null, 2));
  applyPauses(l);
}

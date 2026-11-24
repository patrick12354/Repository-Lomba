// Voiceover per frame lewat ElevenLabs (eleven_v4, voice Senandika) + timestamp karakter.
// Teks diambil dari baris "- voiceover:" di STORYBOARD.md. Hasil: assets/audio/vo/fNN.mp3 + fNN.json
// Pakai: node tools/vo.mjs            (hanya frame yang belum ada)
//        node tools/vo.mjs 05 12      (paksa ulang frame tertentu)
import { readFileSync, writeFileSync, existsSync, mkdirSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const ENV = join(ROOT, "..", "..", "..", ".env"); // C:\Patrick\Satu Data\.env
const KEY = readFileSync(ENV, "utf8").match(/^ELEVENLABS\s*=\s*"?([^"\r\n]+)/m)?.[1].trim();
if (!KEY) throw new Error("ELEVENLABS tidak ada di .env");
const VOICE = "eESTQeTcGUli0jYysKtx";
const MODEL = "eleven_v4";
const OUT = join(ROOT, "assets", "audio", "vo");
mkdirSync(OUT, { recursive: true });

const sb = readFileSync(join(ROOT, "STORYBOARD.md"), "utf8");
const frames = [...sb.matchAll(/^## Frame (\d+):[^\n]*\n([\s\S]*?)(?=^## |(?![\s\S]))/gm)].map(([, n, body]) => ({
  id: String(n).padStart(2, "0"),
  text: (body.match(/^- voiceover: (.+)$/m)?.[1] ?? "").trim().replace(/^"|"$/g, ""),
}));
const force = new Set(process.argv.slice(2));

for (const [i, f] of frames.entries()) {
  const mp3 = join(OUT, `f${f.id}.mp3`);
  if (!f.text || (existsSync(mp3) && !force.has(f.id))) continue;
  const body = {
    text: f.text,
    model_id: MODEL,
    language_code: "id",
    previous_text: frames[i - 1]?.text,
    next_text: frames[i + 1]?.text,
    voice_settings: { stability: 0.5, similarity_boost: 0.8, style: 0.25, use_speaker_boost: true },
  };
  const res = await fetch(`https://api.elevenlabs.io/v1/text-to-speech/${VOICE}/with-timestamps?output_format=mp3_44100_128`, {
    method: "POST",
    headers: { "xi-api-key": KEY, "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`f${f.id}: ${res.status} ${await res.text()}`);
  const j = await res.json();
  writeFileSync(mp3, Buffer.from(j.audio_base64, "base64"));
  const a = j.alignment;
  // kata + waktu mulai/akhir, untuk menyinkronkan animasi ke ucapan
  const words = [];
  let cur = null;
  a.characters.forEach((ch, k) => {
    if (/\s/.test(ch)) { cur = null; return; }
    if (!cur) { cur = { w: "", s: a.character_start_times_seconds[k] }; words.push(cur); }
    cur.w += ch;
    cur.e = a.character_end_times_seconds[k];
  });
  writeFileSync(join(OUT, `f${f.id}.json`), JSON.stringify({ text: f.text, end: a.character_end_times_seconds.at(-1), words }, null, 1));
  console.log(`f${f.id}  ${a.character_end_times_seconds.at(-1).toFixed(2)}s  ${f.text.slice(0, 50)}`);
}

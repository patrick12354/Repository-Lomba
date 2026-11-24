// Generate VO slide 10 per kalimat via ElevenLabs (with timestamps).
// Usage: node tools/vo.mjs [voiceId]
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const proj = path.resolve(here, "..");
const envFile = path.resolve(proj, "../../.env");
const env = Object.fromEntries(
  fs.readFileSync(envFile, "utf8").split(/\r?\n/).filter((l) => l.includes("=")).map((l) => {
    const i = l.indexOf("=");
    return [l.slice(0, i).trim(), l.slice(i + 1).trim().replace(/^["']|["']$/g, "")];
  }),
);
const KEY = env.ELEVEN_LABS;
const VOICE = process.argv[2] || "jXSgE8fsSvkLuY04D16a"; // Basyar - Indonesian documentary narrator
const lines = JSON.parse(fs.readFileSync(path.join(proj, "vo-lines.json"), "utf8"));
const SPEED = Number(process.env.SPEED || 1.0);
const ONLY = process.env.ONLY ? process.env.ONLY.split(",").map(Number) : null;
const out = path.join(proj, process.env.OUT || "assets/vo");
fs.mkdirSync(out, { recursive: true });

const manifest = [];
for (let i = 0; i < lines.length; i++) {
  if (ONLY && !ONLY.includes(i + 1)) continue;
  const id = `line${String(i + 1).padStart(2, "0")}`;
  const body = {
    text: lines[i],
    model_id: "eleven_multilingual_v2",
    previous_text: lines.slice(0, i).join(" ").slice(-400) || undefined,
    next_text: lines[i + 1],
    voice_settings: { stability: 0.55, similarity_boost: 0.8, style: 0.15, use_speaker_boost: true, speed: SPEED },
  };
  const res = await fetch(`https://api.elevenlabs.io/v1/text-to-speech/${VOICE}/with-timestamps?output_format=mp3_44100_128`, {
    method: "POST",
    headers: { "xi-api-key": KEY, "content-type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`${id}: ${res.status} ${await res.text()}`);
  const j = await res.json();
  fs.writeFileSync(path.join(out, `${id}.mp3`), Buffer.from(j.audio_base64, "base64"));
  const a = j.alignment;
  const dur = a.character_end_times_seconds.at(-1);
  manifest.push({ id, text: lines[i], duration: dur, alignment: a });
  console.log(id, dur.toFixed(2) + "s", lines[i].slice(0, 50));
}
fs.writeFileSync(path.join(out, "manifest.json"), JSON.stringify(manifest, null, 1));

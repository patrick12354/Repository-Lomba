// Musik intro babak masalah (v4: Pak Budi; v5: Dika belajar sendiri malam-malam) → dua otak → waktu & radiolog → kelas → chatbot.
// Pakai: node tools/music_v4.mjs [--force]   (VERSI di bawah menentukan nama berkas intro)
// Intro (0 → awal frame "Kunci jawaban") digenerate ElevenLabs Music, lalu disambung dengan bed v3
// mulai detik 71,4 (awal "Opportunity" build-up di v3), supaya drop di reveal SINAPS tetap utuh.
// Hasil: assets/audio/music/bed_intro_v4.mp3 + assets/audio/music/bed.mp3   (bed v3 asli: bed_v3.mp3)
import { readFileSync, writeFileSync, existsSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { execFileSync } from "node:child_process";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const M = join(ROOT, "assets/audio/music");
const KEY = readFileSync(join(ROOT, "..", "..", "..", ".env"), "utf8").match(/^ELEVENLABS\s*=\s*"?([^"\r\n]+)/m)?.[1].trim();
const frames = JSON.parse(readFileSync(join(ROOT, ".hyperframes-frames.json"), "utf8"));
const at = (id) => frames.find((f) => f.id === id).start;
const CUT = at("f08"); // awal frame Kunci jawaban
const V3_TAIL = 71.4; // awal frame Kunci jawaban di v3

const S = (name, a, b, pos, neg = []) => ({ section_name: name, positive_local_styles: pos, negative_local_styles: neg, duration_ms: Math.round((b - a) * 1000), lines: [] });
const plan = {
  positive_global_styles: ["instrumental", "cinematic electronic", "124 bpm", "tense and urgent", "punchy modern drums", "leaves space for voiceover"],
  negative_global_styles: ["vocals", "lyrics", "horror", "lo-fi", "slow tempo", "sleepy", "cheesy"],
  sections: [
    S("Late night alone", 0, at("f02"), ["quiet lonely late night piano motif", "ticking clock percussion", "sudden dark tension hit", "low heartbeat pulse", "ominous pad swell", "tension building"], ["huge drums"]),
    S("Two causes", at("f02"), at("f03"), ["cinematic pulse", "tight kick on every beat", "staccato strings", "suspense", "mid energy rising"]),
    S("Time is brain", at("f03"), at("f04"), ["high urgency", "heartbeat kick", "dramatic stabs", "ticking clock percussion", "driving bass", "cinematic tension peak"]),
    S("Class story", at("f04"), at("f06"), ["lighter plucky synths", "curious bouncy groove", "school day vibe", "soft kick", "undercurrent of tension"], ["huge drums"]),
    S("Overwhelmed and confused", at("f06"), CUT, ["driving rhythm", "punchy kick and snare", "pulsing bassline", "urgent staccato plucks", "tension rising", "brief stop at the end"]),
  ],
};
const VERSI = "v5";
const intro = join(M, `bed_intro_${VERSI}.mp3`);
if (!existsSync(intro) || process.argv.includes("--force")) {
  const res = await fetch("https://api.elevenlabs.io/v1/music?output_format=mp3_44100_128", {
    method: "POST",
    headers: { "xi-api-key": KEY, "Content-Type": "application/json" },
    body: JSON.stringify({ composition_plan: plan }),
  });
  if (!res.ok) throw new Error(`${res.status} ${await res.text()}`);
  writeFileSync(intro, Buffer.from(await res.arrayBuffer()));
  console.log(`bed_intro_${VERSI}.mp3 ok`);
}
// sambung: intro dipotong tepat di CUT (fade-out 0,25 dtk), ekor v3 fade-in 0,12 dtk
execFileSync("ffmpeg", ["-y", "-v", "error",
  "-i", intro, "-i", join(M, "bed_v3.mp3"),
  "-filter_complex",
  `[0:a]atrim=0:${CUT},asetpts=PTS-STARTPTS,apad=whole_dur=${CUT},afade=t=out:st=${(CUT - 0.25).toFixed(2)}:d=0.25[a];` +
  `[1:a]atrim=start=${V3_TAIL},asetpts=PTS-STARTPTS,afade=t=in:st=0:d=0.12[b];[a][b]concat=n=2:v=0:a=1[o]`,
  "-map", "[o]", "-b:a", "192k", join(M, "bed.mp3")]);
console.log(`bed.mp3 = intro 0-${CUT.toFixed(1)}s + v3 ${V3_TAIL}s-akhir`);

// Musik latar ElevenLabs Music, bagian-bagiannya disejajarkan dengan babak di STORYBOARD.md.
// Hasil: assets/audio/music/bed.mp3
import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const KEY = readFileSync(join(ROOT, "..", "..", "..", ".env"), "utf8").match(/^ELEVENLABS\s*=\s*"?([^"\r\n]+)/m)?.[1].trim();
mkdirSync(join(ROOT, "assets/audio/music"), { recursive: true });

// batas babak (detik) dari STORYBOARD.md (v3: pembuka cerita kelas, total 256,2 dtk)
const S = (name, a, b, pos, neg = []) => ({
  section_name: name,
  positive_local_styles: pos,
  negative_local_styles: neg,
  duration_ms: Math.round((b - a) * 1000),
  lines: [],
});
// v2: lebih semangat dan bertenaga (permintaan user: "musiknya lebih semangat, lebih kencang")
const plan = {
  positive_global_styles: ["instrumental", "energetic upbeat electronic", "driving punchy drums", "motivational tech product launch", "bright modern synths", "confident and inspiring", "big but leaves space for voiceover", "124 bpm"],
  negative_global_styles: ["vocals", "lyrics", "sad", "horror", "lo-fi", "ambient drone", "slow tempo", "sleepy"],
  sections: [
    S("Class story", 0, 21.8, ["playful curious intro", "light plucky synths", "bouncy groove building", "school day vibe", "rising curiosity", "soft kick enters"], ["huge drums"]),
    S("Problem", 21.8, 50, ["driving rhythm", "punchy kick and snare", "pulsing bassline", "urgent staccato plucks", "tension rising", "mid-high energy"]),
    S("Data", 50, 71.4, ["serious driving pulse", "heartbeat-like kick", "dramatic stabs", "cinematic tension", "high urgency"]),
    S("Opportunity", 71.4, 88.6, ["big build-up", "snare roll accelerating", "rising synth arpeggio", "filter sweep opening", "anticipation peaking"]),
    S("Reveal", 88.6, 103.2, ["huge euphoric drop", "full drums", "anthemic bright synth lead", "wide supersaw chords", "triumphant"]),
    S("Architecture", 103.2, 169.7, ["energetic four on the floor groove", "rolling bass", "plucky synth arpeggios", "crisp claps", "techy and focused", "high energy"], ["busy lead melody"]),
    S("Demo", 169.7, 228.3, ["upbeat and bouncy", "funky groove bass", "claps and shakers", "playful synth hooks", "feel good high energy"], ["busy lead melody"]),
    S("Results and close", 228.3, 256.2, ["triumphant anthemic climax", "full drums", "uplifting chords", "big final hit", "short confident ending"]),
  ],

};
const res = await fetch("https://api.elevenlabs.io/v1/music?output_format=mp3_44100_128", {
  method: "POST",
  headers: { "xi-api-key": KEY, "Content-Type": "application/json" },
  body: JSON.stringify({ composition_plan: plan }),
});
if (!res.ok) throw new Error(`${res.status} ${await res.text()}`);
writeFileSync(join(ROOT, "assets/audio/music/bed.mp3"), Buffer.from(await res.arrayBuffer()));
console.log("bed.mp3 ok");

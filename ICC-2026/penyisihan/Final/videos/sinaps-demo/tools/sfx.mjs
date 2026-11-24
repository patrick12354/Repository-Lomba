// Palet SFX lewat ElevenLabs Sound Effects. Hasil: assets/audio/sfx/<nama>.mp3 (yang belum ada saja)
import { readFileSync, writeFileSync, existsSync, mkdirSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const KEY = readFileSync(join(ROOT, "..", "..", "..", ".env"), "utf8").match(/^ELEVENLABS\s*=\s*"?([^"\r\n]+)/m)?.[1].trim();
const OUT = join(ROOT, "assets/audio/sfx");
mkdirSync(OUT, { recursive: true });

const SFX = {
  whoosh: ["soft airy whoosh transition, clean, modern UI, short", 0.8],
  pop: ["single soft bubbly UI pop, clean, satisfying, short", 0.5],
  tick: ["single clock tick, crisp, close, dry", 0.5],
  heartbeat: ["two soft low heartbeats, muffled, cinematic but subtle", 1.4],
  glitch: ["short digital glitch stutter, electronic error, subtle", 0.8],
  stamp: ["rubber stamp thud on paper desk, punchy", 0.6],
  reveal: ["warm magical shimmer chime rising into a soft bloom, logo reveal, gentle", 2.4],
  click: ["single mouse click, clean, close mic", 0.5],
  brush: ["soft marker drawing stroke on glass, smooth swipe", 1.2],
  ding: ["pleasant success ding notification, bright, short", 0.9],
  typing: ["fast light keyboard typing, laptop, short burst", 1.6],
  lock: ["metal padlock snapping shut, crisp click", 0.6],
  blips: ["soft digital data blips, three quick ticks, friendly", 0.7],
  riser: ["short soft riser swell, airy, building tension, clean", 1.4],
  slide: ["card sliding on table, soft paper swipe", 0.5],
  clap: ["single high five hand clap, cheerful", 0.5],
  boing: ["cute soft cartoon boing, bouncy character jump, subtle", 0.6],
  // ---- palet v2: variasi supaya tidak ada bunyi yang diulang-ulang ----
  whoosh_deep: ["deep cinematic whoosh pass-by with low sub rumble, powerful transition", 1.0],
  swish_fast: ["very fast sharp swish, air cut, snappy UI transition", 0.5],
  whip: ["whip pan swoosh, quick camera whip transition, stereo", 0.6],
  swipe_zip: ["quick digital zip swipe, sci-fi UI panel sliding in", 0.5],
  reverse_suck: ["reverse cymbal swell sucking into a hit, short", 1.2],
  shimmer_sweep: ["bright glassy shimmer sweep, magical sparkle pass", 1.0],
  woosh_up: ["upward rising whoosh, swoosh going up, energetic", 0.8],
  woosh_down: ["downward falling whoosh, swoosh dropping down", 0.8],
  impact_boom: ["cinematic sub boom impact hit, deep punchy trailer hit", 1.4],
  punch_hit: ["tight punchy kick drum thump impact, modern motion graphics hit", 0.5],
  tension_hit: ["dramatic orchestral stab hit, tense and short", 1.2],
  bass_drop: ["short 808 bass drop with downward pitch sweep", 1.0],
  snap: ["crisp single finger snap, close", 0.5],
  counter_roll: ["fast digital number counter rolling, rapid ticking digits like a slot machine", 1.5],
  data_chirps: ["computer data processing chirps, futuristic beeps sequence, friendly", 1.2],
  scan_beam: ["sci-fi scanner beam sweep, laser scanning hum", 1.2],
  shutter: ["camera shutter click, snapshot", 0.5],
  error_buzz: ["wrong answer error buzzer, short digital", 0.6],
  sparkle: ["magical sparkle twinkle chimes, short and bright", 1.0],
  crowd_murmur: ["small group of university students murmuring and chattering indoors", 2.5],
  success_arp: ["bright ascending synth arpeggio success jingle, short and positive", 1.2],
  logo_sting: ["energetic modern logo sting, punchy hit with bright synth swell and sparkle tail", 3.0],
  marimba: ["single soft marimba note, mid pitch, clean, dry", 0.6],
  bubble: ["playful bubble pop, water droplet, cute", 0.5],
  hop: ["cartoon character hop jump, quick and springy", 0.5],
  slide_whistle: ["slide whistle going up, short and comedic", 0.8],
  glitch_heavy: ["heavy digital glitch burst, data corruption crunch", 1.0],
  card_flip: ["playing card flip, quick paper flick", 0.5],
  thud_soft: ["soft deep wooden thud, box landing on a table", 0.5],
  keys_clack: ["mechanical keyboard typing burst, fast, close mic", 1.2],
  notif_pop: ["modern app notification pop sound, bright and friendly", 0.5],
  tech_beep: ["single short high tech confirmation beep", 0.5],
  confetti: ["party popper confetti burst, celebratory", 1.0],
  lock_heavy: ["heavy metal vault lock clunk, solid and final", 0.8],
  heartbeat_fast: ["fast tense heartbeat pulses, cinematic low end", 2.0],
  pen_scribble: ["marker pen scribbling quickly on a whiteboard", 1.0],
  dbl_click: ["double mouse click, clean, close mic", 0.5],
  glass_tap: ["light glass tap ting, clean and bright", 0.5],
  ui_swell: ["soft airy UI swell with gentle chime at the end", 1.0],
  // ---- adegan kelas (pembuka v3) ----
  school_bell: ["short bright school bell ding dong chime, classroom", 1.5],
  projector_on: ["overhead projector switching on, click then soft fan whir", 1.2],
  paper_drop: ["stack of paper sheets dropping onto a wooden desk", 0.7],
  paper_rustle: ["quick paper sheets rustle and shuffle", 0.8],
  question_pop: ["quirky cartoon question pop, curious and playful", 0.5],
  clock_fast: ["clock ticking very fast, hurried ticks", 1.5],
  class_chatter: ["lecture hall students chatting before class starts, light murmur", 3.0],
  // ---- pembuka v4: pasien stroke (Pak Budi) ----
  siren_pass: ["ambulance siren approaching and passing by, doppler, cinematic, not too loud", 3.5],
  alarm_code: ["hospital emergency code alert, three urgent electronic beeps, clean", 1.6],
  monitor_beep: ["hospital heart monitor beeping steadily, three beeps", 1.6],
  morning_birds: ["calm morning birds chirping through a window, quiet room ambience", 3.0],
  tense_drone: ["short dark tense cinematic drone swell, suspense, low", 2.0],
  liquid_drip: ["single liquid drop into vial, clean medical", 0.6],
  // ---- pembuka v5: drama dosen (gaya sinetron) ----
  drama_zoom: ["dramatic soap opera zoom sting, three hard orchestral hits dun dun dun, telenovela drama, cheesy", 1.8],
  thunder: ["sharp thunder crack with short rumble, dramatic", 1.6],
  night_room: ["quiet night office ambience, distant crickets, soft fan hum", 3.0],
  book_open: ["hardcover book opening and pages flipping", 0.9],
};

for (const [name, [text, dur]] of Object.entries(SFX)) {
  const file = join(OUT, `${name}.mp3`);
  if (existsSync(file)) continue;
  const res = await fetch("https://api.elevenlabs.io/v1/sound-generation?output_format=mp3_44100_128", {
    method: "POST",
    headers: { "xi-api-key": KEY, "Content-Type": "application/json" },
    body: JSON.stringify({ text, duration_seconds: dur, prompt_influence: 0.55 }),
  });
  if (!res.ok) throw new Error(`${name}: ${res.status} ${await res.text()}`);
  writeFileSync(file, Buffer.from(await res.arrayBuffer()));
  console.log("sfx", name);
}

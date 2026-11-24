// Generate the few hand-placed SFX for slide 10 via ElevenLabs sound generation -> assets/sfx/*.mp3
// Usage: node tools/sfx.mjs   (key from Video/.env, falls back to ELEVEN_LABS_2/3 on quota errors)
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
const here = path.dirname(fileURLToPath(import.meta.url));
const proj = path.resolve(here, "..");
const env = Object.fromEntries(fs.readFileSync(path.resolve(proj, "../../.env"), "utf8").split(/\r?\n/).filter((l) => l.includes("=")).map((l) => { const i = l.indexOf("="); return [l.slice(0, i).trim(), l.slice(i + 1).trim().replace(/^["']|["']$/g, "")]; }));
const KEYS = [env.ELEVEN_LABS, env.ELEVEN_LABS_2, env.ELEVEN_LABS_3].filter(Boolean);
const SFX = {
  whoosh: ["fast soft camera whip pan whoosh, airy, short", 0.8],
  pin: ["single thumbtack pushed firmly into a cork board, small dry click, close up", 0.5],
  slap: ["index card slapped flat onto a cork board, light paper slap, close up", 0.5],
  stamp: ["rubber stamp pressed hard onto paper on a desk, single solid thud", 0.6],
  marker: ["felt tip marker quick stroke on paper, short squeak", 0.6],
  unroll: ["roll of paper chart being unrolled across a cork board, smooth paper rustle", 2.5],
  beep: ["tiny soft electronic sensor chirp, two quick gentle blips", 0.6],
};
const out = path.join(proj, "assets/sfx"); fs.mkdirSync(out, { recursive: true });
for (const [name, [text, dur]] of Object.entries(SFX)) {
  const f = path.join(out, name + ".mp3");
  if (fs.existsSync(f)) { console.log("skip", name); continue; }
  let ok = false;
  for (const key of KEYS) {
    const res = await fetch("https://api.elevenlabs.io/v1/sound-generation?output_format=mp3_44100_128", {
      method: "POST", headers: { "xi-api-key": key, "content-type": "application/json" },
      body: JSON.stringify({ text, duration_seconds: dur, prompt_influence: 0.6 }),
    });
    if (res.ok) { fs.writeFileSync(f, Buffer.from(await res.arrayBuffer())); console.log("ok", name); ok = true; break; }
    console.log("fail", name, res.status, (await res.text()).slice(0, 160));
  }
  if (!ok) process.exitCode = 1;
}

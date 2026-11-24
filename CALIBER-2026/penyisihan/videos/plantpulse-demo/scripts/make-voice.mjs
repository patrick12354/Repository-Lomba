// Regenerate the voiceover with HeyGen TTS (word timestamps included).
// Usage: node scripts/make-voice.mjs            -> all lines missing a wav
//        node scripts/make-voice.mjs 05-overview -> force one line
// Needs: `npx hyperframes auth login` (HeyGen) and the media-use skill installed.
import { readFileSync, existsSync } from "node:fs";
import { execFileSync } from "node:child_process";
import { homedir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

const root = fileURLToPath(new URL("..", import.meta.url));
const tts = join(homedir(), ".claude/skills/media-use/audio/scripts/heygen-tts.mjs");
const { voice, lines } = JSON.parse(readFileSync(join(root, "scripts/voice-lines.json"), "utf8"));
const only = process.argv.slice(2);
for (const l of lines) {
  const wav = join(root, "assets/voice", `${l.id}.wav`);
  if (only.length ? !only.includes(l.id) : existsSync(wav)) continue;
  console.log("tts", l.id);
  execFileSync("node", [tts, l.text, "-o", wav, "--voice", voice, "--words", join(root, "assets/voice", `${l.id}.words.json`)], { stdio: "inherit" });
}

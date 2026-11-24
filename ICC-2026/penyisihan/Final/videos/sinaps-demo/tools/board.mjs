// Tulis boards/storyboard.html dari STORYBOARD.md + still di boards/stills/
import { readFileSync, writeFileSync, readdirSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const sb = readFileSync(join(ROOT, "STORYBOARD.md"), "utf8");
const stills = readdirSync(join(ROOT, "boards/stills")).filter((f) => /^frame-\d+-at-.*\.png$/.test(f)).sort();
const esc = (s) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/"/g, "&quot;");
const fr = [...sb.matchAll(/^## Frame (\d+): (.+?) \(([\d.]+)-([\d.]+)s\)\n([\s\S]*?)(?=^## |(?![\s\S]))/gm)].map((m) => ({
  n: +m[1], title: m[2], a: +m[3], b: +m[4],
  act: m[5].match(/^- act: (.+)$/m)?.[1] ?? "",
  scene: m[5].match(/^- scene: (.+)$/m)?.[1] ?? "",
  vo: (m[5].match(/^- voiceover: (.+)$/m)?.[1] ?? "").replace(/^"|"$/g, ""),
}));
let last = "", body = "";
fr.forEach((f, i) => {
  if (f.act !== last) { body += `<section class="act">${esc(f.act)}</section>\n`; last = f.act; }
  body += `<div class="frame"><img src="stills/${stills[i]}" alt="" /><div class="title">${String(f.n).padStart(2, "0")}: ${esc(f.title)}</div><div class="time">${f.a.toFixed(1)} to ${f.b.toFixed(1)}s</div><p class="words">${esc(f.scene)}</p><p class="vo">“${esc(f.vo)}”</p></div>\n`;
});
writeFileSync(join(ROOT, "boards/storyboard.html"), `<!doctype html>
<html lang="id"><head><meta charset="UTF-8" /><meta name="viewport" content="width=device-width, initial-scale=1" />
<title>SINAPS — storyboard</title>
<style>
body { margin: 0; background: #f4f3ef; font-family: Inter, system-ui, sans-serif; color: #10313a; }
header { padding: 40px 48px 8px; } header h1 { margin: 0; font-size: 28px; } header p { margin: 8px 0 0; color: #5f655f; }
main { display: grid; grid-template-columns: repeat(auto-fill, minmax(420px, 1fr)); gap: 28px; padding: 24px 48px 64px; }
.act { grid-column: 1 / -1; font-weight: 700; font-size: 18px; letter-spacing: .06em; text-transform: uppercase; color: #195764; margin-top: 16px; border-bottom: 2px solid #e2dccd; padding-bottom: 8px; }
.frame { background: #fff; border-radius: 16px; overflow: hidden; box-shadow: 0 2px 10px rgba(16,49,58,.08); }
.frame img { display: block; width: 100%; aspect-ratio: 16/9; }
.title { padding: 14px 18px 0; font-weight: 700; } .time { padding: 2px 18px 0; color: #8a8f88; font-size: 13px; font-family: ui-monospace, monospace; }
.words { margin: 8px 18px 0; font-size: 14px; line-height: 1.45; } .vo { margin: 8px 18px 18px; font-size: 14px; line-height: 1.45; color: #5f655f; font-style: italic; }
</style></head><body>
<header><h1>SINAPS — video demo · storyboard</h1><p>${fr.length} frame · ±${Math.round(fr.at(-1).b)} detik · sketsa statis (belum ada motion). Frame demo memakai screenshot MVP sebagai placeholder rekaman layar asli.</p></header>
<main>
${body}</main></body></html>
`);
console.log(`board: ${fr.length} frame, ${stills.length} still`);

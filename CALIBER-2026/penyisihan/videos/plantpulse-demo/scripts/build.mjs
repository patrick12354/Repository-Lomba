// Generates index.html (the root timeline) and compositions/captions.html from scripts/timeline.json.
// Scenes themselves are hand-written in compositions/sNN-*.html; this file only places them in time
// and lays down voice, music, sound effects, captions and the persistent overlays.
// Usage: node scripts/build.mjs   (then: npx hyperframes check)
import { readFileSync, writeFileSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { join } from "node:path";
import { execFileSync } from "node:child_process";

const probe = (f) => Number(execFileSync("ffprobe", ["-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f]).toString().trim());

const root = fileURLToPath(new URL("..", import.meta.url));
const T = JSON.parse(readFileSync(join(root, "scripts/timeline.json"), "utf8"));
const r = (n) => Math.round(n * 1000) / 1000;

// ---- scene placement ------------------------------------------------------------------------
let t = 0;
const scenes = T.scenes.map((s) => {
  const words = JSON.parse(readFileSync(join(root, `assets/voice/${s.vo}.words.json`), "utf8"));
  const out = { ...s, start: r(t), words: words.map((w) => ({ ...w, g0: r(t + s.voAt + w.start), g1: r(t + s.voAt + w.end) })) };
  t += s.dur;
  return out;
});
const TOTAL = r(t);
const at = (id) => scenes.find((s) => s.id === id).start;

// ---- voice ----------------------------------------------------------------------------------
const voice = scenes.map((s) => `    <audio id="vo-${s.vo}" src="assets/audio/vo/${s.vo}.wav" data-start="${r(s.start + s.voAt)}" data-duration="${r(Math.min(probe(join(root, `assets/audio/vo/${s.vo}.wav`)), s.dur - s.voAt))}" data-track-index="20" data-volume="1"></audio>`);

// ---- music: duck under speech, lift in the gaps ---------------------------------------------
function envelope(clipStart, clipDur, lo, hi, extra = []) {
  // Speech spans (merged when the gap is short) pull the bed down to `lo`; gaps rise to `hi`.
  const spans = [];
  for (const s of scenes) for (const w of s.words) {
    const a = w.g0 - clipStart, b = w.g1 - clipStart;
    if (b < 0 || a > clipDur) continue;
    const last = spans[spans.length - 1];
    if (last && a - last[1] < 0.9) last[1] = b; else spans.push([a, b]);
  }
  const pts = [{ t: 0, v: hi }];
  for (const [a, b] of spans) {
    pts.push({ t: r(Math.max(0, a - 0.35)), v: hi }, { t: r(Math.max(0, a - 0.05)), v: lo }, { t: r(b + 0.1), v: lo }, { t: r(b + 0.5), v: hi });
  }
  for (const p of extra) pts.push(p);
  pts.sort((x, y) => x.t - y.t);
  const clean = pts.filter((p, i) => p.t >= 0 && p.t <= clipDur && (i === 0 || p.t > pts[i - 1].t));
  return JSON.stringify({ version: 1, lanes: [{ target: "volume", points: clean }] });
}
const m = T.music;
const act1Dur = r(Math.min(m.act1.dur, TOTAL - m.act1.at));
const act2At = r(at(m.act2.scene) + m.act2.local);
const act2Dur = r(TOTAL - act2At);
const music = [
  `    <audio id="music-act1" src="assets/audio/music/act1.wav" data-start="${m.act1.at}" data-duration="${act1Dur}" data-track-index="21" data-volume="1"
      data-automation='${envelope(m.act1.at, act1Dur, m.lo, m.hi, m.act1.extra.map((p) => ({ t: r(at(p.s) + p.t - m.act1.at), v: p.v })))}'></audio>`,
  `    <audio id="music-act2" src="assets/audio/music/act2.wav" data-start="${act2At}" data-duration="${act2Dur}" data-track-index="22" data-volume="1"
      data-automation='${envelope(act2At, act2Dur, m.lo, m.hi, [{ t: 0, v: 0 }, { t: 0.6, v: m.hi }, { t: r(act2Dur - 2.5), v: m.hi }, { t: r(act2Dur), v: 0 }])}'></audio>`,
];

// ---- sound effects (scene-local cue times in timeline.json) ---------------------------------
// Each cue gets the first SFX lane that is free at its start, so overlapping cues never share a lane.
const sfx = [], laneEnds = [];
for (const s of scenes) for (const [i, c] of (s.sfx ?? []).entries()) {
  const a = r(s.start + c.t), d = r(c.d ?? probe(join(root, `assets/sfx/${c.f}`)) - (c.ms ?? 0));
  let lane = laneEnds.findIndex((e) => e <= a); if (lane < 0) { lane = laneEnds.length; laneEnds.push(0); }
  laneEnds[lane] = a + d;
  sfx.push(`    <audio id="sfx-${s.id}-${i}" src="assets/sfx/${c.f}" data-start="${a}" data-duration="${d}" data-track-index="${30 + lane}" data-volume="${c.v ?? 0.35}"${c.ms ? ` data-media-start="${c.ms}"` : ""}></audio>`);
}

// ---- captions: phrases split at punctuation, one span per spoken word, the live word pops -------
// Spelled-out tokens the narrator needs ("R C A", "three hundred eighty") become one display word first,
// so a phrase break can never split them and the pop lands on the whole figure.
const MERGE = [[["April", "twenty-ninth", "twenty", "twenty-six"], "April 29, 2026"], [["K", "O", "thirty-two", "oh", "one"], "KO-3201"], [["R", "C", "A"], "RCA"], [["P", "I"], "PI"],
  [["three", "hundred", "and", "eighty"], "380"], [["three", "hundred", "eighty"], "380"], [["two", "hundred", "and", "twenty"], "220"], [["two", "hundred", "twenty"], "220"],
  [["One", "point", "five", "eight", "million", "dollars"], "US$1.58 million"], [["one", "point", "six", "million", "dollars"], "US$1.6 million"],
  [["twenty-three", "of", "twenty-three"], "23 of 23"]];
// Word-for-word display swaps, matched on whole token runs (punctuation kept): [spoken tokens, shown tokens].
const DISPLAY = [
  [["Thirty-two", "hours"], ["32", "hours"]], [["twelve", "plants"], ["12", "plants"]], [["five", "RCA"], ["5", "RCA"]], [["five", "root-cause"], ["5", "root-cause"]],
  [["six", "quality"], ["6", "quality"]], [["seven", "of", "nine"], ["7", "of", "9"]], [["four", "actions"], ["4", "actions"]], [["four", "fixes"], ["4", "fixes"]],
  [["Five", "of", "eleven"], ["5", "of", "11"]], [["five", "of", "eleven"], ["5", "of", "11"]], [["one", "of", "six"], ["1", "of", "6"]], [["All", "four"], ["All", "4"]],
  [["sixty"], ["60"]], [["forty-five"], ["45"]], [["sixteen"], ["16"]], [["twenty-three"], ["23"]], [["four", "different"], ["4", "different"]],
];
const strip = (x) => x.replace(/[.,:;?!]+$/, "");
const punct = (x) => x.match(/[.,:;?!]+$/)?.[0] ?? "";
for (const s of scenes) {
  const out = [];
  for (let i = 0; i < s.words.length; i++) {
    const hit = MERGE.find(([seq]) => seq.every((tok, k) => s.words[i + k] && strip(s.words[i + k].text) === tok));
    if (!hit) { out.push({ ...s.words[i] }); continue; }
    const last = s.words[i + hit[0].length - 1];
    out.push({ ...s.words[i], text: hit[1] + punct(last.text), g1: last.g1 });
    i += hit[0].length - 1;
  }
  for (let i = 0; i < out.length; i++) {
    const hit = DISPLAY.find(([seq]) => seq.every((tok, k) => out[i + k] && strip(out[i + k].text) === tok));
    if (hit) hit[1].forEach((tok, k) => { out[i + k].text = tok + punct(out[i + k].text); });
  }
  s.cap = out;
}
let phrases = [];
for (const s of scenes) {
  const ws = s.cap;
  let cur = [];
  const flush = () => { if (cur.length) phrases.push({ scene: s.id, g0: cur[0].g0, g1: cur[cur.length - 1].g1, words: cur }); cur = []; };
  ws.forEach((w, i) => {
    cur.push(w);
    const n = ws[i + 1];
    const words = cur.length;
    if (/[.,:;?!]$/.test(w.text) && (words >= 3 || /[.?!:]$/.test(w.text))) flush();
    else if (words >= 7) {
      // Never leave a one- or two-word orphan: hold the break if the sentence ends within two words.
      const rest = ws.slice(i + 1); const endAt = rest.findIndex((x) => /[.?!:,;]$/.test(x.text));
      if (endAt < 0 || endAt > 1) flush();
    }
    else if (n && n.g0 - w.g1 > 0.6) flush();
  });
  flush();
}
// Merge phrases that would flash for under 0.9 s into the next one in the same breath.
for (let i = 0; i < phrases.length - 1; i++) {
  if (phrases[i].g1 - phrases[i].g0 < 0.9 && phrases[i + 1].g0 - phrases[i].g1 < 0.4) {
    phrases[i + 1] = { ...phrases[i + 1], g0: phrases[i].g0, words: [...phrases[i].words, ...phrases[i + 1].words] };
    phrases.splice(i, 1); i--;
  }
}
// The tagline is already set huge on screen (s04 from "Check", all of s12): no caption doubling it.
phrases = phrases.filter((p) => !(p.scene === "s12-lockup" || (p.scene === "s04-thesis" && /^check/i.test(p.words[0].text))));
for (const p of phrases) { const l = p.words.at(-1); l.text = l.text.replace(/[,;:]$/, ""); }
const esc = (s) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;");
// Pop size per word: short words grow most, long ones less, so a grown word never touches its neighbours.
const pop = (txt) => r(Math.min(1.18, 1 + 18 / (Math.max(2, txt.length) * 19)));
const capHtml = `<!doctype html>
<html lang="en">
  <head><meta charset="UTF-8" /></head>
  <body>
    <template>
      <link rel="stylesheet" href="assets/pp.css" />
      <style>
        #caps { position: absolute; inset: 0; pointer-events: none; }
        #caps .cap { position: absolute; left: 0; right: 0; bottom: 58px; margin: 0 auto; max-width: 1400px; width: max-content;
          padding: 12px 22px 14px; border-radius: 14px; background: rgba(255, 255, 255, 0.92); border: 1px solid rgba(24, 38, 72, 0.14);
          box-shadow: 0 14px 34px -14px rgba(38, 48, 78, 0.45), 0 1px 0 #fff inset;
          font: 600 36px/1.3 var(--sans); color: var(--ink-hi); text-align: center; opacity: 0; letter-spacing: 0.005em; white-space: nowrap; }
        #caps .w { display: inline-block; padding: 0 0.09em; transform-origin: 50% 78%; opacity: 0.42; }
      </style>
      <div id="root" data-composition-id="captions" data-width="1920" data-height="1080">
        <div id="caps">
${phrases.map((p, i) => `          <div class="cap" id="cap-${i}" data-layout-allow-overlap>${p.words.map((w, k) => `<span class="w" id="cap-${i}-${k}">${esc(w.text)}</span>`).join(" ")}</div>`).join("\n")}
        </div>
      </div>
      <script>
        (() => {
          // [phrase start, phrase end, [[word start, word end, pop scale], ...]]
          const P = ${JSON.stringify(phrases.map((p) => [r(p.g0), r(p.g1), p.words.map((w) => [r(w.g0), r(w.g1), pop(strip(w.text))])]))};
          const tl = gsap.timeline({ paused: true });
          P.forEach(([a, b, W], i) => {
            const next = P[i + 1];
            const end = next && next[0] - b < 0.5 ? next[0] - 0.08 : b + 0.35;
            tl.fromTo("#cap-" + i, { opacity: 0, y: 10, scale: 0.97 }, { opacity: 1, y: 0, scale: 1, duration: 0.16, ease: "power2.out" }, Math.max(0, a - 0.06));
            W.forEach(([w0, w1, s], k) => {
              const el = "#cap-" + i + "-" + k;
              // Live until the next word starts (or a beat after it ends), then settles to read ink.
              const off = Math.min(W[k + 1] ? W[k + 1][0] : w1 + 0.2, w1 + 0.2) - 0.03;
              tl.fromTo(el, { scale: 1, y: 0, opacity: 0.42, color: "#0b1426" }, { scale: s, y: -3, opacity: 1, color: "#2f62e0", duration: 0.1, ease: "back.out(2.6)", immediateRender: false }, Math.max(0, w0 - 0.04));
              tl.fromTo(el, { scale: s, y: -3, opacity: 1, color: "#2f62e0" }, { scale: 1, y: 0, opacity: 1, color: "#0b1426", duration: 0.16, ease: "power2.out", immediateRender: false }, Math.max(w0 + 0.06, off));
            });
            tl.set("#cap-" + i, { opacity: 0 }, end);
          });
          window.__timelines["captions"] = tl;
        })();
      </script>
    </template>
  </body>
</html>
`;
writeFileSync(join(root, "compositions/captions.html"), capHtml);


// ---- index.html -----------------------------------------------------------------------------
const tagFrom = at(T.caseTag.from), tagTo = (() => { const s = scenes.find((x) => x.id === T.caseTag.to); return r(s.start + s.dur); })();
const host = (id, start, dur, track, extra = "") =>
  `    <div id="${id}" class="clip" data-composition-id="${id}" data-composition-src="compositions/${id}.html" data-start="${start}" data-duration="${dur}" data-track-index="${track}" data-width="1920" data-height="1080"${extra}></div>`;
const missing = scenes.filter((s) => !existsSync(join(root, `compositions/${s.id}.html`))).map((s) => s.id);
const html = `<!doctype html>
<!-- GENERATED by scripts/build.mjs from scripts/timeline.json. Edit those, not this file. -->
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1920, height=1080" />
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
    <link rel="stylesheet" href="assets/pp.css" />
    <style>
      * { margin: 0; padding: 0; box-sizing: border-box; }
      html, body { margin: 0; width: 1920px; height: 1080px; overflow: hidden; background: #faf8ee; }
      #root { position: relative; width: 100%; height: 100%; background: #faf8ee; overflow: hidden; }
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="${TOTAL}" data-width="1920" data-height="1080">
${host("atmos", 0, TOTAL, 0)}
${scenes.filter((s) => !missing.includes(s.id)).map((s) => host(s.id, s.start, s.dur, 1)).join("\n")}
${host("case-tag", tagFrom, r(tagTo - tagFrom), 5)}
${host("captions", 0, TOTAL, 6, ' data-track-kind="captions"')}
${host("grain", 0, TOTAL, 7)}
${voice.join("\n")}
${music.join("\n")}
${sfx.join("\n")}
    </div>
    <script>
      const tl = gsap.timeline({ paused: true });
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
`;
writeFileSync(join(root, "index.html"), html);
// ---- atmos: the continuous paper/Pipo ground keys its mood cues to scene starts ----------------
const atmosPath = join(root, "compositions/atmos.html");
const starts = Object.fromEntries([...scenes.map((s) => [s.id, s.start]), ["end", TOTAL]]);
writeFileSync(atmosPath, readFileSync(atmosPath, "utf8").replace(/const S = .*; \/\/ scene starts \(written by build\.mjs\)/, `const S = ${JSON.stringify(starts)}; // scene starts (written by build.mjs)`));
// ---- case tag: its band lights "evidence required" when the s10 narrator says "PlantPulse (says no / refuses)" ----
const s10 = scenes.find((s) => s.id === "s10-actions");
const refuse = s10.words.find((w, i) => w.text === "PlantPulse" && /^(refuses|says)/.test(s10.words[i + 1]?.text ?? ""));
const ctPath = join(root, "compositions/case-tag.html");
writeFileSync(ctPath, readFileSync(ctPath, "utf8").replace(/const C = .*; \/\/ cues \(written by build\.mjs\)/,
  `const C = ${JSON.stringify({ evidence: r(refuse.g0 + 0.11 - tagFrom), out: r(tagTo - tagFrom - 0.5) })}; // cues (written by build.mjs)`));
console.log(`index.html: ${scenes.length} scenes (${missing.length ? "missing: " + missing.join(", ") : "all present"}), ${TOTAL}s, ${phrases.length} caption phrases, ${sfx.length} sfx`);
console.log(scenes.map((s) => `${s.id.padEnd(18)} ${String(s.start).padStart(6)} → ${r(s.start + s.dur)}`).join("\n"));

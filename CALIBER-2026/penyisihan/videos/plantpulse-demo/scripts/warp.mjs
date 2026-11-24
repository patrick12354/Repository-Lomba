// Re-syncs every scene to the current voice. Each scene was animated against a reference voice:
//   s05–s11  the first voice (HeyGen "Jonah", v3)  -> scripts/authoring/timeline-v3.json + NN-name.words.json
//   s00–s03  Raphael's clone (v4)                  -> scripts/authoring/v4/timeline-v4.json + v4/NN-name.words.json
// Scene timelines keep their authored times; each one is wrapped in a seek-safe GSAP tween that maps
// authored time -> current time piecewise-linearly through every spoken word, so a move that landed on
// a word still lands on it. Sound-effect cues, the atmos mood keys and the music cues for those scenes
// are warped the same way. s12-lockup is not warped (its keyed mascot video keeps authored time); only
// its word reveals are re-timed to the current word starts.
// Usage: node scripts/warp.mjs   (after changing the voice or a scene's dur/voAt; then node scripts/build.mjs)
import { readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

const root = fileURLToPath(new URL("..", import.meta.url));
const REFS = [
  { dir: "scripts/authoring", timeline: "timeline-v3.json", ids: ["s05-overview", "s06-queue", "s07-evidence", "s08-checkup", "s09-ai", "s10-actions", "s11-trust"] },
  { dir: "scripts/authoring/v4", timeline: "timeline-v4.json", ids: ["s00-plant", "s01-trip", "s02-scatter", "s03-false-finish"] },
];
// Music cues authored against the v4 timeline, scene-local: act 1 cut on "But" (s03) and out under the logo.
const MUSIC = { act1: [["s03-false-finish", 4.1, 1.0], ["s03-false-finish", 4.6, 0.19], ["s03-false-finish", 8.1, 0.13], ["s04-thesis", 0.7, 0]], act2: ["s04-thesis", 6.1] };
// Words not used as anchors: s00 has a cut-in pause before "production", and the machine-stop cascade is
// meant to fill it, so the stretch runs from "stops," to the second "stops" instead.
const SKIP = { "s00-plant": ["production"] };
const r = (n) => Math.round(n * 1000) / 1000;
const norm = (w) => w.text.toLowerCase().replace(/[^a-z0-9']/g, "");
// Index pairs of the longest common subsequence of two word lists (compared without case or punctuation).
function lcs(a, b) {
  const A = a.map(norm), B = b.map(norm), L = A.map(() => new Array(B.length + 1).fill(0));
  L.push(new Array(B.length + 1).fill(0));
  for (let i = A.length - 1; i >= 0; i--) for (let j = B.length - 1; j >= 0; j--) L[i][j] = A[i] === B[j] ? L[i + 1][j + 1] + 1 : Math.max(L[i + 1][j], L[i][j + 1]);
  const out = [];
  for (let i = 0, j = 0; i < A.length && j < B.length;) {
    if (A[i] === B[j]) { out.push([i, j]); i++; j++; } else if (L[i + 1][j] >= L[i][j + 1]) i++; else j++;
  }
  return out;
}
const read = (p) => JSON.parse(readFileSync(join(root, p), "utf8"));
const T = read("scripts/timeline.json");
const maps = {};

for (const ref of REFS) {
  const OLD = read(`${ref.dir}/${ref.timeline}`);
  for (const id of ref.ids) {
    const o = OLD.scenes.find((s) => s.id === id), n = T.scenes.find((s) => s.id === id);
    const ow = read(`${ref.dir}/${o.vo}.words.json`), nw = read(`assets/voice/${n.vo}.words.json`);
    // Anchors [authored, current]: scene start, every word both voices share (longest common subsequence,
    // so a rewritten line still pins the moves on the words it kept), the last word's end, scene end.
    const P = [[0, 0], [o.voAt + ow[0].start, n.voAt + nw[0].start]];
    for (const [i, j] of lcs(ow, nw)) if (!(SKIP[id] ?? []).includes(norm(nw[j]))) P.push([o.voAt + ow[i].start, n.voAt + nw[j].start]);
    P.push([o.voAt + ow.at(-1).end, n.voAt + nw.at(-1).end]);
    P.push([o.dur, n.dur]);
    const mono = P.filter((p, i) => i === 0 || (p[0] > P[i - 1][0] && p[1] > P[i - 1][1])).map(([a, b]) => [r(a), r(b)]);
    const map = (t) => {
      for (let i = 1; i < mono.length; i++) if (t <= mono[i][0]) { const [a0, b0] = mono[i - 1], [a1, b1] = mono[i]; return b0 + (b1 - b0) * ((t - a0) / (a1 - a0)); }
      return mono.at(-1)[1] + (t - mono.at(-1)[0]);
    };
    maps[id] = { mono, map };
    n.sfx = (o.sfx ?? []).map((c) => ({ ...c, t: r(map(c.t)) }));

    const file = join(root, `compositions/${id}.html`);
    let html = readFileSync(file, "utf8");
    const helper = `// time-warp (written by scripts/warp.mjs): [authored s, current s] anchors through every spoken word.
          const WARP = ${JSON.stringify(mono)};
          window.__timelines["${id}"] = ((src, P) => {
            const end = P[P.length - 1];
            const back = (t) => { for (let i = 1; i < P.length; i++) if (t <= P[i][1]) { const [a0, b0] = P[i - 1], [a1, b1] = P[i]; return a0 + (a1 - a0) * ((t - b0) / (b1 - b0)); } return end[0]; };
            const w = gsap.timeline({ paused: true });
            w.fromTo(src, { time: 0 }, { time: end[0], duration: end[1], ease: (p) => back(p * end[1]) / end[0], immediateRender: true });
            return w;
          })(tl, WARP);`;
    const re = new RegExp(`// time-warp \\(written by scripts/warp\\.mjs\\)[\\s\\S]*?\\}\\)\\(tl, WARP\\);|window\\.__timelines\\["${id}"\\] = tl;`);
    if (!re.test(html)) throw new Error(`${id}: no timeline registration found`);
    writeFileSync(file, html.replace(re, helper));
    console.log(`${id.padEnd(17)} ${o.dur}s -> ${n.dur}s, ${mono.length} anchors`);
  }
}

// s04: the tagline is new words, so it is timed straight from the current voice (kicker on "one", the
// tagline word by word, the logo hangs off the last word). Its v4 map only shifts the logo beat.
{
  const n = T.scenes.find((s) => s.id === "s04-thesis"), nw = read(`assets/voice/${n.vo}.words.json`);
  const k = nw.findIndex((w) => norm(w) === "check");
  const at = nw.slice(k).map((w) => r(n.voAt + w.start)), K0 = r(n.voAt + nw.find((w) => norm(w) === "one").start);
  const file = join(root, "compositions/s04-thesis.html");
  writeFileSync(file, readFileSync(file, "utf8").replace(/const at = \[[^\]]*\];/, `const at = ${JSON.stringify(at)};`).replace(/const K0 = [0-9.]+;/, `const K0 = ${K0};`));
  const mono = [[0, 0], [4.51, at.at(-1)], [8, n.dur]]; // v4: last tagline word at 4.51 s, scene 8 s
  maps["s04-thesis"] = { mono, map: (t) => { for (let i = 1; i < mono.length; i++) if (t <= mono[i][0]) { const [a0, b0] = mono[i - 1], [a1, b1] = mono[i]; return b0 + (b1 - b0) * ((t - a0) / (a1 - a0)); } return mono.at(-1)[1] + (t - mono.at(-1)[0]); } };
  const o = read("scripts/authoring/v4/timeline-v4.json").scenes.find((s) => s.id === "s04-thesis");
  n.sfx = (o.sfx ?? []).map((c) => ({ ...c, t: r(maps["s04-thesis"].map(c.t)) }));
}

// s12: word-by-word reveal of the rule on the current voice.
{
  const n = T.scenes.find((s) => s.id === "s12-lockup"), nw = read(`assets/voice/${n.vo}.words.json`);
  const at = nw.slice(1).map((w) => r(n.voAt + w.start)); // word 0 is "PlantPulse.", carried by the wordmark
  const file = join(root, "compositions/s12-lockup.html");
  const html = readFileSync(file, "utf8").replace(/const at = \[[^\]]*\];/, `const at = ${JSON.stringify(at)};`);
  writeFileSync(file, html);
}

// Atmos mood keys are authored in v4 scene-local time: hand it the same maps.
{
  const W = Object.fromEntries([...REFS[1].ids, "s04-thesis"].map((id) => [id, maps[id].mono]));
  const file = join(root, "compositions/atmos.html");
  let html = readFileSync(file, "utf8");
  const line = `const W = ${JSON.stringify(W)}; // time-warp per scene (written by warp.mjs)`;
  html = /const W = .*; \/\/ time-warp per scene \(written by warp\.mjs\)/.test(html)
    ? html.replace(/const W = .*; \/\/ time-warp per scene \(written by warp\.mjs\)/, line)
    : html.replace(/(\n(\s*)const T = S\.end;)/, `\n$2${line}$1`);
  writeFileSync(file, html);
}

T.music.act1.extra = MUSIC.act1.map(([s, t, v]) => ({ s, t: r(maps[s].map(t)), v }));
T.music.act2 = { scene: MUSIC.act2[0], local: r(maps[MUSIC.act2[0]].map(MUSIC.act2[1])) };
writeFileSync(join(root, "scripts/timeline.json"), JSON.stringify(T, null, 1));

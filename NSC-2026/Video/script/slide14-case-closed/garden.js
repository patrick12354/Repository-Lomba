// garden.js — Pak Anton's greenhouse for the slide 14 ending, drawn with the same code as slide 1
// (copied from slide01-opening/index.html: greenhouse, plant generator, sensor, crate, jointed Pak Anton).
// Builds into the #gardenSvg groups and exposes the parts scene.js animates on window.GARDEN.
(function () {
const NS = "http://www.w3.org/2000/svg";
const INK = "#2b2521";
const $ = (s) => document.querySelector(s);
const f1 = (n) => (+n).toFixed(1);
const rad = (d) => (d * Math.PI) / 180;
function el(tag, attrs, parent) { const e = document.createElementNS(NS, tag); for (const k in attrs) e.setAttribute(k, attrs[k]); if (parent) parent.appendChild(e); return e; }
function rng(seed) { return () => { seed |= 0; seed = (seed + 0x6d2b79f5) | 0; let t = Math.imul(seed ^ (seed >>> 15), 1 | seed); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }
      // ───────────────────────── world: greenhouse ─────────────────────────
      const gSky = $("#gSky");
      el("rect", { x: -40, y: -40, width: 2000, height: 720, fill: "url(#sky)" }, gSky);
      el("path", { d: "M-40,585 C180,540 380,575 560,556 C760,536 920,580 1120,560 C1320,540 1520,578 1720,552 C1820,540 1900,556 1960,550 L1960,660 L-40,660 Z", fill: "#cbd4bd" }, gSky);
      el("path", { d: "M-40,612 C160,580 330,606 520,592 C720,578 900,612 1100,598 C1300,584 1520,614 1700,590 C1820,578 1900,592 1960,588 L1960,660 L-40,660 Z", fill: "#b3c09f" }, gSky);
      // back glass wall: mullions, rails, roof lines
      const glass = el("g", { stroke: "#8e9790", "stroke-linecap": "round" }, gSky);
      for (let x = 30; x <= 1900; x += 148) {
        el("line", { x1: x, y1: 96, x2: x, y2: 652, "stroke-width": 7 }, glass);
        el("line", { x1: x, y1: 96, x2: f1(960 + (x - 960) * 1.6), y2: -60, "stroke-width": 7 }, glass);
      }
      [96, 270, 448].forEach((y) => el("line", { x1: -40, y1: y, x2: 1960, y2: y, "stroke-width": y === 96 ? 10 : 6 }, glass));
      [30, -18].forEach((y) => el("line", { x1: -40, y1: y, x2: 1960, y2: y, "stroke-width": 6 }, glass));
      const refl = el("g", { stroke: "#ffffff", "stroke-width": 5, opacity: 0.45, "stroke-linecap": "round" }, gSky);
      for (let i = 0; i < 9; i++) { const x = 70 + i * 222; el("line", { x1: x, y1: 250, x2: x + 60, y2: 120 }, refl); el("line", { x1: x + 26, y1: 252, x2: x + 66, y2: 166 }, refl); }
      // light rays
      const rays = el("g", { id: "rays" }, gSky);
      [[180, 420], [620, 360], [1080, 300]].forEach(([x, w]) => el("polygon", { points: `${x},-40 ${x + w},-40 ${x + w + 520},1080 ${x + 380},1080`, fill: "url(#ray)", opacity: 0.55 }, rays));
      // soil + mulch rows
      el("rect", { x: -40, y: 640, width: 2000, height: 480, fill: "url(#soil)" }, gSky);
      el("line", { x1: -40, y1: 641, x2: 1960, y2: 641, stroke: INK, "stroke-width": 3, opacity: 0.6 }, gSky);
      const VP = [960, 560];
      [-520, 120, 760, 1400, 2040].forEach((bx) => {
        const w = 300, k = (650 - VP[1]) / (1080 - VP[1]);
        const tx = (x) => f1(VP[0] + (x - VP[0]) * k);
        el("polygon", { points: `${tx(bx - w / 2)},650 ${tx(bx + w / 2)},650 ${bx + w / 2},1080 ${bx - w / 2},1080`, fill: "#2f2a25", opacity: 0.9 }, gSky);
        el("line", { x1: tx(bx + w / 2), y1: 650, x2: bx + w / 2, y2: 1080, stroke: "#5d544a", "stroke-width": 4 }, gSky);
      });
      // soil clods
      const rc = rng(77);
      for (let i = 0; i < 60; i++) el("ellipse", { cx: f1(rc() * 1920), cy: f1(660 + rc() * 410), rx: f1(4 + rc() * 10), ry: f1(2 + rc() * 4), fill: "#3e2a1b", opacity: 0.35 }, gSky);

      // ───────────────────────── plants ─────────────────────────
      const GREENS = ["#5e8a39", "#6b9844", "#527d31", "#77a24c"];
      const WILTS = ["#b8a048", "#a99545", "#c4ab5a", "#9d8a3c", "#8e9a46"];
      const swayers = [];

      function leaflet(parent, bx, by, phi, l, w, fill, s, spot) {
        const ux = Math.cos(rad(phi)), uy = Math.sin(rad(phi)), px = -uy, py = ux;
        const tx = bx + ux * l, ty = by + uy * l, mx = bx + ux * l * 0.45, my = by + uy * l * 0.45;
        el("path", { d: `M${f1(bx)},${f1(by)} Q${f1(mx + px * w)},${f1(my + py * w)} ${f1(tx)},${f1(ty)} Q${f1(mx - px * w)},${f1(my - py * w)} ${f1(bx)},${f1(by)} Z`,
                     fill, stroke: INK, "stroke-width": f1(Math.max(1.6, 2.6 * s)), "stroke-linejoin": "round" }, parent);
        el("path", { d: `M${f1(bx)},${f1(by)} L${f1(bx + ux * l * 0.82)},${f1(by + uy * l * 0.82)}`, stroke: "rgba(30,40,15,0.45)", "stroke-width": f1(1.3 * s), fill: "none" }, parent);
        if (spot) el("circle", { cx: f1(mx + px * w * 0.3), cy: f1(my + py * w * 0.3), r: f1(w * 0.28), fill: "#6f4e22", opacity: 0.55 }, parent);
      }
      function leafCluster(parent, nx, ny, ang, L, s, wilt, r) {
        const ux = Math.cos(rad(ang)), uy = Math.sin(rad(ang));
        const ex = nx + ux * L, ey = ny + uy * L + wilt * L * 0.16;
        const cx = nx + ux * L * 0.5, cy = ny + uy * L * 0.5 - (1 - wilt) * L * 0.1;
        el("path", { d: `M${f1(nx)},${f1(ny)} Q${f1(cx)},${f1(cy)} ${f1(ex)},${f1(ey)}`, fill: "none", stroke: INK, "stroke-width": f1(4.2 * s + 1.5), "stroke-linecap": "round" }, parent);
        el("path", { d: `M${f1(nx)},${f1(ny)} Q${f1(cx)},${f1(cy)} ${f1(ex)},${f1(ey)}`, fill: "none", stroke: wilt > 0.5 ? "#7f7c3a" : "#4f6e2c", "stroke-width": f1(3.2 * s), "stroke-linecap": "round" }, parent);
        const pick = () => (r() < wilt ? WILTS[Math.floor(r() * WILTS.length)] : GREENS[Math.floor(r() * GREENS.length)]);
        const at = (t) => [(1 - t) * (1 - t) * nx + 2 * (1 - t) * t * cx + t * t * ex, (1 - t) * (1 - t) * ny + 2 * (1 - t) * t * cy + t * t * ey];
        const droop = (phi) => phi + (90 - phi) * wilt * 0.5;
        [[0.38, 55, 0.4], [0.38, -55, 0.4], [0.7, 48, 0.46], [0.7, -48, 0.46], [1.0, 0, 0.52]].forEach(([t, d, k]) => {
          const [bx, by] = at(t);
          leaflet(parent, bx, by, droop(ang + d + (r() - 0.5) * 16), L * k, L * k * 0.36, pick(), s, wilt > 0.3 && r() < wilt * 0.6);
        });
        return { ex, ey };
      }
      function tomatoes(parent, nx, ny, side, s, r) {
        const n = 2 + Math.floor(r() * 2);
        for (let k = 0; k < n; k++) {
          const cx = nx + side * (10 + k * 15) * s, cy = ny + (22 + (k % 2) * 12) * s, rr = (12 + r() * 3) * s;
          const ripe = r() < 0.65;
          el("line", { x1: f1(nx), y1: f1(ny), x2: f1(cx), y2: f1(cy - rr), stroke: "#4f6e2c", "stroke-width": f1(2.4 * s) }, parent);
          el("circle", { cx: f1(cx), cy: f1(cy), r: f1(rr), fill: ripe ? "#c8372d" : "#9db34f", stroke: INK, "stroke-width": f1(2.4 * s) }, parent);
          el("ellipse", { cx: f1(cx - rr * 0.35), cy: f1(cy - rr * 0.35), rx: f1(rr * 0.28), ry: f1(rr * 0.18), fill: "#fff", opacity: 0.55 }, parent);
          el("path", { d: `M${f1(cx - rr * 0.5)},${f1(cy - rr * 0.85)} L${f1(cx)},${f1(cy - rr * 0.6)} L${f1(cx + rr * 0.5)},${f1(cy - rr * 0.85)}`, stroke: "#3f6a25", "stroke-width": f1(3 * s), fill: "none", "stroke-linecap": "round" }, parent);
        }
      }
      function plant(parent, x, baseY, s, o) {
        const r = rng(o.seed), wilt = o.wilt || 0, h = 560 * s * (o.hMul || 1), dir = o.dir || 1;
        const g = el("g", {}, parent);
        const P0 = [x, baseY], P1 = [x + (r() - 0.5) * 30 * s, baseY - h * 0.6], P2 = [x + dir * h * 0.3 * wilt + (r() - 0.5) * 16 * s, baseY - h + h * 0.2 * wilt];
        const q = (t) => [(1 - t) ** 2 * P0[0] + 2 * (1 - t) * t * P1[0] + t * t * P2[0], (1 - t) ** 2 * P0[1] + 2 * (1 - t) * t * P1[1] + t * t * P2[1]];
        if (o.string) el("line", { x1: f1(P2[0]), y1: 96, x2: f1(P2[0]), y2: f1(P2[1]), stroke: "#f1ead8", "stroke-width": 1.8, opacity: 0.75 }, g);
        const d = `M${f1(P0[0])},${f1(P0[1])} Q${f1(P1[0])},${f1(P1[1])} ${f1(P2[0])},${f1(P2[1])}`;
        el("path", { d, fill: "none", stroke: INK, "stroke-width": f1(7 * s + 2.5), "stroke-linecap": "round" }, g);
        el("path", { d, fill: "none", stroke: wilt > 0.5 ? "#7f7c3a" : "#4f6e2c", "stroke-width": f1(7 * s), "stroke-linecap": "round" }, g);
        const fruitG = el("g", {}, g);
        [0.2, 0.33, 0.46, 0.58, 0.7, 0.82, 0.93].forEach((t, i) => {
          const [nx, ny] = q(t), side = i % 2 ? 1 : -1;
          const L = 150 * s * (0.78 + r() * 0.32) * (t > 0.9 ? 0.75 : 1);
          const a = wilt > 0 ? -12 + wilt * 66 + r() * 14 : -32 + r() * 30;
          const cg = el("g", { transform: `rotate(0 ${f1(nx)} ${f1(ny)})` }, g);
          leafCluster(cg, nx, ny, side > 0 ? a : 180 - a, L, s, wilt, r);
          if (o.sway) swayers.push({ g: cg, nx, ny, amp: (wilt > 0.5 ? 1.2 : 2.6) * (0.7 + r() * 0.6), per: 1.5 + r() * 1.3 });
          if (o.fruit && i >= 1 && i <= 4 && r() < o.fruit) tomatoes(fruitG, nx, ny, -side, s, r);
        });
        g.appendChild(fruitG);
        return { g, q };
      }

      for (let i = 0, x = 20; x < 1940; x += 74, i++) plant($("#gBackPlants"), x + (i % 2) * 12, 664, 0.42, { seed: 100 + i, fruit: 0.5, string: true });
      [110, 250, 395, 1190, 1470, 1615, 1760, 1900].forEach((x, i) => plant($("#gMidPlants"), x, 772, 0.62, { seed: 300 + i, fruit: 0.7, string: true, sway: true }));

// ── the plants that recover: each one drawn wilted and healthy, scene.js crossfades them ──
const pairs = [];
function pairPlant(parent, x, baseY, s, o) {
  const gW = el("g", { class: "wiltV" }, parent), gH = el("g", { class: "healV", opacity: 0 }, parent);
  plant(gW, x, baseY, s, o);
  plant(gH, x, baseY, s, { ...o, wilt: 0, fruit: o.fruitH ?? 0.7, seed: o.seed + 50 });
  pairs.push({ gW, gH, x, baseY });
}
pairPlant($("#gInspect"), 1090, 1018, 0.95, { seed: 501, wilt: 0.9, dir: 1, sway: true });
pairPlant($("#gFront"), 300, 1090, 1.15, { seed: 611, wilt: 0.75, dir: -1, sway: true });
pairPlant($("#gFront"), 150, 1075, 1.0, { seed: 612, wilt: 0.35, sway: true, fruit: 0.5 });
plant($("#gFront"), 1610, 1095, 1.2, { seed: 613, fruit: 0.8, sway: true });
pairPlant($("#gFront"), 1800, 1080, 1.0, { seed: 614, wilt: 0.5, sway: true });

      // ───────────────────────── sensor on its pole ─────────────────────────
      const gS = $("#gSensor");
      el("rect", { x: 1332, y: 210, width: 18, height: 700, fill: "url(#metal)", stroke: INK, "stroke-width": 4 }, gS);
      el("ellipse", { cx: 1341, cy: 910, rx: 30, ry: 8, fill: "#2a1d12", opacity: 0.45 }, gS);
      el("rect", { x: 1322, y: 292, width: 38, height: 22, rx: 4, fill: "#8d938f", stroke: INK, "stroke-width": 3.5 }, gS);
      // radiation shield (stacked discs)
      for (let i = 0; i < 6; i++) el("path", { d: `M1262,${282 + i * 15} Q1293,${270 + i * 15} 1324,${282 + i * 15} L1318,${290 + i * 15} Q1293,${280 + i * 15} 1268,${290 + i * 15} Z`, fill: "#f2f1ea", stroke: INK, "stroke-width": 3 }, gS);
      el("rect", { x: 1286, y: 270, width: 14, height: 100, fill: "#d9dbd6", stroke: INK, "stroke-width": 3, opacity: 0.0 }, gS);
      // logger box
      el("rect", { x: 1358, y: 270, width: 70, height: 92, rx: 6, fill: "#dfe1dc", stroke: INK, "stroke-width": 4 }, gS);
      el("rect", { x: 1368, y: 282, width: 50, height: 30, rx: 3, fill: "#c4c8c2", stroke: INK, "stroke-width": 2.5 }, gS);
      el("line", { x1: 1410, y1: 270, x2: 1414, y2: 196, stroke: INK, "stroke-width": 5, "stroke-linecap": "round" }, gS);
      el("circle", { cx: 1414, cy: 194, r: 6, fill: INK }, gS);
      el("line", { x1: 1378, y1: 270, x2: 1376, y2: 226, stroke: INK, "stroke-width": 4, "stroke-linecap": "round" }, gS);
      el("circle", { id: "led", cx: 1376, cy: 340, r: 6.5, fill: "#5fbf5a", stroke: INK, "stroke-width": 2 }, gS);
      const wifi = el("g", { fill: "none", stroke: "#3f8fd0", "stroke-width": 6, "stroke-linecap": "round" }, gS);
      const wifiInk = el("g", { fill: "none", stroke: INK, "stroke-width": 11, "stroke-linecap": "round", opacity: 0.0 }, gS);
      [18, 34, 50].forEach((rr, i) => {
        const d = `M${1426},${f1(194 - rr * 0.8)} A${rr},${rr} 0 0 1 ${1426},${f1(194 + rr * 0.8)}`;
        el("path", { class: "wfInk", d, opacity: 0 }, wifiInk);
        el("path", { class: "wf", d, opacity: 0 }, wifi);
      });
      wifiInk.setAttribute("opacity", 1);
      wifi.parentNode.appendChild(wifi);

      // ───────────────────────── crate + notebook ─────────────────────────
      const gC = $("#gCrate");
      el("polygon", { points: "462,862 728,862 746,914 444,914", fill: "#a77a4b", stroke: INK, "stroke-width": 4, "stroke-linejoin": "round" }, gC);
      el("rect", { x: 444, y: 914, width: 302, height: 128, fill: "#8a6139", stroke: INK, "stroke-width": 4 }, gC);
      [944, 976, 1008].forEach((y) => el("line", { x1: 444, y1: y, x2: 746, y2: y, stroke: INK, "stroke-width": 2.5, opacity: 0.55 }, gC));
      [470, 720].forEach((x) => el("rect", { x: x - 10, y: 914, width: 20, height: 128, fill: "#74502f", stroke: INK, "stroke-width": 3 }, gC));
      const nbW = el("g", { id: "nbWorld", transform: "rotate(-6 595 885)" }, gC);
      el("rect", { x: 510, y: 838, width: 170, height: 95, rx: 4, fill: "#2f3d4f", stroke: INK, "stroke-width": 3.5 }, nbW);
      el("rect", { x: 560, y: 870, width: 70, height: 22, fill: "#efe5cf" }, nbW);
      for (let i = 0; i < 11; i++) el("rect", { x: 518 + i * 15, y: 832, width: 4, height: 12, rx: 2, fill: "#8a8e93" }, nbW);
      el("line", { x1: 640, y1: 930, x2: 712, y2: 902, stroke: "#e8b23c", "stroke-width": 7, "stroke-linecap": "round" }, gC);

      // ───────────────────────── Pak Anton (jointed puppet) ─────────────────────────
      const HIP = [800, 860];
      const A = $("#anton");
      A.setAttribute("transform", `translate(${HIP[0]} ${HIP[1]})`);
      const tube = (parent, d, w, col) => { el("path", { d, fill: "none", stroke: INK, "stroke-width": w + 8, "stroke-linecap": "round", "stroke-linejoin": "round" }, parent); el("path", { d, fill: "none", stroke: col, "stroke-width": w, "stroke-linecap": "round", "stroke-linejoin": "round" }, parent); };
      // legs
      tube(A, "M-12,6 L74,-40 L70,104", 46, "#77684a");
      el("path", { d: "M44,64 L96,64 L98,126 Q128,128 134,148 L44,148 Z", fill: "#2f2b28", stroke: INK, "stroke-width": 4, "stroke-linejoin": "round" }, A);
      const torso = el("g", { id: "torso", transform: "translate(0 0) scale(1 1)" }, A);
      // far arm (behind torso)
      const mkArm = (parent, sleeve, skin) => {
        const g = el("g", {}, parent);
        const o = {
          ink: el("path", { fill: "none", stroke: INK, "stroke-width": 31, "stroke-linecap": "round", "stroke-linejoin": "round" }, g),
          up: el("path", { fill: "none", stroke: sleeve, "stroke-width": 23, "stroke-linecap": "round", "stroke-linejoin": "round" }, g),
          fo: el("path", { fill: "none", stroke: "#000", "stroke-opacity": 0, "stroke-width": 5, "stroke-linecap": "round", "stroke-linejoin": "round" }, g),
          cuffInk: el("path", { fill: "none", stroke: INK, "stroke-width": 33, "stroke-linecap": "butt" }, g),
          cuff: el("path", { fill: "none", stroke: sleeve === "#6b7541" ? "#5b6437" : "#484f2b", "stroke-width": 25, "stroke-linecap": "butt" }, g),
          hand: el("g", { transform: "translate(0 0) rotate(0)" }, g),
        };
        el("ellipse", { cx: 7, cy: 0, rx: 17, ry: 13.5, fill: skin, stroke: INK, "stroke-width": 3.5 }, o.hand);
        el("path", { d: "M10,-10 Q20,-16 24,-8", fill: "none", stroke: INK, "stroke-width": 3, "stroke-linecap": "round" }, o.hand);
        el("ellipse", { cx: 4, cy: -12, rx: 8, ry: 5.5, fill: skin, stroke: INK, "stroke-width": 3, transform: "rotate(-30 4 -12)" }, o.hand);
        el("path", { d: "M12,2 L22,2 M11,8 L20,8", stroke: INK, "stroke-width": 2, opacity: 0.6 }, o.hand);
        return o;
      };
      const farArmEls = mkArm(torso, "#555e33", "#b37a50");
      // torso
      el("path", { d: "M-42,22 C-50,-58 -42,-140 -8,-184 L62,-190 C92,-160 106,-98 102,-38 C100,-2 82,24 52,30 Z", fill: "#66703e", stroke: INK, "stroke-width": 4.5, "stroke-linejoin": "round" }, torso);
      el("path", { d: "M-42,22 C-50,-58 -42,-140 -8,-184 L4,-184 C-18,-130 -22,-60 -10,24 Z", fill: "#525b31", opacity: 0.8 }, torso);
      el("path", { d: "M64,-172 C72,-120 76,-60 72,12", fill: "none", stroke: INK, "stroke-width": 2.5, opacity: 0.55 }, torso);
      el("path", { d: "M26,-136 L52,-138 L54,-112 L28,-110 Z", fill: "#5b6536", stroke: INK, "stroke-width": 2.5, opacity: 0.9 }, torso);
      // neck
      el("path", { d: "M38,-206 L74,-206 L72,-180 L40,-180 Z", fill: "#b97c51", stroke: INK, "stroke-width": 3.5 }, torso);
      el("path", { d: "M26,-190 L50,-166 L70,-194 L60,-184 L50,-176 L36,-192 Z", fill: "#5c6537", stroke: INK, "stroke-width": 3.5, "stroke-linejoin": "round" }, torso);
      // head
      const headT = el("g", { transform: "translate(70 -238)" }, torso);
      const head = el("g", { id: "headR", transform: "rotate(4 -5 40)" }, headT);
      el("path", { d: "M-52,-6 C-58,-40 -30,-60 2,-58 L-8,12 C-30,24 -48,20 -52,-6 Z", fill: INK }, head);
      el("path", { d: "M-46,-8 C-48,-44 -14,-58 16,-54 C40,-51 52,-36 52,-18 C52,-10 55,-5 60,-1 C68,4 72,12 67,18 C63,22 57,21 53,21 C53,29 51,37 45,46 C37,56 23,60 8,58 C-22,58 -44,32 -46,-8 Z", fill: "#c98a5e", stroke: INK, "stroke-width": 4.5, "stroke-linejoin": "round" }, head);
      el("path", { d: "M-44,4 C-40,34 -20,54 6,57 C-14,44 -30,28 -36,4 Z", fill: "#a96d47", opacity: 0.55 }, head);
      el("path", { d: "M-46,-16 L-28,-18 L-32,14 L-46,8 Z", fill: INK }, head);
      el("ellipse", { cx: -30, cy: 4, rx: 9, ry: 13, fill: "#c98a5e", stroke: INK, "stroke-width": 3.5 }, head);
      el("path", { d: "M-31,-2 Q-26,4 -31,10", fill: "none", stroke: INK, "stroke-width": 2.2 }, head);
      // eyes
      const eyes = el("g", {}, head);
      [[8, -6, 9.5, 10.5], [35, -7, 8, 9.5]].forEach(([x, y, rx, ry]) => el("ellipse", { class: "eyeW", cx: x, cy: y, rx, ry, fill: "#fbf6ea", stroke: INK, "stroke-width": 2.8 }, eyes));
      const pupils = el("g", { id: "pupils", transform: "translate(3 3)" }, eyes);
      [[9, -6], [36, -7]].forEach(([x, y]) => el("ellipse", { class: "eyeP", cx: x, cy: y, rx: 4.6, ry: 5.2, fill: INK }, pupils));
      el("path", { id: "browN", d: "M-6,-24 Q6,-32 20,-26", fill: "none", stroke: INK, "stroke-width": 6.5, "stroke-linecap": "round", transform: "translate(0 0) rotate(0 7 -27)" }, head);
      el("path", { id: "browF", d: "M26,-28 Q37,-34 47,-26", fill: "none", stroke: INK, "stroke-width": 6, "stroke-linecap": "round", transform: "translate(0 0) rotate(0 36 -30)" }, head);
      el("path", { d: "M54,6 C51,10 51,16 55,19", fill: "none", stroke: INK, "stroke-width": 2.6, "stroke-linecap": "round", opacity: 0.7 }, head);
      el("ellipse", { cx: 63, cy: 6, rx: 3.6, ry: 2.4, fill: "#fff", opacity: 0.35, transform: "rotate(30 63 6)" }, head);
      
      el("path", { d: "M22,31 Q28,23 38,24 Q45,21 51,23 Q55,26 52,31 Q49,35 43,33 Q38,32 33,35 Q25,37 22,31 Z", fill: INK }, head);
      el("path", { id: "mouth", d: "M34,43 Q40,41 46,43", fill: "none", stroke: INK, "stroke-width": 3, "stroke-linecap": "round" }, head);
      // caping (conical straw hat)
      el("path", { d: "M-50,-26 Q4,-6 58,-26 L58,-14 Q4,6 -50,-14 Z", fill: "#000", opacity: 0.16 }, head);
      el("path", { d: "M-104,-30 Q2,-2 110,-36 L8,-118 Z", fill: "#d8b56a", stroke: INK, "stroke-width": 4.5, "stroke-linejoin": "round" }, head);
      const weave = el("g", { stroke: "#a8843f", "stroke-width": 2.2, fill: "none", opacity: 0.8 }, head);
      [-80, -52, -24, 6, 36, 66, 92].forEach((bx) => el("line", { x1: 8, y1: -116, x2: bx, y2: f1(-24 + Math.abs(bx - 3) * -0.05), "stroke-linecap": "round" }, weave));
      [0.35, 0.62, 0.85].forEach((k) => el("path", { d: `M${f1(8 - 112 * k)},${f1(-118 + 88 * k)} Q${f1(5)},${f1(-118 + 112 * k)} ${f1(8 + 102 * k)},${f1(-118 + 82 * k)}` }, weave));
      el("path", { d: "M-104,-30 Q2,-2 110,-36", fill: "none", stroke: "#8f6d32", "stroke-width": 3 }, head);
      // near leg (in front of torso) and near arm (in front of everything)
      tube(A, "M10,16 L110,-18 L104,108", 52, "#8c7a55");
      el("path", { d: "M76,68 L130,68 L132,130 Q166,132 172,154 L76,154 Z", fill: "#363130", stroke: INK, "stroke-width": 4, "stroke-linejoin": "round" }, A);
      el("path", { d: "M84,80 L124,80", stroke: "#57504b", "stroke-width": 4 }, A);
      const nearArmEls = mkArm(A, "#6b7541", "#c98a5e");

      // ───────────────────────── arm IK (baked into keyframes) ─────────────────────────
      const L1 = 92, L2 = 88;
      const toLocal = (p) => [p[0] - HIP[0], p[1] - HIP[1]];
      const arms = {
        far: { S: [50, -166], els: farArmEls, ang: 0 },
        near: { S: [16, -150], els: nearArmEls, ang: 0 },
      };
      function pose(arm, T) {
        const [sx, sy] = arm.S;
        const dx = T[0] - sx, dy = T[1] - sy;
        const d = Math.min(L1 + L2 - 1, Math.max(Math.abs(L1 - L2) + 1, Math.hypot(dx, dy)));
        const a = Math.atan2(dy, dx);
        const b = Math.acos((L1 * L1 + d * d - L2 * L2) / (2 * L1 * d));
        const E = [sx + L1 * Math.cos(a + b), sy + L1 * Math.sin(a + b)];
        const H = [sx + d * Math.cos(a), sy + d * Math.sin(a)];
        let ang = (Math.atan2(H[1] - E[1], H[0] - E[0]) * 180) / Math.PI;
        while (ang - arm.ang > 180) ang -= 360;
        while (ang - arm.ang < -180) ang += 360;
        arm.ang = ang;
        const ux = Math.cos(rad(ang)), uy = Math.sin(rad(ang));
        const P = (p) => `${f1(p[0])},${f1(p[1])}`;
        const at = (k) => [H[0] - ux * k, H[1] - uy * k];
        const W = at(12); // wrist: the cuff ends where the hand begins
        // crease: a short fold on the inside of the elbow, follows the bend
        const ex = (S0, E0, k) => [E0[0] + (S0[0] - E0[0]) * k, E0[1] + (S0[1] - E0[1]) * k];
        const c0 = ex(arm.S, E, 0.22), c1 = [E[0] + ux * 16, E[1] + uy * 16];
        return {
          ink: `M${P(arm.S)} L${P(E)} L${P(W)}`, up: `M${P(arm.S)} L${P(E)} L${P(W)}`, fo: `M${P(c0)} L${P(E)} L${P(c1)}`,
          cuffInk: `M${P(at(26))} L${P(at(9))}`, cuff: `M${P(at(24))} L${P(at(11))}`, hand: `translate(${f1(H[0])} ${f1(H[1])}) rotate(${f1(ang)})`,
        };
      }
      function armSet(arm, T) { const p = pose(arm, T); for (const k of ["ink", "up", "fo", "cuffInk", "cuff"]) arm.els[k].setAttribute("d", p[k]); arm.els.hand.setAttribute("transform", p.hand); }
      function armMove(tl, arm, targetAt, t, dur, ease, n = 10) {
        const E = gsap.parseEase(ease);
        for (let i = 1; i <= n; i++) {
          const p = pose(arm, targetAt(E(i / n)));
          const at = t + ((i - 1) * dur) / n, d = dur / n;
          for (const k of ["ink", "up", "fo", "cuffInk", "cuff"]) tl.to(arm.els[k], { attr: { d: p[k] }, duration: d, ease: "none" }, at);
          tl.to(arm.els.hand, { attr: { transform: p.hand }, duration: d, ease: "none" }, at);
        }
      }
      const lerp2 = (a, b) => (p) => [a[0] + (b[0] - a[0]) * p, a[1] + (b[1] - a[1]) * p];
      const REST_F = [104, -36], REST_N = [130, -30], CHIN = [108, -190];
      armSet(arms.far, REST_F);
      armSet(arms.near, REST_N);

// thumbs-up: a thumb that sticks out along the hand's local +x (shown when the forearm points up)
const thumb = el("ellipse", { id: "thumbUp", cx: 14, cy: -22, rx: 18, ry: 8.5, fill: "#c98a5e", stroke: INK, "stroke-width": 3.4, opacity: 0, transform: "rotate(-75 14 -22)" }, nearArmEls.hand);

// thought bubble: the drop of humidity, now with a tick instead of slide 1's question mark
const gB = $("#gBubble");
const bubT = [el("g", { transform: "translate(948 560) scale(0)" }, gB), el("g", { transform: "translate(972 528) scale(0)" }, gB)];
el("circle", { cx: 0, cy: 0, r: 9, fill: "#fbf6ea", stroke: INK, "stroke-width": 3.5 }, bubT[0]);
el("circle", { cx: 0, cy: 0, r: 14, fill: "#fbf6ea", stroke: INK, "stroke-width": 3.5 }, bubT[1]);
const bub = el("g", { id: "bubble", transform: "translate(1036 452) scale(0)" }, gB);
el("ellipse", { cx: 0, cy: 0, rx: 92, ry: 72, fill: "#fbf6ea", stroke: INK, "stroke-width": 4.5 }, bub);
el("path", { d: "M-36,-36 C-24,-14 -12,-2 -12,14 A24,24 0 0 1 -60,14 C-60,-2 -48,-14 -36,-36 Z", fill: "#3f8fd0", stroke: INK, "stroke-width": 3.5 }, bub);
el("ellipse", { cx: -44, cy: 8, rx: 5, ry: 9, fill: "#fff", opacity: 0.7 }, bub);
el("path", { d: "M8,4 L28,26 L64,-22", fill: "none", stroke: "#4f8a33", "stroke-width": 15, "stroke-linecap": "round", "stroke-linejoin": "round" }, bub);

// greenhouse posts (foreground)
const gP = $("#gPosts");
[[46, 52], [1874, 52]].forEach(([x, w]) => el("rect", { x: x - w / 2, y: -40, width: w, height: 1160, fill: "url(#metal)", stroke: INK, "stroke-width": 5 }, gP));
el("rect", { x: -40, y: -40, width: 2000, height: 58, fill: "url(#metal)", stroke: INK, "stroke-width": 5 }, gP);

window.GARDEN = { swayers, pairs, arms, armMove, armSet, lerp2, REST_F, REST_N, HIP, bubT, bub, wifi, f1 };
})();

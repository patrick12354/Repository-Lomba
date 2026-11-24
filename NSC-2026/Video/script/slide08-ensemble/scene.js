// Slide 8 — Combining the Evidence (55 s, muted; the presenter speaks the script live).
// Five models, three day-bands (no clock boundaries invented), one NNLS per band, shrinkage.
// Every thread has the same weight on purpose: the real per-band weights are not drawn.
// 0,080 vs 0,007 come from the report (nested-validation audit, equal-parameter random control).
const { el, txt, f1, INK, RED, NAVY, GOLD } = BOARD;
const B = BOARD.make({ duration: 55, title: "WAKTU MEMBANTU PENGGABUNGAN MODEL", act: "THE INVESTIGATION", titleSize: 56 });
const { tl, L } = B;
const out = "expo.out";

// ───────────── the five models ─────────────
const MODELS = [["LightGBM Huber", "#a91d1a"], ["CatBoost Huber", "#3c6e9a"], ["ElasticNet", "#5e7a3a"], ["Ridge-e", "#6d4f8a"], ["LightGBM L2", "#b8732a"]];
const my = (k) => 250 + k * 166;
const models = MODELS.map(([n, c], k) => {
  const s = B.card(L.papers, 130, my(k), 600, 140, [0.8, -0.7, 0.5, -0.9, 0.6][k], 70 + k);
  el("rect", { x: 0, y: 0, width: 22, height: 140, fill: c }, s.c);
  txt(n, { x: 50, y: 98, "font-size": 50, "font-weight": 700, fill: INK }, s.c);
  return { s, pin: B.pin(L.top, 430, my(k) + 14, "deco", c) };
});

// threads run under the papers they cross
const UND = el("g", {}, L.papers);

// ───────────── method card ─────────────
const MC = B.sheet(L.papers, 850, 214, 1220, 156, { seed: 19, amp: 5, step: 12, rot: -0.6 });
txt("TIME-BANDED ENSEMBLE", { x: 610, y: 74, "font-size": 64, fill: RED, "text-anchor": "middle", class: "rus" }, MC.c);
txt("Non-Negative Least Squares (NNLS)", { x: 610, y: 130, "font-size": 42, "font-weight": 700, "text-anchor": "middle", fill: INK }, MC.c);

// ───────────── three parts of the day ─────────────
const DSH = B.sheet(L.papers, 850, 400, 1220, 270, { seed: 23, amp: 6, step: 12, rot: 0.4, fill: "#f4ecd9" });
const bx = (j) => 1060 + j * 400; // board centre x of band j
const bands = [0, 1, 2].map((j) => {
  const g = el("g", { transform: `translate(${30 + j * 400} 24)` }, DSH.c);
  const sky = [["#26344f", "#55607a"], ["#9cc3dd", "#e8eef0"], ["#d77a43", "#3c3550"]][j];
  const gid = "sky" + j, lg = el("linearGradient", { id: gid, x1: 0, y1: 0, x2: 0, y2: 1 }, B.defs);
  el("stop", { offset: 0, "stop-color": sky[0] }, lg); el("stop", { offset: 1, "stop-color": sky[1] }, lg);
  el("rect", { x: 0, y: 0, width: 360, height: 150, fill: `url(#${gid})`, stroke: INK, "stroke-width": 4 }, g);
  el("path", { d: "M0,150 L60,112 L120,132 L190,96 L260,128 L320,104 L360,124 L360,150 Z", fill: "#3d4a3a", opacity: 0.85 }, g);
  if (j === 0) { el("circle", { cx: 120, cy: 60, r: 30, fill: "#f2ecd2" }, g); el("circle", { cx: 134, cy: 52, r: 27, fill: "#2c3a55" }, g); [[220, 40], [270, 70], [60, 36], [300, 30]].forEach(([x, y]) => el("circle", { cx: x, cy: y, r: 3.5, fill: "#f2ecd2" }, g)); }
  if (j === 1) { el("circle", { cx: 180, cy: 64, r: 34, fill: "#f2b53c", stroke: "#c9852a", "stroke-width": 4 }, g); for (let a = 0; a < 360; a += 30) { const r1 = 46, r2 = 64, c = Math.cos((a * Math.PI) / 180), s = Math.sin((a * Math.PI) / 180); el("line", { x1: f1(180 + c * r1), y1: f1(64 + s * r1), x2: f1(180 + c * r2), y2: f1(64 + s * r2), stroke: "#e39a2c", "stroke-width": 5, "stroke-linecap": "round" }, g); } }
  if (j === 2) { el("circle", { cx: 120, cy: 112, r: 38, fill: "#f0a050" }, g); el("circle", { cx: 280, cy: 46, r: 22, fill: "#f2ecd2" }, g); el("circle", { cx: 290, cy: 40, r: 20, fill: "#4a4058" }, g); }
  const lbl = txt("Pita " + (j + 1), { x: 180, y: 218, "font-size": 52, "font-weight": 700, "text-anchor": "middle", fill: INK }, g);
  return { g, lbl };
});
const bandNote = txt("bagian waktu dalam sehari · skema", { x: 1460, y: 706, "font-size": 36, "font-style": "italic", "text-anchor": "middle", fill: "#efe5cf", stroke: "#2b2521", "stroke-width": 9, "paint-order": "stroke", opacity: 0 }, L.mid);
const nBest = B.note(L.notes, 1110, 700, 700, 150, 2.0, ["Model terbaik bisa", "berbeda tiap bagian hari"], { seed: 51, fill: "#e3cf86", fs: [38, 42] });

// ───────────── NNLS per band + threads from every model ─────────────
const NY = 820;
const nodes = [0, 1, 2].map((j) => {
  const g = el("g", { transform: `translate(${bx(j)} ${NY})` }, L.top);
  const i = el("g", {}, g);
  el("ellipse", { cx: 0, cy: 0, rx: 130, ry: 62, fill: "#f4ecd9", stroke: RED, "stroke-width": 6, filter: "url(#shPin)" }, i);
  txt("NNLS", { x: 0, y: 17, "font-size": 50, "font-weight": 700, "text-anchor": "middle", fill: INK }, i);
  const w = txt("bobot ≥ 0", { x: 0, y: 118, "font-size": 44, "font-weight": 700, "text-anchor": "middle", fill: INK, opacity: 0 }, g);
  return { g, i, w };
});
const ths = [];
[0, 1, 2].forEach((j) => MODELS.forEach(([, c], k) => {
  const y0 = my(k) + 70, x1 = bx(j) - 128;
  ths.push({ j, th: B.thread(UND, `M735,${y0} C${f1(820 + j * 90)},${y0} ${f1(x1 - 150)},${NY} ${f1(x1)},${NY}`, c, 4.5) });
}));

// ───────────── shrinkage ─────────────
const SK = B.sheet(L.papers, 1290, 1040, 340, 100, { seed: 29, amp: 4, step: 10, rot: -0.8, fill: "#d9c9a3" });
txt("SHRINKAGE", { x: 170, y: 68, "font-size": 50, fill: INK, "text-anchor": "middle", class: "rus" }, SK.c);
const zig = (x0, y0, x1, y1, n = 9, a = 16) => { const pts = []; for (let i = 0; i <= n * 2; i++) { const t = i / (n * 2), x = x0 + (x1 - x0) * t, y = y0 + (y1 - y0) * t, dx = -(y1 - y0), dy = x1 - x0, L0 = Math.hypot(dx, dy), o = i === 0 || i === n * 2 ? 0 : (i % 2 ? a : -a); pts.push(`${f1(x + (dx / L0) * o)},${f1(y + (dy / L0) * o)}`); } return "M" + pts.join(" L"); };
const springs = [0, 1, 2].map((j) => el("path", { d: zig(bx(j), NY + 140, 1460 + (j - 1) * 110, 1040), fill: "none", stroke: "#5d574f", "stroke-width": 5, "stroke-linejoin": "round" }, L.threads));
const skCap = txt("menahan bobot agar tidak terlalu mengikuti validasi", { x: 1460, y: 1196, "font-size": 38, "font-weight": 700, "text-anchor": "middle", fill: "#efe5cf", stroke: "#2b2521", "stroke-width": 9, "paint-order": "stroke", opacity: 0 }, L.mid);

// ───────────── control: same number of parameters, random bands ─────────────
const RS = B.sheet(L.papers, 850, 1236, 1220, 170, { seed: 37, amp: 5, step: 12, rot: -0.4, fill: "#f4ecd9" });
const pal = ["#3b4766", "#e3c46a", "#c26a3a"], order = [1, 2, 0, 2, 1, 0, 0, 2, 1, 2, 0, 1, 1, 0, 2, 0];
const slices = order.map((c, i) => el("rect", { x: 30 + i * 72, y: 22, width: 66, height: 70, fill: pal[c], stroke: INK, "stroke-width": 2.5, opacity: 0 }, RS.c));
txt("Pembagian acak · jumlah parameter setara", { x: 30, y: 144, "font-size": 38, "font-weight": 700, fill: INK }, RS.c);
const nQ = B.note(L.notes, 880, 1428, 1160, 132, -0.8, ["Informasi waktu, atau parameter bertambah?"], { seed: 53, fill: "#e3cf86", fs: [46, 46], bold: true, y0: 84 });
const nYes = B.note(L.notes, 900, 1424, 1120, 136, 0.9, ["Informasi waktu memang membantu"], { seed: 54, fill: "#efe5cf", fs: [50, 50], bold: true, y0: 88, torn: true, col: RED });

// ───────────── result card ─────────────
const RC = B.sheet(L.papers, 2150, 230, 630, 980, { seed: 57, amp: 6, step: 12, rot: 0.6 });
const rc = RC.c;
txt("PENURUNAN RMSE", { x: 315, y: 84, "font-size": 58, fill: RED, "text-anchor": "middle", class: "rus" }, rc);
const b1 = el("g", { opacity: 0 }, rc);
txt("Berdasarkan waktu", { x: 40, y: 200, "font-size": 42, "font-weight": 700, fill: INK }, b1);
const r1 = el("rect", { x: 40, y: 228, width: 0, height: 100, fill: RED }, b1);
const v1 = txt("0,080", { x: 410, y: 300, "font-size": 62, "font-weight": 700, fill: INK, opacity: 0 }, b1);
const b2 = el("g", { opacity: 0 }, rc);
txt("Pembagian acak", { x: 40, y: 440, "font-size": 42, "font-weight": 700, fill: INK }, b2);
const r2 = el("rect", { x: 40, y: 468, width: 0, height: 100, fill: INK }, b2);
const v2 = txt("0,007", { x: 98, y: 540, "font-size": 62, "font-weight": 700, fill: INK, opacity: 0 }, b2);
const ft = el("g", { opacity: 0 }, rc);
txt("Kompleksitas setara", { x: 315, y: 690, "font-size": 46, "font-weight": 700, "text-anchor": "middle", fill: INK }, ft);
txt("Audit validasi bersarang", { x: 315, y: 772, "font-size": 46, "font-weight": 700, "text-anchor": "middle", fill: RED }, ft);
txt("Equal-Parameter Random Control", { x: 315, y: 846, "font-size": 34, "font-style": "italic", "text-anchor": "middle", fill: "#5d564e" }, ft);
const ring = el("path", { d: "M30,222 C200,206 600,210 614,276 C622,348 220,354 34,342 C-6,332 -4,238 64,220", fill: "none", stroke: RED, "stroke-width": 6, "stroke-linecap": "round", opacity: 0 }, rc);
const pRC = B.pin(L.top, 2465, 250, "deco", RED);
const nT = B.note(L.notes, 2130, 1270, 680, 190, 1.8, ["Tapi saat kesalahan", "diperiksa satu per satu…"], { seed: 58, fill: "#f7f1e1", fs: [40, 42] });

// ───────────── timeline ─────────────
B.hideAtStart(...models.map((m) => m.s.inner), ...models.map((m) => m.pin.s), MC.inner, DSH.inner, nBest.inner, ...nodes.map((n) => n.i), SK.inner, ...springs, RS.inner, nQ.inner, nYes.inner, RC.inner, pRC.s, nT.inner, ...bands.map((b) => b.g));

// Pacing: one beat per script sentence; visuals land in the first ~1.5 s of the beat, then hold for the presenter.

// 0.3  "Kami menemukan satu pola menarik."
B.camSet(0, 1000, 660, 0.9);
tl.to("#bcam", { ...B.cam(1040, 640, 0.92), duration: 8, ease: "none" }, 0);
models.forEach((m, k) => { B.slap(m.s.inner, 0.3 + k * 0.18, 1.4, k % 2 ? -4 : 4); B.pinIn(m.pin, 0.3 + k * 0.18); });

// 2.6  "Model yang bagus pada satu bagian hari belum tentu paling akurat di bagian hari yang lain."
B.slap(DSH.inner, 2.6, 1.3, 3);
bands.forEach((b, j) => tl.fromTo(b.g, { opacity: 0, y: 16 }, { opacity: 1, y: 0, duration: 0.35, ease: out }, 2.9 + j * 0.2));
B.slap(nBest.inner, 3.7, 1.5, -5);

// 8.6  "Karena itu, kami menggunakan Time-Banded Ensemble dengan Non-Negative Least Squares, atau NNLS."
B.camTo(8.5, 1250, 640, 0.8, 1.0);
tl.to(nBest.inner, { opacity: 0, y: -40, duration: 0.3 }, 8.6);
B.slap(MC.inner, 8.9, 1.4, -4);
tl.to(bandNote, { opacity: 1, duration: 0.3 }, 9.4);

// 12.5  "Sederhananya, kami mencari kombinasi bobot model yang meminimalkan kesalahan, dengan syarat bobotnya tidak negatif."
tl.to(bandNote, { opacity: 0, duration: 0.3 }, 12.4);
[0, 1, 2].forEach((j) => {
  const t = 12.5 + j * 0.35;
  ths.filter((o) => o.j === j).forEach((o, k) => B.drawThread(o.th, t + k * 0.04, 0.5));
  tl.fromTo(nodes[j].i, { opacity: 0, scale: 1.8, transformOrigin: "50% 50%" }, { opacity: 1, scale: 1, duration: 0.3, ease: "power4.out" }, t + 0.5);
});
nodes.forEach((n, j) => tl.fromTo(n.w, { opacity: 0, y: 10 }, { opacity: 1, y: 0, duration: 0.3, ease: out }, 13.8 + j * 0.12));
tl.to("#bcam", { ...B.cam(1250, 720, 0.82), duration: 5, ease: "none" }, 12.5);

// 17.8  "Bobot ini kami pelajari secara terpisah berdasarkan bagian waktu dalam sehari, lalu kami beri shrinkage agar
//        tidak terlalu mengikuti data validasi."
B.camTo(17.7, 1250, 835, 0.85, 1.0);
B.slap(SK.inner, 18.1, 1.4, 4);
springs.forEach((s, j) => { tl.set(s, { opacity: 1 }, 18.4 + j * 0.1); B.drawIn(s, 18.4 + j * 0.1, 0.35); });
nodes.forEach((n, j) => {
  tl.to(n.i, { y: 26, duration: 0.35, ease: "power2.inOut" }, 18.9 + j * 0.05);
  tl.to(n.i, { y: 0, duration: 1.0, ease: "elastic.out(1, 0.45)" }, 19.25 + j * 0.05);
});
tl.to(skCap, { opacity: 1, duration: 0.35 }, 19.3);

// 25.0  "Tetapi kami perlu memastikan satu hal: apakah peningkatannya benar-benar berasal dari informasi waktu, atau hanya
//        karena jumlah parameter bertambah?"
B.camTo(24.9, 1240, 930, 0.78, 1.0);
B.slap(nQ.inner, 25.3, 1.5, 4);

// 31.9  "Kami mengujinya dengan Equal-Parameter Random Control."
B.slap(RS.inner, 31.9, 1.3, -3);
slices.forEach((s, i) => tl.to(s, { opacity: 1, duration: 0.1 }, 32.2 + i * 0.04));

// 34.6  "Hasilnya, pembagian berdasarkan waktu memberikan perbaikan RMSE sebesar 0,080, sedangkan pembagian acak dengan
//        kompleksitas setara hanya 0,007 dalam audit validasi bersarang."
B.camTo(34.5, 1813, 820, 0.9, 1.0);
B.slap(RC.inner, 34.9, 1.35, -3); B.pinIn(pRC, 34.9);
tl.to(b1, { opacity: 1, duration: 0.25 }, 35.3); B.grow(r1, 352, 35.4, 0.7);
tl.fromTo(v1, { opacity: 0, x: -10 }, { opacity: 1, x: 0, duration: 0.3, ease: out }, 36.0);
tl.to(b2, { opacity: 1, duration: 0.25 }, 36.2); B.grow(r2, 33, 36.3, 0.4);
tl.fromTo(v2, { opacity: 0, x: -10 }, { opacity: 1, x: 0, duration: 0.3, ease: out }, 36.6);
B.fadeIn(ft, 36.9, 0.4);
tl.set(ring, { opacity: 1 }, 37.4); B.drawIn(ring, 37.4, 0.5, "power2.inOut");

// 42.4  "Artinya, informasi waktu memang membantu."
B.camTo(42.3, 1440, 900, 0.7, 1.0);
tl.to(nQ.inner, { opacity: 0, y: -30, duration: 0.3 }, 42.5);
B.slap(nYes.inner, 42.7, 1.5, -5);

// 44.8  "Sepertinya kasus ini hampir selesai. Namun ketika kami memeriksa kesalahan prediksinya satu per satu, muncul
//        petunjuk yang jauh lebih besar."
B.camTo(44.7, 1440, 810, 0.6667, 1.0);
B.slap(nT.inner, 45.1, 1.5, 5);

B.register();

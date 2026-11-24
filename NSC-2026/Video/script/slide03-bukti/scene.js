// Slide 3 — Contaminated Evidence (70 s, muted; the presenter speaks the script live).
// Real data: air_temperature in Dataset/train.csv, 6 Aug 2023 22:00 → 7 Aug 06:00 (17 readings).
// The 02:00 reading is 54.1 °C; the leave-one-out quadratic through the four neighbours gives 11.0 °C.
// Ratios 5.75 / 6.86 / 1.20 come from the report (Gambar 2, Tabel I).
const { el, txt, f1, INK, RED, NAVY, GOLD } = BOARD;
const B = BOARD.make({ duration: 70, title: "SEBAGIAN BUKTI PERLU DIPERIKSA", act: "THE CLUES" });
const { tl, L } = B;
const out = "expo.out";

// ───────────── exhibit: the temperature log ─────────────
const EX = B.sheet(L.papers, 150, 230, 1760, 1010, { seed: 11, amp: 9, step: 16, grid: "graph" });
const ex = el("g", { transform: "translate(-150 -230)" }, EX.c);
B.pin(L.papers, 200, 272, "deco", GOLD); B.pin(L.papers, 1860, 272, "deco", GOLD);
txt("Catatan sensor · Suhu udara", { x: 220, y: 330, "font-size": 50, "font-weight": 700, fill: INK }, ex);
txt("6–7 Agustus 2023, setiap 30 menit", { x: 222, y: 384, "font-size": 34, fill: "#5d564e" }, ex);

const T = [18.12, 15.6, 14.39, 13.55, 12.77, 12.5, 12.17, 11.12, 54.1, 10.91, 9.91, 10.13, 10.83, 11.66, 13.17, 17.74, 21.67];
const SP = 8, EST = 11.0067; // spike index, LOO quadratic estimate (c0 of the fit through t = −2, −1, +1, +2)
const X = (i) => 420 + i * 84;
const Y = (v) => 1110 - (v - 5) * 13.6;
const axes = el("g", {}, ex);
const axY = el("path", { d: "M330,1140 L330,440", fill: "none", stroke: INK, "stroke-width": 4, "marker-end": "url(#arr)" }, axes);
const axX = el("path", { d: "M330,1140 L1860,1140", fill: "none", stroke: INK, "stroke-width": 4, "marker-end": "url(#arr)" }, axes);
const ticks = el("g", {}, axes);
[10, 20, 30, 40, 50].forEach((v) => { el("line", { x1: 318, y1: f1(Y(v)), x2: 342, y2: f1(Y(v)), stroke: INK, "stroke-width": 3 }, ticks); el("line", { x1: 342, y1: f1(Y(v)), x2: 1840, y2: f1(Y(v)), stroke: INK, "stroke-opacity": 0.08, "stroke-width": 2 }, ticks); txt(String(v), { x: 304, y: f1(Y(v) + 13), "font-size": 36, "text-anchor": "end", fill: INK }, ticks); });
txt("°C", { x: 352, y: 470, "font-size": 36, "font-weight": 700, fill: INK }, ticks);
[["22.00", 0], ["00.00", 4], ["02.00", 8], ["04.00", 12], ["06.00", 16]].forEach(([s, i]) => txt(s, { x: X(i), y: 1190, "font-size": 34, "text-anchor": "middle", fill: "#4c463f" }, ticks));
const src = txt("Sumber: train.csv (air_temperature)", { x: 1840, y: 1218, "font-size": 28, "font-style": "italic", "text-anchor": "end", fill: "#6f685f" }, ex);

const ys = T.map(Y);
// the series is drawn as two runs plus the two legs into the 02.00 reading, so the legs can fade while it is hidden
const lineClip = el("clipPath", { id: "lineClip" }, B.defs);
const lineClipR = el("rect", { x: 300, y: 200, width: 0, height: 1100 }, lineClip);
const lines = el("g", { "clip-path": "url(#lineClip)" }, ex);
const run = (a, b) => el("polyline", { points: T.slice(a, b + 1).map((v, k) => `${X(a + k)},${f1(ys[a + k])}`).join(" "), fill: "none", stroke: INK, "stroke-width": 4, "stroke-linejoin": "round" }, lines);
run(0, SP - 1); run(SP + 1, 16);
const legs = el("polyline", { fill: "none", stroke: INK, "stroke-width": 4, "stroke-linejoin": "round" }, lines);
const setLine = (ySp) => legs.setAttribute("points", `${X(SP - 1)},${f1(ys[SP - 1])} ${X(SP)},${f1(ySp)} ${X(SP + 1)},${f1(ys[SP + 1])}`);
setLine(ys[SP]);
const dots = T.map((v, i) => el("circle", { cx: X(i), cy: f1(ys[i]), r: i === SP ? 16 : 12, fill: i === SP ? RED : NAVY, stroke: "#1a1410", "stroke-width": 2.5 }, ex));
const spikeLbl = el("g", {}, ex);
txt("54,1 °C", { x: X(SP) + 84, y: f1(ys[SP] + 4), "font-size": 52, "font-weight": 700, fill: RED }, spikeLbl);
txt("pukul 02.00, malam hari", { x: X(SP) + 86, y: f1(ys[SP] + 50), "font-size": 32, fill: "#5d564e" }, spikeLbl);
const ring = el("path", { d: `M${X(SP) - 4},${f1(ys[SP] - 52)} C${X(SP) + 60},${f1(ys[SP] - 58)} ${X(SP) + 62},${f1(ys[SP] + 50)} ${X(SP)},${f1(ys[SP] + 54)} C${X(SP) - 64},${f1(ys[SP] + 56)} ${X(SP) - 60},${f1(ys[SP] - 44)} ${X(SP) + 10},${f1(ys[SP] - 56)}`, fill: "none", stroke: RED, "stroke-width": 7, "stroke-linecap": "round" }, ex);

// LOO pieces (in the lens)
const nbr = [SP - 2, SP - 1, SP + 1, SP + 2];
const nbrRings = nbr.map((i) => el("circle", { cx: X(i), cy: f1(ys[i]), r: 26, fill: "none", stroke: GOLD, "stroke-width": 6, opacity: 0 }, ex));
const nbrLbl = txt("4 titik tetangga", { x: X(SP), y: 1090, "font-size": 38, "font-weight": 700, "text-anchor": "middle", fill: INK, opacity: 0 }, ex);
const qPts = []; for (let t = -2.4; t <= 2.401; t += 0.1) qPts.push(`${f1(X(SP) + t * 84)},${f1(Y(0.0083333 * t * t - 0.473 * t + EST))}`);
const quad = el("path", { d: "M" + qPts.join(" L"), fill: "none", stroke: RED, "stroke-width": 5, "stroke-dasharray": "12 8", "stroke-linecap": "round" }, ex);
const estDot = el("circle", { cx: X(SP), cy: f1(Y(EST)), r: 14, fill: "#efe5cf", stroke: RED, "stroke-width": 5, opacity: 0 }, ex);
const estLbl = el("g", { opacity: 0 }, ex);
txt("Perkiraan", { x: X(SP) + 40, y: f1(Y(EST) - 112), "font-size": 38, "font-weight": 700, fill: RED }, estLbl);
txt("11,0 °C", { x: X(SP) + 40, y: f1(Y(EST) - 66), "font-size": 38, "font-weight": 700, fill: RED }, estLbl);
const resid = el("path", { d: `M${X(SP)},${f1(Y(EST) - 16)} L${X(SP)},${f1(ys[SP] + 18)}`, fill: "none", stroke: RED, "stroke-width": 5, "stroke-dasharray": "14 9" }, ex);
const resLbl = el("g", { opacity: 0 }, ex);
txt("Residual", { x: X(SP) - 26, y: 640, "font-size": 46, "font-weight": 700, "text-anchor": "end", fill: RED }, resLbl);
txt("43,1 °C", { x: X(SP) - 26, y: 694, "font-size": 46, "font-weight": 700, "text-anchor": "end", fill: RED }, resLbl);
// the paper tab that hides the point for a moment
const patch = B.sheet(ex, X(SP) - 50, ys[SP] - 46, 100, 92, { seed: 7, amp: 5, step: 10, rot: -6, fill: "#e3cf86", texOp: 0.6, blend: true });
txt("?", { x: 50, y: 66, "font-size": 60, "font-weight": 700, fill: RED, "text-anchor": "middle" }, patch.c);

// Hampel pieces
const hBand = el("rect", { x: X(SP - 3) - 30, y: f1(Y(11.12) - 46), width: 6 * 84 + 60, height: 92, fill: RED, opacity: 0, rx: 10 }, ex);
const hBandLbl = txt("batas Hampel di sekitar median lokal", { x: X(SP - 3) - 30, y: f1(Y(11.12) + 88), "font-size": 32, "font-weight": 700, fill: RED, opacity: 0 }, ex);
const ghost = el("circle", { cx: X(SP), cy: f1(ys[SP]), r: 16, fill: "none", stroke: RED, "stroke-width": 4, "stroke-dasharray": "6 6", opacity: 0 }, ex);
const flat = el("path", { d: `M${X(0)},${f1(Y(14.2))} L${X(16)},${f1(Y(14.2))}`, fill: "none", stroke: "#8f887d", "stroke-width": 16, "stroke-linecap": "round", opacity: 0 }, ex);
const strike = el("g", { opacity: 0 }, ex);
const st1 = el("path", { d: `M${X(12) - 90},${f1(Y(14.2) - 110)} L${X(12) + 90},${f1(Y(14.2) + 60)}`, fill: "none", stroke: RED, "stroke-width": 12, "stroke-linecap": "round" }, strike);
const st2 = el("path", { d: `M${X(12) + 90},${f1(Y(14.2) - 110)} L${X(12) - 90},${f1(Y(14.2) + 60)}`, fill: "none", stroke: RED, "stroke-width": 12, "stroke-linecap": "round" }, strike);
const stampOK = B.stamp(ex, 1450, 560, "DIPERIKSA", { fs: 78, rot: -8 });

// ───────────── right column: hypotheses, then the ratio card ─────────────
const nA = B.note(L.notes, 1990, 250, 780, 160, -1.6, ["Lingkungan memang", "berubah ekstrem?"], { seed: 31, fill: "#efe5cf", fs: [42, 46] });
const nB = B.note(L.notes, 2000, 450, 780, 160, 1.4, ["Atau sensornya", "bermasalah?"], { seed: 32, fill: "#e3cf86", fs: [42, 46] });
const nC = B.note(L.notes, 1985, 690, 780, 200, -1.0, ["Jangan langsung dibuang:", "bisa jadi petunjuk"], { seed: 33, fill: "#f7f1e1", fs: [40, 48], torn: true });
const thA = B.thread(L.threads, `M${X(SP) + 6},${f1(ys[SP] - 56)} C1400,250 1900,250 2380,262`, RED, 4);
const thB = B.thread(L.threads, `M${X(SP) + 6},${f1(ys[SP] - 56)} C1450,300 1950,380 2390,462`, RED, 4);

const RC = B.sheet(L.top, 1975, 240, 820, 1010, { seed: 57, amp: 6, step: 12, rot: 0.6 });
const rc = RC.c;
txt("RASIO RESIDUAL", { x: 410, y: 92, "font-size": 64, fill: RED, "text-anchor": "middle", class: "rus" }, rc);
const frac = el("g", {}, rc);
txt("SD residual", { x: 410, y: 192, "font-size": 44, "font-weight": 700, "text-anchor": "middle", fill: INK }, frac);
el("line", { x1: 150, y1: 214, x2: 670, y2: 214, stroke: INK, "stroke-width": 4 }, frac);
txt("skala robust (MAD)", { x: 410, y: 270, "font-size": 44, "font-weight": 700, "text-anchor": "middle", fill: INK }, frac);
const BARS = [["Suhu", 5.75, "5,75", RED], ["Tekanan", 6.86, "6,86", RED], ["Kelembapan", 1.2, "1,20", INK]];
const bars = BARS.map(([n, v, s, c], k) => {
  const y = 360 + k * 130;
  const g = el("g", { opacity: 0 }, rc);
  txt(n, { x: 290, y: y + 48, "font-size": 38, "text-anchor": "end", fill: INK }, g);
  const r = el("rect", { x: 310, y, width: 0, height: 68, fill: c }, g);
  const vt = txt(s, { x: 322 + v * 52, y: y + 52, "font-size": 54, "font-weight": 700, fill: INK, opacity: 0 }, g);
  return { g, r, w: v * 52, vt };
});
const verdict = el("g", { opacity: 0 }, rc);
txt("Lonjakan lebih dominan", { x: 410, y: 816, "font-size": 50, "font-weight": 700, "text-anchor": "middle", fill: RED }, verdict);
txt("pada sensor masukan", { x: 410, y: 876, "font-size": 50, "font-weight": 700, "text-anchor": "middle", fill: RED }, verdict);
const rcPin = B.pin(L.top, 2385, 262, "deco", RED);

// ───────────── bottom: the method chain ─────────────
const chain = [
  [150, 830, "Leave-One-Out", "Quadratic Interpolation"],
  [1080, 700, "Skala robust", "MAD"],
  [1880, 860, "Hampel Filter", "selektif"],
].map(([x, w, a, b], k) => {
  const c = B.card(L.papers, x, 1290, w, 220, [0.8, -0.6, 0.9][k], 80 + k);
  txt(a, { x: 34, y: 108, "font-size": 46, fill: "#5d564e" }, c.c);
  txt(b, { x: 34, y: 176, "font-size": 56, "font-weight": 700, fill: INK }, c.c);
  return { c, pin: B.pin(L.top, x + w / 2, 1306, "deco", NAVY) };
});
const arrows = [[985, 1070], [1785, 1870]].map(([a, b]) => el("path", { d: `M${a},1400 L${b},1400`, fill: "none", stroke: RED, "stroke-width": 9, "stroke-linecap": "round", "marker-end": "url(#arrR)" }, L.top));

// ───────────── timeline ─────────────
B.hideAtStart(spikeLbl, ring, quad, resid, ...chain.map((c) => c.c.inner), ...chain.map((c) => c.pin.s), ...arrows, RC.inner, rcPin.s, nA.inner, nB.inner, nC.inner, thA.g, thB.g, patch.g, src);
dots.forEach((d) => tl.set(d, { attr: { r: 0 } }, 0));
B.camSet(0, 1010, 760, 1.0);
tl.to("#bcam", { ...B.cam(1000, 740, 1.03), duration: 5, ease: "none" }, 0);

// Pacing: one beat per script sentence. Each beat reveals its visuals in the first ~1.5 s,
// then holds still so the presenter can talk over it. Beat starts follow the sentence lengths.

// 0.3  "Ketika kami memeriksa catatan sensor, beberapa angka terlihat tidak masuk akal."
B.drawIn(axY, 0.2, 0.5, "power2.inOut"); B.drawIn(axX, 0.2, 0.6, "power2.inOut");
tl.fromTo(ticks, { opacity: 0 }, { opacity: 1, duration: 0.4 }, 0.5);
tl.to(lineClipR, { attr: { width: 1500 }, duration: 1.6, ease: "none" }, 0.7);
dots.forEach((d, i) => tl.to(d, { attr: { r: i === SP ? 16 : 12 }, duration: 0.2, ease: "back.out(3)" }, 0.75 + i * 0.09));
tl.fromTo(src, { opacity: 0 }, { opacity: 1, duration: 0.4 }, 2.0);

// 5.5  "Contohnya, ada pembacaan suhu yang melonjak jauh dari kondisi normal."
B.camTo(5.4, 1065, 730, 1.12, 1.0);
tl.to(dots[SP], { attr: { r: 22 }, duration: 0.2, yoyo: true, repeat: 3, ease: "sine.inOut" }, 5.8);
tl.set(ring, { opacity: 1 }, 5.9); B.drawIn(ring, 5.9, 0.5, "power2.inOut");
B.fadeIn(spikeLbl, 6.2, 0.4);
tl.to("#bcam", { ...B.cam(1052, 722, 1.15), duration: 3.4, ease: "none" }, 6.4);

// 9.9  "Ada dua kemungkinan: kondisi lingkungan memang berubah ekstrem, atau sensornya bermasalah."
B.camTo(9.8, 1966, 700, 1.05, 1.0);
B.drawThread(thA, 10.3, 0.45); B.slap(nA.inner, 10.6, 1.5, 5);
B.drawThread(thB, 10.8, 0.45); B.slap(nB.inner, 11.1, 1.5, -5);

// 14.6  "Kami tidak bisa langsung membuang semua nilai yang terlihat aneh. Bisa jadi, justru di situlah petunjuknya."
B.slap(nC.inner, 14.7, 1.5, 4);
tl.to("#bcam", { ...B.cam(1966, 710, 1.07), duration: 6.2, ease: "none" }, 14.8);

// 21.4  "Karena itu, kami melakukan Leave-One-Out Quadratic Interpolation."
B.camTo(21.3, 1300, 1060, 0.74, 1.0);
B.slap(chain[0].c.inner, 21.9, 1.45, 4); B.pinIn(chain[0].pin, 21.9);

// 25.0  "Sederhananya, satu titik kami sembunyikan sementara, kemudian kami perkirakan menggunakan pola empat titik
//        di sekitarnya melalui interpolasi kuadratik."  — the whole estimate is on screen by ~29.5
const lens = B.lens(450);
B.camTo(24.9, X(SP), 760, 1.1, 0.9);
tl.to([thA.g, thB.g], { opacity: 0, duration: 0.4 }, 24.9);
lens.in(25.0);
lens.hold(25.9, 11.0);
tl.to([ring, spikeLbl], { opacity: 0, duration: 0.3 }, 25.3);
tl.set(patch.g, { opacity: 1 }, 25.8);
tl.to(legs, { opacity: 0.12, duration: 0.3 }, 25.8);
tl.fromTo(patch.inner, { opacity: 0, scale: 1.8, rotation: -14, transformOrigin: "50% 50%" }, { opacity: 1, scale: 1, duration: 0.3, ease: out }, 25.8);
nbrRings.forEach((r, k) => { tl.to(r, { opacity: 1, duration: 0.2 }, 26.6 + k * 0.12); tl.fromTo(r, { attr: { r: 40 } }, { attr: { r: 26 }, duration: 0.35, ease: out }, 26.6 + k * 0.12); });
tl.to(nbrLbl, { opacity: 1, duration: 0.3 }, 26.9);
tl.set(quad, { opacity: 1 }, 27.6);
B.drawIn(quad, 27.6, 0.8, "power2.inOut");
tl.fromTo(estDot, { opacity: 0, attr: { r: 30 } }, { opacity: 1, attr: { r: 14 }, duration: 0.3, ease: out }, 28.4);
B.fadeIn(estLbl, 28.6);

// 33.0  "Selisih hasil perkiraan dan nilai aslinya disebut residual."
tl.to(patch.inner, { x: 160, y: -120, rotation: 30, opacity: 0, duration: 0.45, ease: "power2.in" }, 33.0);
tl.set(resid, { opacity: 1 }, 33.4);
B.drawIn(resid, 33.4, 0.6, "power2.inOut");
B.fadeIn(resLbl, 33.8);
lens.out(36.7);
tl.to(legs, { opacity: 1, duration: 0.4 }, 36.9);
tl.to([...nbrRings, nbrLbl, quad, estLbl, resLbl], { opacity: 0, duration: 0.4 }, 36.9);
tl.to(resid, { opacity: 0.45, duration: 0.4 }, 36.9);

// 37.0  "Untuk mendeteksi lonjakan ekstrem, kami membandingkan standar deviasi residual dengan skala robust berbasis MAD."
B.camTo(36.9, 1500, 830, 0.7, 1.1);
tl.to([nA.inner, nB.inner, nC.inner], { opacity: 0, duration: 0.3 }, 37.3);
B.slap(RC.inner, 37.6, 1.4, -4); B.pinIn(rcPin, 37.6);
B.slap(chain[1].c.inner, 38.0, 1.45, -4); B.pinIn(chain[1].pin, 38.0);
B.drawIn(arrows[0], 38.3, 0.3, "power2.out"); tl.set(arrows[0], { opacity: 1 }, 38.3);
tl.fromTo(frac, { opacity: 0 }, { opacity: 1, duration: 0.4 }, 38.5);

// 43.8  "Hasilnya, rasio suhu mencapai 5,75, tekanan 6,86, sementara kelembapan hanya 1,20."
B.camTo(43.7, 2400, 745, 1.12, 1.0);
bars.forEach((b, k) => {
  const t = 44.3 + k * 0.55;
  tl.to(b.g, { opacity: 1, duration: 0.2 }, t);
  B.grow(b.r, b.w, t + 0.05, 0.6);
  tl.fromTo(b.vt, { opacity: 0, x: -10 }, { opacity: 1, x: 0, duration: 0.3, ease: out }, t + 0.45);
});

// 49.0  "Artinya, gangguan ekstrem lebih dominan pada sensor masukan."
B.fadeIn(verdict, 49.0, 0.45);
tl.to([bars[0].r, bars[1].r], { attr: { height: 80, y: "-=6" }, duration: 0.3, yoyo: true, repeat: 1, ease: "power2.inOut" }, 49.1);

// 53.0  "Karena itu, kami menggunakan Hampel Filter secara selektif untuk menangani lonjakan sensor, bukan meratakan seluruh data."
B.camTo(52.9, 1440, 870, 0.72, 0.9);
B.slap(chain[2].c.inner, 53.3, 1.45, 4); B.pinIn(chain[2].pin, 53.3);
B.drawIn(arrows[1], 53.5, 0.3, "power2.out"); tl.set(arrows[1], { opacity: 1 }, 53.5);
B.camTo(54.1, 1030, 735, 1.08, 0.9);
tl.to(hBand, { opacity: 0.16, duration: 0.4 }, 54.6);
tl.to(hBandLbl, { opacity: 1, duration: 0.3 }, 54.7);
tl.to(resid, { opacity: 0, duration: 0.3 }, 54.8);
tl.to(ghost, { opacity: 0.9, duration: 0.2 }, 55.0);
const mv = { y: ys[SP] };
tl.to(mv, { y: Y((11.12 + 10.91) / 2), duration: 0.9, ease: "power2.inOut", onUpdate: () => { dots[SP].setAttribute("cy", f1(mv.y)); setLine(mv.y); } }, 55.0);
tl.to(dots[SP], { attr: { r: 13 }, duration: 0.5 }, 55.3);
tl.to(estDot, { opacity: 0, duration: 0.3 }, 55.6);
// not a flattening of the whole series
tl.set(flat, { opacity: 0.75 }, 56.2);
B.drawIn(flat, 56.2, 0.4, "power2.out");
tl.set(strike, { opacity: 1 }, 56.7);
B.drawIn(st1, 56.7, 0.16, "power2.in"); B.drawIn(st2, 56.9, 0.16, "power2.in");
tl.to(ghost, { opacity: 0.35, duration: 0.5 }, 58.4);
tl.to([flat, strike], { opacity: 0, duration: 0.4 }, 59.2);

// 59.8  "Barang bukti pertama telah diperiksa. Tapi ternyata ada informasi lain yang selama ini tersembunyi di dalam catatan."
B.camTo(59.6, 1440, 810, 0.6667, 1.2);
tl.to(hBandLbl, { opacity: 0, duration: 0.4 }, 59.6);
B.stampIn(stampOK, 60.6);
tl.to("#bcam", { ...B.cam(1440, 810, 0.672), duration: 3, ease: "sine.inOut" }, 61.2);

B.register();

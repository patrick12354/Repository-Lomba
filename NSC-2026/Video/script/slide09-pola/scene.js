// Slide 9 — The Pattern Nobody Noticed (55 s, muted; the presenter speaks the script live).
// The residual series is an illustration of the pattern (labelled on screen); ≈0,93 lag-1 is the report's value.
// The bottom strip hands over to slide 10: level pins, 30-minute arcs, the 2-hour link, two prediction cards.
const { el, txt, f1, INK, RED, NAVY, GOLD } = BOARD;
const B = BOARD.make({ duration: 55, title: "KESALAHAN MASIH MEMILIKI POLA WAKTU", act: "THE BREAKTHROUGH", titleSize: 56 });
const { tl, L } = B;
const out = "expo.out";

// ───────────── the RMSE score, not enough on its own ─────────────
const SC = B.sheet(L.top, 900, 420, 820, 330, { seed: 9, amp: 6, step: 12, rot: -2 });
txt("SKOR RMSE", { x: 410, y: 120, "font-size": 80, fill: INK, "text-anchor": "middle", class: "rus" }, SC.c);
txt("prediksi gabungan", { x: 410, y: 190, "font-size": 44, "text-anchor": "middle", fill: "#5d564e" }, SC.c);
const scQ = txt("cukup?", { x: 410, y: 280, "font-size": 64, "font-weight": 700, "font-style": "italic", "text-anchor": "middle", fill: RED, opacity: 0 }, SC.c);

// ───────────── residual exhibit ─────────────
const EX = B.sheet(L.papers, 150, 230, 1720, 880, { seed: 11, amp: 9, step: 16, grid: "graph" });
const ex = el("g", { transform: "translate(-150 -230)" }, EX.c);
const exPins = [B.pin(L.papers, 186, 262, "deco", GOLD), B.pin(L.papers, 1834, 262, "deco", GOLD)];
txt("RESIDUAL AUTOCORRELATION ANALYSIS", { x: 236, y: 334, "font-size": 54, fill: RED, class: "rus" }, ex);
txt("Residual = prediksi − aktual", { x: 222, y: 392, "font-size": 40, fill: INK }, ex);
const RV = [1.5, 1.25, 0.85, 0.15, -0.75, -1.2, -1.55, -1.15, -0.45, 0.35, 0.85, 1.15, 0.95, 1.4];
const X = (i) => 330 + i * 106, Z = 630, Y = (v) => Z - v * 120;
const zero = el("path", { d: `M260,${Z} L1820,${Z}`, fill: "none", stroke: INK, "stroke-width": 3, "stroke-dasharray": "12 10" }, ex);
const zl = txt("0", { x: 236, y: Z + 14, "font-size": 40, "text-anchor": "end", fill: INK }, ex);
const axX = el("path", { d: "M260,1010 L1830,1010", fill: "none", stroke: INK, "stroke-width": 4, "marker-end": "url(#arr)" }, ex);
const wl = txt("Waktu", { x: 1820, y: 1062, "font-size": 38, "text-anchor": "end", fill: INK }, ex);
const illus = txt("Ilustrasi pola residual, bukan deret pengukuran", { x: 262, y: 1070, "font-size": 30, "font-style": "italic", fill: "#6f685f" }, ex);
const lineClip = el("clipPath", { id: "resClip" }, B.defs);
const lineClipR = el("rect", { x: 300, y: 300, width: 0, height: 800 }, lineClip);
const rline = el("polyline", { points: RV.map((v, i) => `${X(i)},${f1(Y(v))}`).join(" "), fill: "none", stroke: INK, "stroke-width": 4, "stroke-linejoin": "round", "clip-path": "url(#resClip)" }, ex);
const NEG = [4, 5, 6, 7, 8];
const dots = RV.map((v, i) => el("circle", { cx: X(i), cy: f1(Y(v)), r: 0, fill: "#7a7268", stroke: "#1a1410", "stroke-width": 2.5 }, ex));
const runBr = el("path", { d: `M${X(4) - 30},${f1(Y(-1.55) + 60)} Q${X(6)},${f1(Y(-1.55) + 110)} ${X(8) + 30},${f1(Y(-1.55) + 60)}`, fill: "none", stroke: RED, "stroke-width": 6, "stroke-linecap": "round" }, ex);
const runLbl = txt("Meleset terlalu rendah, berturut-turut", { x: X(6), y: f1(Y(-1.55) + 160), "font-size": 46, "font-weight": 700, "text-anchor": "middle", fill: RED, opacity: 0 }, ex);
// lag-1: each residual next to the one right after it
const lagArcs = RV.slice(0, -1).map((v, i) => el("path", { d: `M${X(i) + 14},${f1(Y(v) - 22)} Q${f1(X(i) + 53)},${f1(Math.min(Y(v), Y(RV[i + 1])) - 70)} ${X(i + 1) - 14},${f1(Y(RV[i + 1]) - 22)}`, fill: "none", stroke: GOLD, "stroke-width": 4, "marker-end": "url(#arr)", opacity: 0 }, ex));
const lagLbl = txt("lag-1: tiap titik vs titik sesudahnya", { x: 1820, y: 392, "text-anchor": "end", "font-size": 36, "font-weight": 700, fill: "#8a6a1e", opacity: 0 }, ex);

// ───────────── the number ─────────────
const AC = B.sheet(L.papers, 1960, 230, 820, 880, { seed: 57, amp: 6, step: 12, rot: 0.6 });
const ac = AC.c;
txt("Autokorelasi residual", { x: 410, y: 96, "font-size": 50, "font-weight": 700, "text-anchor": "middle", fill: INK }, ac);
const num = el("g", { opacity: 0 }, ac);
txt("≈0,93", { x: 410, y: 340, "font-size": 200, "font-weight": 700, "text-anchor": "middle", fill: RED }, num);
const lag = txt("lag-1", { x: 410, y: 436, "font-size": 70, "font-weight": 700, "text-anchor": "middle", fill: INK, opacity: 0 }, ac);
const gal = txt("Galat model level", { x: 410, y: 540, "font-size": 50, "font-weight": 700, "text-anchor": "middle", fill: INK, opacity: 0 }, ac);
const struct = el("g", { opacity: 0 }, ac);
el("line", { x1: 120, y1: 620, x2: 700, y2: 620, stroke: INK, "stroke-opacity": 0.3, "stroke-width": 2 }, struct);
txt("Kesalahan menyimpan", { x: 410, y: 708, "font-size": 52, "font-weight": 700, "text-anchor": "middle", fill: RED }, struct);
txt("struktur waktu", { x: 410, y: 772, "font-size": 52, "font-weight": 700, "text-anchor": "middle", fill: RED }, struct);
const pAC = B.pin(L.top, 2370, 250, "deco", RED);

// ───────────── bottom: from values to changes ─────────────
const ST = B.sheet(L.papers, 150, 1170, 1500, 390, { seed: 33, amp: 6, step: 14, rot: -0.3 });
txt("DARI NILAI KE PERUBAHAN", { x: 40, y: 72, "font-size": 56, fill: RED, class: "rus" }, ST.c);
const XS = [330, 600, 870, 1140, 1410], PY = 1420;
const pins = XS.map((x) => B.pin(L.top, x, PY, "ring"));
const lvlLbl = txt("Level: nilai pada setiap waktu", { x: 1040, y: 1240, "font-size": 36, "font-weight": 700, fill: INK, opacity: 0 }, L.top);
const arcs = XS.slice(0, -1).map((x, i) => el("path", { d: `M${x + 6},${PY - 30} C${x + 60},${PY - 130} ${XS[i + 1] - 60},${PY - 130} ${XS[i + 1] - 6},${PY - 30}`, fill: "none", stroke: "#6c665e", "stroke-width": 5, "stroke-dasharray": "12 9", "stroke-linecap": "round" }, L.top));
const sag = el("path", { d: `M${XS[0]},${PY + 28} C${XS[0] + 200},${PY + 150} ${XS[4] - 200},${PY + 150} ${XS[4]},${PY + 28}`, fill: "none", stroke: "#6c665e", "stroke-width": 5, "stroke-dasharray": "14 10", "stroke-linecap": "round" }, L.top);
const l30 = txt("30 menit", { x: 465, y: 1300, "font-size": 42, "font-weight": 700, "text-anchor": "middle", fill: RED, opacity: 0 }, L.top);
const l2j = txt("2 jam", { x: 870, y: 1508, "font-size": 42, "font-weight": 700, "text-anchor": "middle", fill: RED, opacity: 0 }, L.top);

function indexCard(x, y, rot, title, sub, seed) {
  const c = B.card(L.papers, x, y, 660, 180, rot, seed);
  txt(title, { x: 30, y: 98, "font-size": 48, "font-weight": 700, fill: INK }, c.c);
  txt(sub, { x: 30, y: 154, "font-size": 34, fill: "#5d564e" }, c.c);
  return c;
}
const cL = indexCard(1730, 1170, 1.0, "Level Prediction", "Nilai pada setiap waktu", 81);
const cI = indexCard(1730, 1380, -1.0, "Increment Prediction", "Perubahan 30 menit & 2 jam", 82);
const pcL = B.pin(L.top, 2060, 1186, "deco", NAVY), pcI = B.pin(L.top, 2060, 1396, "deco", NAVY);
const fromL = B.thread(L.threads, `M1650,1300 C1690,1300 1690,1260 1735,1260`, "#3a2f28", 4);
const fromI = B.thread(L.threads, `M1650,1300 C1690,1300 1690,1470 1735,1470`, "#3a2f28", 4);
const qBack = B.sheet(L.papers, 2405, 1262, 420, 156, { seed: 91, amp: 5, step: 12, rot: -3, fill: "#efe5cf" });
const qStamp = B.stamp(L.top, 2615, 1342, "BELUM TENTU COCOK", { fs: 46, rot: -6, w: 380 });
const thQ1 = B.thread(L.threads, "M2390,1260 C2400,1260 2400,1300 2412,1300", RED, 4);
const thQ2 = B.thread(L.threads, "M2390,1470 C2400,1470 2400,1384 2412,1384", RED, 4);

// ───────────── timeline ─────────────
B.hideAtStart(...exPins.map((p) => p.s), SC.inner, EX.inner, AC.inner, pAC.s, ST.inner, ...pins.map((p) => p.s), cL.inner, cI.inner, pcL.s, pcI.s, fromL.g, fromI.g, thQ1.g, thQ2.g, qBack.inner, ...arcs, sag, runBr);

// Pacing: one beat per script sentence; visuals land in the first ~1.5 s of the beat, then hold for the presenter.

// 0.3  "Setelah mendapatkan prediksi gabungan, kami tidak langsung puas dengan skor RMSE."
B.camSet(0, 1300, 600, 1.0);
B.slap(SC.inner, 0.3, 1.4, -5);
tl.fromTo(scQ, { opacity: 0, x: -14 }, { opacity: 1, x: 0, duration: 0.35, ease: out }, 0.9);
tl.to(SC.inner, { x: 1300, y: -260, rotation: 14, opacity: 0, duration: 0.6, ease: "power2.in" }, 4.4);

// 5.0  "Kami memeriksa pola residualnya melalui Residual Autocorrelation Analysis."
B.camTo(4.8, 1010, 700, 1.0, 1.0);
B.slap(EX.inner, 5.1, 1.2, 2); exPins.forEach((p) => B.pinIn(p, 5.3));
B.drawIn(axX, 5.5, 0.5, "power2.inOut");
B.drawIn(zero, 5.6, 0.5, "power2.inOut");

// 8.6  "Dan hasilnya sangat menarik."
RV.forEach((v, i) => tl.to(dots[i], { attr: { r: 15 }, duration: 0.18, ease: "back.out(3)" }, 8.6 + i * 0.09));
tl.to(lineClipR, { attr: { width: 1500 }, duration: 0.09 * RV.length, ease: "none" }, 8.6);

// 10.7  "Ketika satu titik diprediksi terlalu rendah, titik-titik di sekitarnya cenderung ikut diprediksi terlalu rendah."
B.camTo(10.5, 1010, 760, 1.1, 0.9);
NEG.forEach((i, k) => tl.to(dots[i], { attr: { fill: RED, r: 18 }, duration: 0.2 }, 10.8 + k * 0.1));
tl.set(runBr, { opacity: 1 }, 11.3); B.drawIn(runBr, 11.3, 0.4, "power2.inOut");
tl.fromTo(runLbl, { opacity: 0, y: 12 }, { opacity: 1, y: 0, duration: 0.35, ease: out }, 11.5);
lagArcs.forEach((a, i) => { tl.set(a, { opacity: NEG.includes(i) && NEG.includes(i + 1) ? 1 : 0.55 }, 11.9 + i * 0.05); B.drawIn(a, 11.9 + i * 0.05, 0.25); });
tl.to(lagLbl, { opacity: 1, duration: 0.3 }, 12.2);

// 16.5  "Autokorelasi residual pada lag pertama mencapai sekitar 0,93."
B.camTo(16.3, 1460, 700, 0.72, 1.0);
B.slap(AC.inner, 16.6, 1.35, -3); B.pinIn(pAC, 16.6);
tl.fromTo(num, { opacity: 0, scale: 1.3, transformOrigin: "50% 50%" }, { opacity: 1, scale: 1, duration: 0.4, ease: "power3.out" }, 17.0);
tl.fromTo(lag, { opacity: 0, y: 12 }, { opacity: 1, y: 0, duration: 0.3, ease: out }, 17.3);
tl.fromTo(gal, { opacity: 0, y: 12 }, { opacity: 1, y: 0, duration: 0.3, ease: out }, 17.5);

// 20.0  "Ini menunjukkan bahwa kesalahan model masih memiliki struktur waktu yang kuat."
B.fadeIn(struct, 20.0, 0.45);
tl.to("#bcam", { ...B.cam(1460, 700, 0.73), duration: 4.4, ease: "sine.inOut" }, 20.0);

// 24.7  "Dari sini, muncul hipotesis baru."
B.camTo(24.5, 960, 1300, 1.0, 1.0);
B.slap(ST.inner, 24.9, 1.15, 1.5);

// 27.2  "Selama ini, model kami berfokus memprediksi berapa nilai kelembapan pada setiap titik."
pins.forEach((p, k) => B.pinIn(p, 27.2 + k * 0.15));
tl.fromTo(lvlLbl, { opacity: 0, x: -14 }, { opacity: 1, x: 0, duration: 0.35, ease: out }, 27.8);

// 32.2  "Tetapi bagaimana dengan seberapa besar kelembapan berubah di antara dua titik waktu?"
arcs.forEach((a, k) => { tl.set(a, { opacity: 1 }, 32.2 + k * 0.15); B.drawIn(a, 32.2 + k * 0.15, 0.4); });
tl.to("#bcam", { ...B.cam(960, 1310, 1.02), duration: 11, ease: "none" }, 32.2);

// 37.3  "Untuk mengujinya, kami membangun Increment Prediction Model, yang secara khusus mempelajari perubahan kelembapan
//        dalam interval 30 menit dan dua jam."
tl.fromTo(l30, { opacity: 0, y: 12 }, { opacity: 1, y: 0, duration: 0.3, ease: out }, 37.3);
tl.set(sag, { opacity: 1 }, 37.6); B.drawIn(sag, 37.6, 0.6, "power2.inOut");
tl.fromTo(l2j, { opacity: 0, y: 12 }, { opacity: 1, y: 0, duration: 0.3, ease: out }, 38.1);

// 44.1  "Sekarang kami memiliki dua jawaban: prediksi nilainya, dan prediksi perubahannya."
B.camTo(43.9, 1440, 810, 0.6667, 1.0);
B.drawThread(fromL, 44.3, 0.3); B.slap(cL.inner, 44.4, 1.45, 4); B.pinIn(pcL, 44.4);
B.drawThread(fromI, 44.7, 0.3); B.slap(cI.inner, 44.8, 1.45, -4); B.pinIn(pcI, 44.8);

// 48.4  "Masalahnya, kedua jawaban tersebut belum tentu saling cocok."
B.drawThread(thQ1, 48.4, 0.3); B.drawThread(thQ2, 48.45, 0.3);
B.slap(qBack.inner, 48.6, 1.3, 3);
B.stampIn(qStamp, 48.9);
tl.to("#bcam", { ...B.cam(1440, 810, 0.672), duration: 3, ease: "sine.inOut" }, 49.2);

B.register();

// Slide 4 — The Hidden Clue (60 s, muted; the presenter speaks the script live).
// The seven daily index columns are the real names in Dataset/*.csv. The two Tmin curves are rebuilt from the
// daily indices of train+test (assets/tmin.js); 0,047 °C is the report's SD of their difference.
const { el, txt, f1, INK, RED, NAVY, GOLD } = BOARD;
const B = BOARD.make({ duration: 60, title: "CATATAN HARIAN MENYIMPAN PETUNJUK", act: "THE CLUES" });
const { tl, L } = B;
const out = "expo.out";

// ───────────── the daily record: seven agronomic indices ─────────────
const DS = B.sheet(L.papers, 130, 230, 800, 960, { seed: 13, amp: 7, step: 14, rot: -0.6, fill: "#f4ecd9" });
for (let y = 230; y < 940; y += 96) el("line", { x1: 4, y1: y + 22, x2: 796, y2: y + 22, stroke: "#4a76a8", "stroke-opacity": 0.2, "stroke-width": 2 }, DS.c);
el("line", { x1: 96, y1: 6, x2: 96, y2: 954, stroke: "#c45a55", "stroke-opacity": 0.5, "stroke-width": 2.5 }, DS.c);
txt("7", { x: 128, y: 196, "font-size": 190, fill: RED, class: "rus" }, DS.c);
txt("indeks agronomi", { x: 250, y: 112, "font-size": 46, "font-weight": 700, fill: INK }, DS.c);
txt("harian", { x: 250, y: 168, "font-size": 46, "font-weight": 700, fill: INK }, DS.c);
const RY = (k) => 290 + k * 92;
const NAMES = ["gdd", "standard_day_degree", "daily_mean_temperature", "daily_max_above_Tbase", "daily_max", "daily_max_reduction", "ontario_units"];
const rows = NAMES.map((n, k) => {
  const g = el("g", {}, DS.c);
  txt(String(k + 1), { x: 58, y: RY(k), "font-size": 34, "font-weight": 700, "text-anchor": "middle", fill: "#8b857c" }, g);
  const t = txt(n, { x: 124, y: RY(k), "font-size": 38, fill: INK }, g);
  return { g, t };
});
const KEY = [2, 4, 6];
const uls = KEY.map((k) => el("path", { d: `M120,${RY(k) + 14} C300,${RY(k) + 8} 520,${RY(k) + 18} ${[600, 330, 400][KEY.indexOf(k)]},${RY(k) + 12}`, fill: "none", stroke: RED, "stroke-width": 6, "stroke-linecap": "round" }, DS.c));
const qm = KEY.map((k, j) => txt("rumus?", { x: [660, 370, 440][j], y: RY(k) + 2, "font-size": 34, "font-weight": 700, "font-style": "italic", fill: RED, opacity: 0 }, DS.c));
B.pin(L.papers, 530, 250, "deco", NAVY);
const rowY = (k) => 230 + RY(k) - 12; // board y of a row (sheet is barely rotated)

// ───────────── method label + the two paths ─────────────
const ML = B.sheet(L.papers, 1000, 216, 920, 104, { seed: 19, amp: 5, step: 12, rot: -0.8, fill: "#efe5cf" });
txt("ALGEBRAIC INVERSE RECONSTRUCTION", { x: 460, y: 70, "font-size": 50, fill: RED, "text-anchor": "middle", class: "rus" }, ML.c);
function pathCard(y, rot, seed, tag, name, formula, fsz) {
  const c = B.card(L.papers, 990, y, 940, 330, rot, seed);
  txt(tag, { x: 34, y: 94, "font-size": 56, fill: RED, class: "rus" }, c.c);
  txt(name, { x: 34, y: 152, "font-size": 44, "font-weight": 700, fill: INK }, c.c);
  const f = txt(formula, { x: 34, y: 262, "font-size": fsz, fill: INK }, c.c);
  return { c, f };
}
const J1 = pathCard(352, 0.7, 41, "JALUR 1", "Rerata dan maksimum", "Tmin = 2 × Tmean − Tmax", 58);
const J2 = pathCard(732, -0.8, 42, "JALUR 2", "Ontario Crop Heat Unit", "Tmin = (2 × CHU − Ymax) / 1,8 + 4,4", 46);
const pJ1 = B.pin(L.top, 1460, 368, "deco", NAVY), pJ2 = B.pin(L.top, 1460, 748, "deco", NAVY);
const th = [
  [rowY(2), 1000, 520], [rowY(4), 1000, 560], [rowY(4), 1000, 890], [rowY(6), 1000, 930],
].map(([y0, x1, y1]) => B.thread(L.threads, `M936,${y0} C968,${y0} 950,${y1} ${x1},${y1}`, "#3a2f28", 4));
const thOut = [[520, 560], [900, 720]].map(([y0, y1]) => B.thread(L.threads, `M1925,${y0} C1960,${y0} 1960,${y1} 2000,${y1}`, RED, 4.5));

// ───────────── Tmin card: both reconstructions overlap ─────────────
const TC = B.sheet(L.papers, 1990, 230, 790, 960, { seed: 27, amp: 6, step: 12, rot: 0.5, grid: "graph" });
const tc = TC.c;
txt("Suhu minimum harian", { x: 40, y: 82, "font-size": 48, "font-weight": 700, fill: INK }, tc);
const T1 = window.TMIN1 || [], T2 = window.TMIN2 || [];
const lo = 8, hi = 26, px = (i) => 104 + (i / (T1.length - 1)) * 640, py = (v) => 480 - ((v - lo) / (hi - lo)) * 320;
el("path", { d: "M94,490 L94,140", fill: "none", stroke: INK, "stroke-width": 3, "marker-end": "url(#arr)" }, tc);
el("path", { d: "M94,490 L760,490", fill: "none", stroke: INK, "stroke-width": 3, "marker-end": "url(#arr)" }, tc);
[10, 20].forEach((v) => txt(v + "°", { x: 84, y: f1(py(v) + 12), "font-size": 30, "text-anchor": "end", fill: "#4c463f" }, tc));
const ln1 = el("polyline", { points: T1.map((v, i) => `${f1(px(i))},${f1(py(v))}`).join(" "), fill: "none", stroke: INK, "stroke-width": 7, "stroke-linejoin": "round" }, tc);
const ln2 = el("polyline", { points: T2.map((v, i) => `${f1(px(i))},${f1(py(v))}`).join(" "), fill: "none", stroke: RED, "stroke-width": 3.5, "stroke-linejoin": "round" }, tc);
const leg = el("g", { opacity: 0 }, tc);
el("line", { x1: 60, y1: 556, x2: 120, y2: 556, stroke: INK, "stroke-width": 7 }, leg); txt("Jalur 1", { x: 134, y: 568, "font-size": 34, fill: INK }, leg);
el("line", { x1: 340, y1: 556, x2: 400, y2: 556, stroke: RED, "stroke-width": 4 }, leg); txt("Jalur 2", { x: 414, y: 568, "font-size": 34, fill: RED }, leg);
const big = el("g", { opacity: 0 }, tc);
txt("0,047 °C", { x: 395, y: 712, "font-size": 128, "font-weight": 700, "text-anchor": "middle", fill: RED }, big);
txt("SD selisih dua rekonstruksi", { x: 395, y: 776, "font-size": 42, "font-weight": 700, "text-anchor": "middle", fill: INK }, big);
const srcT = txt("Data harian NSC 2026 · 29 Jun – 12 Sep 2023", { x: 395, y: 826, "font-size": 28, "font-style": "italic", "text-anchor": "middle", fill: "#6f685f", opacity: 0 }, tc);
const pTC = B.pin(L.top, 2385, 250, "deco", GOLD);

// ───────────── bottom: from Tmin to relative humidity ─────────────
const PH = B.sheet(L.papers, 130, 1236, 2650, 300, { seed: 33, amp: 6, step: 14, rot: 0.2 });
const ph = PH.c;
const it1 = el("g", { opacity: 0 }, ph);
txt("Tmin", { x: 60, y: 130, "font-size": 72, "font-weight": 700, fill: INK }, it1);
txt("sebagai proksi", { x: 60, y: 190, "font-size": 40, fill: "#5d564e" }, it1);
txt("titik embun", { x: 60, y: 240, "font-size": 40, "font-weight": 700, fill: INK }, it1);
const dropG = el("g", { transform: "translate(560 160) scale(0.82)" }, ph);
const drop = el("g", { opacity: 0 }, dropG);
el("path", { d: "M0,-92 C30,-44 62,-6 62,30 C62,68 34,92 0,92 C-34,92 -62,68 -62,30 C-62,-6 -30,-44 0,-92 Z", fill: "#6f9cc4", stroke: INK, "stroke-width": 5 }, drop);
el("path", { d: "M-30,22 C-30,4 -20,-12 -10,-24", fill: "none", stroke: "#fff", "stroke-width": 8, "stroke-linecap": "round", opacity: 0.7 }, drop);
const ar1 = el("path", { d: "M690,150 L840,150", fill: "none", stroke: RED, "stroke-width": 10, "stroke-linecap": "round", "marker-end": "url(#arrR)" }, ph);
const it2 = el("g", { opacity: 0 }, ph);
txt("Uap air di udara", { x: 880, y: 130, "font-size": 50, "font-weight": 700, fill: INK }, it2);
txt("tekanan uap aktual  e", { x: 880, y: 196, "font-size": 40, fill: "#5d564e" }, it2);
const ar2 = el("path", { d: "M1360,150 L1510,150", fill: "none", stroke: RED, "stroke-width": 10, "stroke-linecap": "round", "marker-end": "url(#arrR)" }, ph);
const it3 = el("g", { opacity: 0 }, ph);
txt("RH = 100 × e / es(T)", { x: 1550, y: 140, "font-size": 70, "font-weight": 700, fill: INK }, it3);
const it3b = el("g", { opacity: 0 }, ph);
txt("e : tekanan uap aktual", { x: 1552, y: 206, "font-size": 38, fill: "#5d564e" }, it3b);
txt("es(T) : tekanan uap jenuh pada suhu T", { x: 1552, y: 254, "font-size": 38, fill: "#5d564e" }, it3b);
// a jar: es(T) is the full jar, e is how far it is filled
const jar = el("g", { transform: "translate(2340 26)", opacity: 0 }, ph);
const jarClip = el("clipPath", { id: "jarClip" }, B.defs);
el("rect", { x: 2340, y: 66, width: 150, height: 200, rx: 18 }, jarClip);
el("rect", { x: 0, y: 40, width: 150, height: 200, rx: 18, fill: "#f7f1e1", stroke: INK, "stroke-width": 5 }, jar);
const fillR = el("rect", { x: 2340, y: 266, width: 150, height: 0, fill: "#6f9cc4", opacity: 0.85, "clip-path": "url(#jarClip)" }, ph);
el("rect", { x: 0, y: 40, width: 150, height: 200, rx: 18, fill: "none", stroke: INK, "stroke-width": 5 }, jar);
txt("es(T)", { x: 172, y: 70, "font-size": 34, "font-weight": 700, fill: INK }, jar);
const eLbl = txt("e", { x: 172, y: 200, "font-size": 40, "font-weight": 700, fill: "#3f6d97", opacity: 0 }, ph);
eLbl.setAttribute("transform", "translate(2340 26)");
const pPH = B.pin(L.top, 1450, 1250, "deco", NAVY);

// ───────────── notes ─────────────
const nQ = B.note(L.notes, 1060, 1080, 820, 140, -1.4, ["Kenapa ini penting?"], { seed: 61, fill: "#e3cf86", fs: [52, 52], bold: true, y0: 92 });
const nP = B.note(L.notes, 1040, 1068, 860, 170, 1.0, ["Physical feature engineering", "dari hubungan termodinamika"], { seed: 62, fill: "#efe5cf", fs: [46, 44], torn: true });
const stampF = B.stamp(L.top, 520, 1162, "PETUNJUK DITEMUKAN", { fs: 42, rot: -3 });
const nT = B.note(L.notes, 2010, 1092, 760, 160, 2.0, ["Pola lingkungan saat kasus", "masih sama?"], { seed: 63, fill: "#f7f1e1", fs: [40, 46] });

// ───────────── timeline ─────────────
B.hideAtStart(ar1, ar2, ML.inner, J1.c.inner, J2.c.inner, J1.f, J2.f, pJ1.s, pJ2.s, TC.inner, pTC.s, ln1, ln2, PH.inner, pPH.s, nQ.inner, nP.inner, nT.inner, ...rows.map((r) => r.g));
uls.forEach((u) => tl.set(u, { opacity: 0 }, 0));

// Pacing: the clue (0–38 s) is told slowly, one step at a time; the payoff (38–60 s) moves faster.

// 0.3  "Di antara catatan sensor, kami menemukan tujuh indeks agronomi harian."
B.camSet(0, 560, 700, 1.12);
tl.to("#bcam", { ...B.cam(560, 720, 1.16), duration: 7, ease: "none" }, 0);
rows.forEach((r, k) => tl.fromTo(r.g, { opacity: 0, x: -16 }, { opacity: 1, x: 0, duration: 0.45, ease: out }, 0.3 + k * 0.4));

// 7.0  "Sekilas cuma variabel tambahan. Tapi waktu kami cek rumusnya, ternyata indeks ini dihitung dari suhu maksimum
//       dan suhu minimum harian."
const lens = B.lens(480, 700, 530);
B.camTo(6.9, 580, 880, 1.15, 1.1);
lens.in(7.2);
lens.hold(8.1, 7.3);
KEY.forEach((k, j) => {
  const t = 8.6 + j * 1.4;
  tl.set(uls[j], { opacity: 1 }, t); B.drawIn(uls[j], t, 0.6, "power2.inOut");
  tl.fromTo(qm[j], { opacity: 0, x: -10 }, { opacity: 1, x: 0, duration: 0.35, ease: out }, t + 0.5);
});
lens.out(15.4);

// 16.4  "Jadi rumusnya kami balik. Ini yang kami sebut Algebraic Inverse Reconstruction. Suhu minimum kami hitung lewat
//        dua jalur: dari rata-rata harian, dan dari indeks Crop Heat Unit."
// Each path lights up the indices it uses, so the three source columns of Tmin read one by one.
const lit = (ks, on, t) => ks.forEach((k) => tl.to(rows[k].t, { attr: { fill: on ? RED : INK, "font-weight": on ? 700 : 400 }, duration: 0.3 }, t));
B.camTo(16.0, 1300, 700, 0.84, 1.4);
tl.to("#bcam", { ...B.cam(1310, 705, 0.86), duration: 11.8, ease: "none" }, 17.4);
B.slap(ML.inner, 16.6, 1.45, -4);
// jalur 1: daily_mean_temperature + daily_max
lit([2, 4], true, 18.2);
B.drawThread(th[0], 18.4, 0.8); B.drawThread(th[1], 18.9, 0.8);
B.slap(J1.c.inner, 19.8, 1.45, 4); B.pinIn(pJ1, 19.8);
tl.fromTo(J1.f, { opacity: 0, x: -14 }, { opacity: 1, x: 0, duration: 0.5, ease: out }, 20.5);
// jalur 2: daily_max + ontario_units
lit([2], false, 23.2); lit([6], true, 23.2);
B.drawThread(th[2], 23.4, 0.8); B.drawThread(th[3], 23.9, 0.8);
B.slap(J2.c.inner, 24.8, 1.45, -4); B.pinIn(pJ2, 24.8);
tl.fromTo(J2.f, { opacity: 0, x: -14 }, { opacity: 1, x: 0, duration: 0.5, ease: out }, 25.5);
// both paths together: Tmin comes from three columns
lit([2], true, 27.6);

// 29.6  "Hasil keduanya hampir sama persis, selisihnya cuma 0,047 derajat. Jadi rekonstruksinya terbukti benar."
B.camTo(29.4, 1940, 720, 1.0, 1.2);
B.slap(TC.inner, 29.8, 1.4, 4); B.pinIn(pTC, 29.8);
B.drawThread(thOut[0], 30.1, 0.5); B.drawThread(thOut[1], 30.3, 0.5);
tl.set(ln1, { opacity: 1 }, 30.6); ln1.style.strokeDasharray = 3000; ln1.style.strokeDashoffset = 3000;
tl.to(ln1, { strokeDashoffset: 0, duration: 1.3, ease: "power1.inOut" }, 30.6);
tl.set(ln2, { opacity: 1 }, 31.6); ln2.style.strokeDasharray = 3000; ln2.style.strokeDashoffset = 3000;
tl.to(ln2, { strokeDashoffset: 0, duration: 1.3, ease: "power1.inOut" }, 31.6);
B.fadeIn(leg, 32.6);
tl.fromTo(big, { opacity: 0, scale: 1.25, transformOrigin: "50% 50%" }, { opacity: 1, scale: 1, duration: 0.45, ease: "power3.out" }, 33.4);
tl.to(srcT, { opacity: 1, duration: 0.4 }, 34.0);
tl.to("#bcam", { ...B.cam(1950, 710, 1.02), duration: 6.8, ease: "none" }, 30.6);

// 37.8  "Kenapa ini penting?"
B.camTo(37.6, 1440, 900, 0.72, 0.7);
B.slap(nQ.inner, 37.9, 1.5, 5);

// 39.6  "Karena suhu minimum bisa dipakai sebagai pendekatan titik embun. Dan titik embun menunjukkan seberapa banyak
//        uap air di udara."
B.camTo(39.4, 960, 1080, 1.0, 0.8);
B.slap(PH.inner, 39.6, 1.15, 1.5); B.pinIn(pPH, 39.6);
B.fadeIn(it1, 39.9);
tl.fromTo(drop, { opacity: 0, y: -60 }, { opacity: 1, y: 0, duration: 0.45, ease: "bounce.out" }, 40.1);
tl.set(ar1, { opacity: 1 }, 40.4); B.drawIn(ar1, 40.4, 0.25);
B.fadeIn(it2, 40.6);
tl.to("#bcam", { ...B.cam(970, 1085, 1.01), duration: 4.2, ease: "none" }, 40.2);

// 44.8  "Sementara kelembapan relatif, secara definisi, adalah perbandingan uap air yang ada dengan uap air maksimum
//        pada suhu itu."
B.camTo(44.6, 1940, 1080, 1.0, 0.8);
tl.set(ar2, { opacity: 1 }, 44.9); B.drawIn(ar2, 44.9, 0.25);
B.fadeIn(it3, 45.1, 0.35);
B.fadeIn(it3b, 45.4, 0.35);
tl.to(jar, { opacity: 1, duration: 0.3 }, 45.6);
tl.to(fillR, { attr: { y: 26 + 40 + 200 - 140, height: 140 }, duration: 0.7, ease: "power2.inOut" }, 45.7);
tl.to(eLbl, { opacity: 1, duration: 0.3 }, 46.3);
tl.to("#bcam", { ...B.cam(1945, 1085, 1.01), duration: 4.6, ease: "none" }, 45.4);

// 50.4  "Jadi fitur ini bukan hasil hitung-hitungan asal. Fitur ini diturunkan langsung dari hukum termodinamika yang
//        mengatur kelembapan."
B.camTo(50.2, 1440, 900, 0.72, 0.8);
tl.to(nQ.inner, { opacity: 0, y: -30, duration: 0.3 }, 50.4);
B.slap(nP.inner, 50.6, 1.5, -5);
tl.to([ar1, ar2], { attr: { "stroke-width": 14 }, duration: 0.25, yoyo: true, repeat: 1 }, 51.0);
tl.to("#bcam", { ...B.cam(1440, 880, 0.7), duration: 4.0, ease: "none" }, 51.0);

// 55.2  "Petunjuk tersembunyi sudah ditemukan."
B.camTo(55.1, 1440, 810, 0.6667, 0.8);
B.stampIn(stampF, 55.5);

// 57.0  "Tapi, apakah pola lingkungan saat kasus terjadi masih sama dengan pola yang selama ini kami pelajari?"
B.slap(nT.inner, 57.0, 1.5, 6);

B.register();

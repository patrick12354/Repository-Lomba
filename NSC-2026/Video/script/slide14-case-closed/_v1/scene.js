// Slide 14 — Case Closed: Berkas 734 (35 s, muted; the presenter speaks the script live).
// Numbers from the final report: public RMSE 2,82744; rolling-origin 5,71 → 4,81, ≈15,8 %, 9/9 folds.
// The small curve in the case file is the real submission (734 predictions, assets/pred.js). No count-ups.
const { el, txt, f1, INK, RED, NAVY, GOLD } = BOARD;
const B = BOARD.make({ duration: 35, title: "CASE CLOSED: BERKAS 734", act: "CASE CLOSED" });
const { tl, L } = B;
const out = "expo.out";

// ───────────── the case file ─────────────
const FO = el("g", {}, L.papers);
const foIn = el("g", {}, FO);
el("path", { d: "M130,262 L150,214 L560,214 L590,262 Z", fill: "#c9a463", stroke: "#7d5f2c", "stroke-width": 3, filter: "url(#shPaper)" }, foIn);
el("rect", { x: 130, y: 258, width: 1210, height: 880, rx: 8, fill: "#d9b77a", stroke: "#7d5f2c", "stroke-width": 3, filter: "url(#shPaper)" }, foIn);
txt("CASE #734 · TIM HEISENBERG", { x: 170, y: 250, "font-size": 30, fill: "#4a3516", class: "rus" }, foIn);
const PA = B.sheet(foIn, 175, 300, 1120, 800, { seed: 15, amp: 6, step: 14, rot: -0.6 });
const pa = PA.c;
txt("RMSE PUBLIK AKHIR", { x: 560, y: 100, "font-size": 62, fill: INK, "text-anchor": "middle", class: "rus" }, pa);
const hero = el("g", { opacity: 0 }, pa);
txt("2,82744", { x: 560, y: 285, "font-size": 200, "font-weight": 700, "text-anchor": "middle", fill: RED }, hero);
const PR = window.PRED || [];
const pmin = Math.min(...PR), pmax = Math.max(...PR);
const cx = (i) => 80 + (i / (PR.length - 1)) * 960, cy = (v) => 455 - ((v - pmin) / (pmax - pmin)) * 140;
const predLine = el("polyline", { points: PR.map((v, i) => `${f1(cx(i))},${f1(cy(v))}`).join(" "), fill: "none", stroke: RED, "stroke-width": 3, "stroke-linejoin": "round" }, pa);
const predLbl = txt("Prediksi submission · 734 titik, setiap 30 menit", { x: 560, y: 500, "font-size": 28, "font-style": "italic", "text-anchor": "middle", fill: "#6f685f", opacity: 0 }, pa);
const cap = el("g", { opacity: 0 }, pa);
txt("734 nilai kelembapan direkonstruksi", { x: 560, y: 562, "font-size": 50, "font-weight": 700, "text-anchor": "middle", fill: INK }, cap);
txt("Rekonstruksi yang dapat diuji dan dipertanggungjawabkan", { x: 560, y: 606, "font-size": 32, "text-anchor": "middle", fill: "#5d564e" }, cap);
const pFO = B.pin(L.top, 735, 314, "deco", RED);

// ───────────── validation card ─────────────
const VC = B.sheet(L.papers, 1420, 230, 1360, 900, { seed: 57, amp: 6, step: 12, rot: 0.5 });
const vc = VC.c;
txt("RMSE validasi rolling-origin", { x: 680, y: 92, "font-size": 54, "font-weight": 700, "text-anchor": "middle", fill: INK }, vc);
txt("sembilan jendela validasi yang sama", { x: 680, y: 144, "font-size": 34, "text-anchor": "middle", fill: "#5d564e" }, vc);
function barRow(y, l1, l2, w, val, col) {
  const g = el("g", { opacity: 0 }, vc);
  txt(l1, { x: 330, y: y + 46, "font-size": 40, "font-weight": 700, "text-anchor": "end", fill: INK }, g);
  txt(l2, { x: 330, y: y + 94, "font-size": 40, "font-weight": 700, "text-anchor": "end", fill: INK }, g);
  const r = el("rect", { x: 360, y: y + 6, width: 0, height: 100, fill: col }, g);
  const v = txt(val, { x: 380 + w, y: y + 78, "font-size": 66, "font-weight": 700, fill: INK, opacity: 0 }, g);
  return { g, r, v, w };
}
const rb = barRow(190, "Baseline", "LightGBM", 5.71 * 133, "5,71", INK);
const rp = barRow(330, "Pipeline", "lengkap", 4.81 * 133, "4,81", RED);
const pct = el("g", { opacity: 0 }, vc);
txt("≈15,8%", { x: 340, y: 600, "font-size": 120, "font-weight": 700, "text-anchor": "middle", fill: RED }, pct);
txt("perbaikan validasi", { x: 340, y: 664, "font-size": 44, "font-weight": 700, "text-anchor": "middle", fill: INK }, pct);
const fold = el("g", { opacity: 0 }, vc);
txt("9/9 fold", { x: 1020, y: 600, "font-size": 120, "font-weight": 700, "text-anchor": "middle", fill: RED }, fold);
txt("hasil lebih baik", { x: 1020, y: 664, "font-size": 44, "font-weight": 700, "text-anchor": "middle", fill: INK }, fold);
const checks = [...Array(9)].map((_, k) => el("path", { d: `M${190 + k * 122},768 L${206 + k * 122},788 L${236 + k * 122},746`, fill: "none", stroke: RED, "stroke-width": 9, "stroke-linecap": "round", "stroke-linejoin": "round" }, vc));
const cav = txt("Jendela validasi tumpang tindih: dibaca sebagai konsistensi", { x: 680, y: 860, "font-size": 34, "font-style": "italic", "text-anchor": "middle", fill: "#5d564e", opacity: 0 }, vc);
const pVC = B.pin(L.top, 2100, 250, "deco", GOLD);

// ───────────── the investigation, in order ─────────────
const ST = B.sheet(L.papers, 130, 1176, 2650, 380, { seed: 33, amp: 6, step: 14, rot: -0.2 });
const stHead = txt("Memahami bukti, bukan sekadar memilih algoritma", { x: 1325, y: 76, "font-size": 50, "font-weight": 700, "text-anchor": "middle", fill: INK, opacity: 0 }, ST.c);
const STEPS = ["Sensor", "Fisika", "Shift", "Ensemble", "Lintasan"];
const steps = STEPS.map((s, k) => {
  const c = B.card(L.top, 250 + k * 500, 1290, 420, 124, [1, -1.2, 0.8, -0.8, 1.1][k], 90 + k);
  txt(s, { x: 210, y: 90, "font-size": 58, "font-weight": 700, "text-anchor": "middle", fill: INK }, c.c);
  return c;
});
const yarns = [0, 1, 2, 3].map((k) => B.thread(L.top, `M${672 + k * 500},1352 C${700 + k * 500},1330 ${722 + k * 500},1374 ${746 + k * 500},1352`, RED, 7));
const quote = el("g", { opacity: 0 }, L.top);
txt("“Petunjuk terpenting bukan selalu yang paling terlihat, melainkan yang berhasil kita pahami.”", { x: 1455, y: 1504, "font-size": 42, "font-weight": 700, "font-style": "italic", "text-anchor": "middle", fill: RED }, quote);

const closed = B.stamp(L.top, 735, 1034, "CASE CLOSED", { fs: 100, rot: -4 });

// ───────────── timeline ─────────────
B.hideAtStart(foIn, pFO.s, VC.inner, pVC.s, ST.inner, ...steps.map((s) => s.inner), ...checks, predLine);

// Pacing (35 s): one beat per script sentence; visuals land in the first ~1.5 s of the beat, then hold for the presenter.

// 0.3  "Setelah seluruh pemeriksaan … inilah solusi terbaik … untuk Berkas 734. RMSE publik akhir: 2,82744."
B.camSet(0, 760, 730, 0.98);
tl.fromTo(foIn, { opacity: 0, y: 40 }, { opacity: 1, y: 0, duration: 0.5, ease: "power3.out" }, 0.1);
B.pinIn(pFO, 0.35);
tl.fromTo(hero, { opacity: 0, scale: 1.18, transformOrigin: "50% 50%" }, { opacity: 1, scale: 1, duration: 0.45, ease: "power3.out" }, 0.7);
tl.to("#bcam", { ...B.cam(760, 740, 1.02), duration: 5, ease: "none" }, 0.1);

// 5.4  "Dalam sembilan rolling-origin validation yang sama, … dari 5,71 pada baseline LightGBM menjadi 4,81."
B.camTo(5.2, 2130, 690, 1.28, 0.9);
B.slap(VC.inner, 5.5, 1.3, -3); B.pinIn(pVC, 5.5);
[rb, rp].forEach((r, k) => { const t = 5.9 + k * 0.5; tl.to(r.g, { opacity: 1, duration: 0.2 }, t); B.grow(r.r, r.w, t + 0.05, 0.5); tl.fromTo(r.v, { opacity: 0, x: -10 }, { opacity: 1, x: 0, duration: 0.25, ease: out }, t + 0.45); });

// 9.4  "Artinya, terdapat perbaikan sekitar 15,8 persen, dengan hasil lebih baik pada kesembilan fold tersebut."
B.fadeIn(pct, 9.4, 0.35);
checks.forEach((c, k) => { tl.set(c, { opacity: 1 }, 9.6 + k * 0.07); B.drawIn(c, 9.6 + k * 0.07, 0.14, "power2.out"); });
B.fadeIn(fold, 9.9, 0.35);
tl.to(cav, { opacity: 1, duration: 0.35 }, 10.2);
tl.to("#bcam", { ...B.cam(2130, 692, 1.29), duration: 3, ease: "none" }, 9.4);

// 12.6  "Namun bagi kami, temuan terpenting bukan hanya angka akhirnya."
B.camTo(12.5, 1440, 810, 0.72, 1.0);

// 14.7  "Kami belajar bahwa solusi yang baik dimulai dengan memahami bukti, bukan sekadar memilih algoritma."
B.slap(ST.inner, 14.7, 1.12, 1);
tl.fromTo(stHead, { opacity: 0, y: 10 }, { opacity: 1, y: 0, duration: 0.35, ease: out }, 14.95);

// 17.9  "Kami memeriksa kualitas sensor, merekonstruksi informasi fisika, mengantisipasi distribution shift, … pola residual …"
steps.forEach((s, k) => { const t = 17.9 + k * 0.3; B.slap(s.inner, t, 1.45, k % 2 ? -5 : 5); if (k) B.drawThread(yarns[k - 1], t - 0.18, 0.22); });
tl.to("#bcam", { ...B.cam(1440, 822, 0.725), duration: 6, ease: "none" }, 17.9);

// 24.1  "Karena dalam sebuah investigasi, petunjuk terpenting bukan selalu yang paling terlihat. Melainkan yang berhasil kita pahami."
tl.fromTo(quote, { opacity: 0, y: 12 }, { opacity: 1, y: 0, duration: 0.45, ease: out }, 24.1);

// 27.6  "734 nilai kelembapan yang semula tidak diketahui kini memiliki rekonstruksi yang dapat diuji dan dipertanggungjawabkan."
B.camTo(27.4, 696, 742, 1.38, 0.9);
tl.set(predLine, { opacity: 1 }, 27.8); predLine.style.strokeDasharray = 6000; predLine.style.strokeDashoffset = 6000;
tl.to(predLine, { strokeDashoffset: 0, duration: 0.9, ease: "power1.inOut" }, 27.8);
tl.to(predLbl, { opacity: 1, duration: 0.3 }, 28.3);
B.fadeIn(cap, 28.5, 0.35);

// 30.6  "Berkas 734: Case Closed."  "Kami Heisenberg. Terima kasih."  (the last frame holds every number)
B.camTo(30.4, 1440, 810, 0.6667, 0.9);
tl.set(closed.g, { opacity: 1 }, 31.0);
tl.fromTo(closed.i, { opacity: 0, scale: 1.15, transformOrigin: "50% 50%" }, { opacity: 1, scale: 1, duration: 0.4, ease: "power3.out" }, 31.0);

B.register();

// Slide 14 — Case Closed: Berkas 734 (35 s, muted; the presenter speaks the script live).
// v3: detective desk under a lamp → Pak Anton's greenhouse.
//  · Pak Anton's hand lays down the final report (2,82744); one sticky note carries the validation (5,71 → 4,81, ≈15,8 %, 9/9).
//  · The five clues are rewritten as detective lessons and filed, in script order, into the kraft CASE #734 folder from slide 1.
//  · The folder closes (3D flip); whip to the greenhouse of slide 1 (garden.js): the "? ? ?" gap in the sensor log fills with
//    the real predictions, the wilted plants recover, Pak Anton smiles, CASE CLOSED is stamped on the frame, thumbs up.
// Real data: Lintasan card + log gap = submission predictions (assets/pred.js); Fisika card = daily Tmin, two paths (assets/tmin.js).
// Beat starts are the same as v1 (_v1/scene.js) so rehearsal timing does not change. No count-ups.
(function () {
  const NS = "http://www.w3.org/2000/svg";
  const INK = "#2b2521", RED = "#a91d1a", NAVY = "#2f3d4f", GOLD = "#c9a13b", OLIVE = "#5b6b3a", PLUM = "#6d2f52", GREY = "#6f685f", IVORY = "#efe5cf";
  const BW = 2880, BH = 1620, DUR = 35;
  const $ = (s) => document.querySelector(s);
  const f1 = (n) => (+n).toFixed(1);
  const rad = (d) => (d * Math.PI) / 180;
  function rng(seed) { return () => { seed |= 0; seed = (seed + 0x6d2b79f5) | 0; let t = Math.imul(seed ^ (seed >>> 15), 1 | seed); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }
  const tl = gsap.timeline({ paused: true });
  const CAM = $("#cam");

  // ───────────── builders ─────────────
  function div(cls, css, parent) {
    const d = document.createElement("div");
    if (cls) d.className = cls;
    Object.assign(d.style, css || {});
    (parent || CAM).appendChild(d);
    return d;
  }
  function svg(w, h, parent, markup, x = 0, y = 0) {
    const s = document.createElementNS(NS, "svg");
    s.setAttribute("width", w); s.setAttribute("height", h); s.setAttribute("viewBox", `${x} ${y} ${w} ${h}`);
    s.style.position = "absolute"; s.style.left = x + "px"; s.style.top = y + "px";
    s.innerHTML = markup;
    parent.appendChild(s);
    return s;
  }
  function torn(w, h, amp, step, seed) {
    const r = rng(seed), pts = [];
    for (let x = 0; x <= w; x += step) pts.push([x, r() * amp]);
    for (let y = 0; y <= h; y += step) pts.push([w - r() * amp, y]);
    for (let x = w; x >= 0; x -= step) pts.push([x, h - r() * amp]);
    for (let y = h; y >= 0; y -= step) pts.push([r() * amp, y]);
    return "polygon(" + pts.map(([x, y]) => `${f1(x)}px ${f1(y)}px`).join(",") + ")";
  }
  // filters are written in computed-style order (colour first) so GSAP interpolates them number by number
  const SH_REST = "drop-shadow(rgba(20, 10, 4, 0.55) 6px 10px 8px)", SH_LIFT = "drop-shadow(rgba(20, 10, 4, 0.42) 30px 48px 26px)";
  // a sheet of paper centred on (cx, cy); animate .o with x/y offsets from that centre
  function sheet(cx, cy, w, h, rot, o = {}) {
    const ob = div("obj", { left: cx - w / 2 + "px", top: cy - h / 2 + "px", width: w + "px", height: h + "px", zIndex: o.z || 5, filter: SH_REST });
    const p = div("paper", {}, ob);
    if (o.bg) p.style.background = o.bg;
    if (o.torn !== false) p.style.clipPath = torn(w, h, o.amp || 6, o.step || 14, o.seed || 7);
    if (o.svg) svg(w, h, p, o.svg);
    gsap.set(ob, { rotation: rot });
    return { o: ob, p, cx, cy, w, h, rot };
  }
  const T = (x, y, s, attrs = "", fill = INK) => `<text x="${x}" y="${y}" font-size="${s}" fill="${fill}" ${attrs}>`;
  const t = (x, y, s, str, attrs = "", fill = INK) => `${T(x, y, s, attrs, fill)}${str}</text>`;
  const poly = (vals, x0, x1, y0, y1, lo, hi) => vals.map((v, i) => `${f1(x0 + (i / (vals.length - 1)) * (x1 - x0))},${f1(y1 - ((v - lo) / (hi - lo)) * (y1 - y0))}`).join(" ");

  // Pak Anton's right hand seen from above: palm at (0,0), sleeve runs down-right at 35° (rotate the holder to aim it)
  function handMarkup(ox = 0, oy = 0) {
    const c = Math.cos(rad(35)), s = Math.sin(rad(35)), P = (d, q = 0) => [ox + c * d - s * q, oy + s * d + c * q];
    const L = (a, b, w, col, cap = "round") => `<path d="M${f1(a[0])},${f1(a[1])} L${f1(b[0])},${f1(b[1])}" stroke="${col}" stroke-width="${w}" stroke-linecap="${cap}" fill="none"/>`;
    let m = "";
    m += L(P(150), P(2600), 180, INK) + L(P(150), P(2600), 166, "#6b7541") + L(P(170, -50), P(2600, -50), 22, "#5d6638");
    // fingers (behind the palm), thumb on the left of the hand
    [[-62, 92], [-21, 110], [20, 104], [58, 84]].forEach(([q, len]) => { const a = P(-60, q), b = P(-60 - len, q * 1.08); m += L(a, b, 54, INK) + L(a, b, 43, "#c98a5e"); });
    { const a = P(-10, 78), b = P(-70, 132); m += L(a, b, 60, INK) + L(a, b, 49, "#c98a5e"); }
    const pc = P(0, 0);
    m += `<ellipse cx="${f1(pc[0])}" cy="${f1(pc[1])}" rx="122" ry="94" transform="rotate(35 ${f1(pc[0])} ${f1(pc[1])})" fill="#c98a5e" stroke="${INK}" stroke-width="6"/>`;
    m += `<ellipse cx="${f1(P(30, -30)[0])}" cy="${f1(P(30, -30)[1])}" rx="70" ry="40" transform="rotate(35 ${f1(P(30, -30)[0])} ${f1(P(30, -30)[1])})" fill="#d89c70" opacity="0.6"/>`;
    [-48, -10, 28].forEach((q) => { const a = P(-74, q - 14), b = P(-74, q + 14); m += L(a, b, 4.5, INK); });
    m += L(P(118, 0), P(150, 0), 2, INK); // wrist line under the cuff
    m += L(P(132), P(232), 196, INK, "butt") + L(P(136), P(228), 184, "#5b6437", "butt") + L(P(150, -70), P(150, 70), 5, "#47502a");
    return m;
  }
  function makeHand(z) {
    const h = div("obj", { left: "0px", top: "0px", width: "0px", height: "0px", zIndex: z, filter: "drop-shadow(26px 40px 22px rgba(15,8,3,0.45))" });
    svg(2700, 2300, h, handMarkup(), -300, -300);
    return h;
  }

  // ───────────── the folder: CASE #734 from slide 1 ─────────────
  const FX = 1100, FY = 600, FW = 900, FH = 680; // closed footprint (spine on the left edge)
  const back = div("obj", { left: FX + "px", top: FY + "px", width: FW + "px", height: FH + "px", zIndex: 2, filter: "drop-shadow(-8px 14px 16px rgba(10,5,2,0.6))" });
  div("kraft", { left: "70px", top: "-46px", width: "290px", height: "60px", right: "auto", bottom: "auto", borderRadius: "14px 14px 0 0", filter: "brightness(0.9)" }, back);
  div("kraft", {}, back);
  div("edge", {}, back);
  const page = sheet(FX + 450, FY + 340, 840, 620, 0.6, { z: 3, seed: 81, svg:
    `<rect x="210" y="40" width="420" height="96" fill="#e2d4b2" transform="rotate(-2 420 88)"/>` +
    t(420, 112, 66, "BUKTI AWAL", 'class="rus" text-anchor="middle"', "#7d1513") +
    t(420, 330, 170, "734", 'class="rus" text-anchor="middle"', RED) +
    t(420, 392, 32, "nilai kelembapan tidak diketahui", 'text-anchor="middle"') +
    t(420, 500, 64, "? ? ?", 'font-weight="700" text-anchor="middle"', RED) });

  const coverWrap = div("", { left: FX + "px", top: FY + "px", width: FW + "px", height: FH + "px", zIndex: 4, filter: "drop-shadow(-10px 16px 18px rgba(10,5,2,0.55))" });
  coverWrap.id = "coverWrap";
  const coverRot = div("", {}, coverWrap); coverRot.id = "coverRot";
  const cFront = div("face", {}, coverRot); cFront.id = "coverFront";
  div("kraft", {}, cFront); div("edge", {}, cFront);
  svg(FW, FH, cFront,
    `<g transform="rotate(-3 200 90)"><rect x="40" y="36" width="330" height="112" fill="${IVORY}" style="filter:drop-shadow(0 3px 5px rgba(0,0,0,0.3))"/>` +
    t(205, 96, 56, "BERKAS 734", 'class="rus" text-anchor="middle"') +
    t(205, 132, 21, "CASE #734 · Missing Humidity", 'class="rus" text-anchor="middle"', "#5a3c1e") + "</g>");
  const cBack = div("face", {}, coverRot); cBack.id = "coverBack";
  div("kraft", { filter: "brightness(1.07)" }, cBack); div("edge", {}, cBack);
  gsap.set(coverRot, { rotationY: -180, transformOrigin: "0% 50%" });

  // ───────────── desk props ─────────────
  const mug = div("obj", { left: "30px", top: "60px", width: "240px", height: "220px", zIndex: 9, filter: "drop-shadow(10px 16px 12px rgba(0,0,0,0.5))" });
  svg(240, 220, mug, `<path d="M190,92 q46,8 44,34 q-2,26 -46,24" fill="none" stroke="#ddd3c2" stroke-width="22" stroke-linecap="round"/><circle cx="100" cy="110" r="98" fill="#e6dccb" stroke="${INK}" stroke-width="4"/><circle cx="100" cy="110" r="76" fill="#3b2312"/><ellipse cx="78" cy="88" rx="26" ry="12" fill="#fff" opacity="0.12" transform="rotate(-30 78 88)"/>`);
  const lensProp = div("obj", { left: "-40px", top: "1180px", width: "360px", height: "360px", zIndex: 9, filter: "drop-shadow(12px 18px 12px rgba(0,0,0,0.5))" });
  svg(360, 360, lensProp, `<path d="M240,250 L340,350" stroke="${INK}" stroke-width="46" stroke-linecap="round"/><path d="M240,250 L340,350" stroke="#6b4a2c" stroke-width="36" stroke-linecap="round"/><circle cx="160" cy="165" r="118" fill="#cfe2e8" fill-opacity="0.18" stroke="${INK}" stroke-width="30"/><circle cx="160" cy="165" r="118" fill="none" stroke="#a98a4f" stroke-width="20"/><path d="M90,120 A95,95 0 0 1 150,72" fill="none" stroke="#fff" stroke-width="10" stroke-linecap="round" opacity="0.35"/>`);
  const pol = sheet(2160, 1440, 300, 340, 7, { z: 8, torn: false, bg: "#f4f1ea", svg:
    `<defs><linearGradient id="pSky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#e9eee2"/><stop offset="1" stop-color="#f5ecd6"/></linearGradient></defs>` +
    `<rect x="20" y="20" width="260" height="240" fill="url(#pSky)"/>` +
    `<path d="M20,150 L150,70 L280,150 Z" fill="none" stroke="#9aa49a" stroke-width="5"/>` +
    [60, 100, 140, 180, 220, 260].map((x) => `<line x1="${x}" y1="${150 - Math.max(0, 80 - Math.abs(x - 150)) * 0.95}" x2="${x}" y2="260" stroke="#b8c0b4" stroke-width="3"/>`).join("") +
    `<rect x="20" y="200" width="260" height="60" fill="#6f4f33"/>` + [40, 90, 140, 190, 240].map((x, i) => `<ellipse cx="${x}" cy="${190 + (i % 2) * 6}" rx="30" ry="22" fill="${i % 2 ? "#4f7a3a" : "#5f8c44"}"/>`).join("") +
    `<line x1="232" y1="120" x2="232" y2="210" stroke="#7e8581" stroke-width="5"/><rect x="220" y="112" width="26" height="22" fill="#d6dad4" stroke="${INK}" stroke-width="2"/>` +
    t(150, 304, 24, "kebun Pak Anton", 'font-style="italic" text-anchor="middle"', "#4b443d") });

  const nb = div("obj", { left: "2240px", top: "1000px", width: "560px", height: "400px", zIndex: 7, filter: SH_REST });
  svg(560, 400, nb, `<rect x="0" y="0" width="560" height="400" rx="12" fill="${NAVY}" stroke="${INK}" stroke-width="5"/>` +
    [...Array(16)].map((_, i) => `<rect x="${26 + i * 33}" y="-14" width="8" height="30" rx="4" fill="#8a8e93" stroke="${INK}" stroke-width="2"/>`).join("") +
    `<rect x="110" y="150" width="340" height="96" fill="${IVORY}" transform="rotate(-2 280 198)"/>` + t(280, 216, 46, "CATATAN SENSOR", 'class="rus" text-anchor="middle"'));
  gsap.set(nb, { rotation: -5 });

  // ───────────── five clues, rewritten as what each one taught us (each with its index tab) ─────────────
  const PR = window.PRED || [], T1 = window.TMIN1 || [], T2 = window.TMIN2 || [];
  const prLo = Math.min(...PR), prHi = Math.max(...PR);
  const tLo = Math.min(...T1, ...T2), tHi = Math.max(...T1, ...T2);
  const spikePts = [...Array(28)].map((_, i) => { const x = 40 + i * 20; const y = i === 13 ? 228 : 338 + Math.sin(i * 1.3) * 9 + Math.sin(i * 0.45) * 6; return `${x},${f1(y)}`; }).join(" ");
  const gauss = (mu, sg, amp, y0) => { let d = `M40,${y0}`; for (let x = 40; x <= 600; x += 10) d += ` L${x},${f1(y0 - amp * Math.exp(-((x - mu) ** 2) / (2 * sg * sg)))}`; return d + ` L600,${y0} Z`; };
  // layout: lesson number (y 56) · the lesson in two lines (y 122/176) · a small reminder of the evidence (y 205–360) · the fact (y 408)
  const lesson = (n, l1, l2, col) => t(36, 56, 30, `PELAJARAN ${n}`, 'class="rus"', col) + t(36, 122, 46, l1, 'font-weight="700"') + t(36, 176, 46, l2, 'font-weight="700"');
  const EVD = [
    { label: "SENSOR", col: RED, tc: IVORY, cx: 470, cy: 430, rot: -5, svg:
      lesson(1, "Saksi pertama", "belum tentu jujur.", RED) +
      `<polyline points="${spikePts}" fill="none" stroke="${NAVY}" stroke-width="4" stroke-linejoin="round"/>` +
      `<circle cx="300" cy="228" r="26" fill="none" stroke="${RED}" stroke-width="5"/>` + t(338, 240, 32, "54,1 °C", 'font-weight="700"', RED) +
      t(36, 408, 25, "lonjakan sensor → dibersihkan (Hampel)", "", GREY) },
    { label: "FISIKA", col: NAVY, tc: IVORY, cx: 1150, cy: 420, rot: 3, svg:
      lesson(2, "Hukum alam", "ikut bersaksi.", NAVY) +
      `<polyline points="${poly(T1, 40, 590, 222, 352, tLo, tHi)}" fill="none" stroke="${NAVY}" stroke-width="4"/>` +
      `<polyline points="${poly(T2, 40, 590, 222, 352, tLo, tHi)}" fill="none" stroke="${RED}" stroke-width="3" stroke-dasharray="9 7"/>` +
      t(36, 408, 25, "RH = 100 × e / es(T) · Tmin dua jalur", "", GREY) },
    { label: "SHIFT", col: GOLD, tc: INK, cx: 560, cy: 930, rot: 4, svg:
      lesson(3, "Masa depan tak", "mirip masa lalu.", "#8a6a12") +
      `<path d="${gauss(220, 62, 125, 362)}" fill="${NAVY}" fill-opacity="0.16" stroke="${NAVY}" stroke-width="4"/>` +
      `<path d="${gauss(400, 52, 110, 362)}" fill="${RED}" fill-opacity="0.12" stroke="${RED}" stroke-width="4"/>` +
      `<path d="M252,226 L352,226 M336,214 L354,226 L336,238" fill="none" stroke="${INK}" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>` +
      t(120, 262, 26, "latih", 'font-weight="700"', NAVY) + t(462, 280, 26, "uji", 'font-weight="700"', RED) +
      t(36, 408, 25, "distribution shift: periode uji ≠ latih", "", GREY) },
    { label: "ENSEMBLE", col: OLIVE, tc: IVORY, cx: 880, cy: 1270, rot: -6, svg:
      lesson(4, "Satu saksi", "tidak pernah cukup.", OLIVE) +
      [110, 215, 320, 425, 530].map((x, i) => `<path d="M${x},226 Q${(x + 320) / 2},${280 + (i % 2) * 12} 320,326" fill="none" stroke="${RED}" stroke-width="4"/>`).join("") +
      [110, 215, 320, 425, 530].map((x, i) => `<circle cx="${x}" cy="226" r="17" fill="${[NAVY, GOLD, OLIVE, PLUM, "#8b857c"][i]}" stroke="${INK}" stroke-width="3"/>`).join("") +
      `<rect x="250" y="316" width="140" height="48" fill="#e3cf86" stroke="${INK}" stroke-width="3"/>` + t(320, 350, 28, "NNLS", 'font-weight="700" text-anchor="middle"') +
      t(36, 408, 25, "5 model · bobot ≥ 0 · 3 pita waktu", "", GREY) },
    { label: "LINTASAN", col: PLUM, tc: IVORY, cx: 1760, cy: 430, rot: -3, svg:
      lesson(5, "Kesalahan pun", "punya pola.", PLUM) +
      `<polyline points="${poly(PR, 40, 590, 214, 356, prLo, prHi)}" fill="none" stroke="${RED}" stroke-width="3" stroke-linejoin="round"/>` +
      t(36, 408, 25, "residual lag-1 ≈ 0,93 → level + increment", "", GREY) },
  ];
  const cards = EVD.map((e, k) => {
    const c = sheet(e.cx, e.cy, 640, 440, e.rot, { z: 10 + k, seed: 30 + k * 11, svg: e.svg });
    const tab = div("tab", { left: "632px", top: 26 + k * 82 + "px", background: e.col, color: e.tc }, c.o);
    const sp = document.createElement("span"); sp.style.position = "relative"; sp.style.zIndex = 1; sp.textContent = e.label; tab.appendChild(sp);
    c.o.insertBefore(tab, c.p); // the divider tab sits under its sheet
    return c;
  });

  // ───────────── final report + validation sheet ─────────────
  const R = sheet(2440, 410, 800, 600, 1.5, { z: 16, seed: 15, svg:
    t(400, 76, 40, "LAPORAN AKHIR · BERKAS 734", 'class="rus" text-anchor="middle"', "#4a3516") +
    `<line x1="120" y1="100" x2="680" y2="100" stroke="${RED}" stroke-width="4"/>` +
    t(400, 182, 58, "RMSE PUBLIK AKHIR", 'class="rus" text-anchor="middle"') +
    `<g id="hero">${t(400, 384, 168, "2,82744", 'font-weight="700" text-anchor="middle"', RED)}</g>` +
    t(400, 470, 30, "solusi terbaik untuk Berkas 734", 'font-style="italic" text-anchor="middle"', GREY) });
  // the validation, kept to one sticky note on the report (it travels with the report)
  const note = div("obj", { left: "500px", top: "410px", width: "420px", height: "330px", filter: SH_REST }, R.o);
  div("paper", { background: "#e8d27e", backgroundImage: "url(assets/tex/paper.png)", backgroundBlendMode: "multiply", backgroundSize: "cover" }, note);
  svg(420, 330, note,
    `<path d="M0,0 L420,0 L420,46 L0,46 Z" fill="#000" opacity="0.05"/>` +
    t(210, 64, 28, "VALIDASI · 9 JENDELA", 'class="rus" text-anchor="middle"', "#5a4a14") +
    `<g id="nA" opacity="0">${t(210, 132, 54, "5,71 → 4,81", 'font-weight="700" text-anchor="middle"')}${t(210, 166, 20, "baseline LightGBM → pipeline lengkap", 'text-anchor="middle"', "#5a4f3a")}</g>` +
    `<g id="nB" opacity="0">${t(210, 236, 44, "≈15,8% lebih baik", 'font-weight="700" text-anchor="middle"', RED)}${t(210, 290, 36, "9/9 fold ✓", 'font-weight="700" text-anchor="middle"')}</g>`);
  gsap.set(note, { rotation: 5 });
  div("", { position: "absolute", left: "150px", top: "-18px", width: "120px", height: "40px", background: "rgba(240,232,210,0.7)", transform: "rotate(-4deg)" }, note);

  const hand = makeHand(60);
  gsap.set(hand, { x: 3300, y: 2200 });

  // ───────────── ambient: screen dust + grain, world dust puffs ─────────────
  const rd = rng(42), dust = $("#dust");
  for (let i = 0; i < 26; i++) {
    const m = document.createElement("div"); m.className = "mote";
    const sz = 2 + rd() * 4; m.style.width = m.style.height = sz.toFixed(1) + "px";
    m.style.left = (rd() * 1920).toFixed(0) + "px"; m.style.top = (120 + rd() * 900).toFixed(0) + "px"; m.style.opacity = (0.15 + rd() * 0.3).toFixed(2);
    dust.appendChild(m);
    tl.fromTo(m, { x: 0, y: 0 }, { x: (rd() - 0.5) * 220, y: -(140 + rd() * 260), duration: DUR, ease: "none" }, 0);
  }
  tl.fromTo("#grain", { x: 0, y: 0 }, { x: -60, y: -60, duration: DUR, ease: `steps(${DUR * 15})` }, 0);
  function puff(t0, x, y, w, h, n, seed, spread = 120) {
    const r = rng(seed);
    for (let i = 0; i < n; i++) {
      const side = i % 4, u = r();
      const px = side === 0 ? x + u * w : side === 1 ? x + w : side === 2 ? x + u * w : x;
      const py = side === 0 ? y : side === 1 ? y + u * h : side === 2 ? y + h : y + u * h;
      const dx = side === 1 ? 1 : side === 3 ? -1 : (u - 0.5) * 0.6, dy = side === 0 ? -1 : side === 2 ? 1 : (u - 0.5) * 0.6;
      const sz = 10 + r() * 22;
      const p = div("", { position: "absolute", left: px + "px", top: py + "px", width: sz + "px", height: sz + "px", borderRadius: "50%", background: "rgba(236,222,196,0.55)", filter: "blur(4px)", zIndex: 70, opacity: 0 });
      tl.set(p, { opacity: 0.85, x: 0, y: 0, scale: 0.6 }, t0);
      tl.to(p, { opacity: 0, x: dx * spread * (0.5 + r()), y: dy * spread * (0.5 + r()), scale: 1.8, duration: 0.9 + r() * 0.4, ease: "power2.out" }, t0);
    }
  }

  // ───────────── camera + motion helpers ─────────────
  const cam = (fx, fy, s, m = 260) => { let x = 960 - fx * s, y = 540 - fy * s; x = Math.min(m * s, Math.max(1920 - (BW + m) * s, x)); y = Math.min(m * s, Math.max(1080 - (BH + m) * s, y)); return { x, y, scale: s }; };
  const camTo = (t0, fx, fy, s, d = 1.2, ease = "power3.inOut") => tl.to(CAM, { ...cam(fx, fy, s), duration: d, ease }, t0);
  const shake = (t0, k = 1) => [[14, -10], [-12, 8], [9, 6], [-6, -5], [3, 3], [0, 0]].forEach(([x, y], i) => tl.to("#shake", { x: x * k, y: y * k, duration: 0.05, ease: "none" }, t0 + i * 0.05));
  const grabPt = (c, cx, cy, rot, sc = 1) => { const a = rad(rot), ox = (c.w / 2 - 120) * sc, oy = (c.h / 2 - 90) * sc; return [cx + ox * Math.cos(a) - oy * Math.sin(a), cy + ox * Math.sin(a) + oy * Math.cos(a)]; };
  // hand reaches a sheet, lifts it, carries it to (sx, sy) and lays it down
  function carry(c, t0, sx, sy, srot, z, o = {}) {
    const sc = o.scale || 1, reach = o.reach ?? 0.32, d = o.d || 0.5;
    const from = o.from || [c.cx, c.cy, c.rot];
    const g0 = grabPt(c, from[0], from[1], from[2]), g1 = grabPt(c, sx, sy, srot, sc);
    if (reach) tl.to(hand, { x: g0[0], y: g0[1], rotation: o.hr || 0, duration: reach, ease: "power2.inOut" }, t0);
    const t1 = t0 + reach;
    tl.set(c.o, { zIndex: z }, t1 - 0.02);
    tl.to(c.o, { x: sx - c.cx, y: sy - c.cy, rotation: srot, duration: d, ease: "power2.inOut" }, t1);
    tl.to(c.o, { scale: 1.05 * sc, filter: SH_LIFT, duration: d * 0.45, ease: "power2.out" }, t1);
    tl.to(c.o, { scale: sc, filter: SH_REST, duration: d * 0.55, ease: "power2.in" }, t1 + d * 0.45);
    tl.to(hand, { x: g1[0], y: g1[1], rotation: o.hr2 || 0, duration: d, ease: "power2.inOut" }, t1);
    return t1 + d;
  }
  const strip = (sel, t0, inn = true) => inn
    ? tl.fromTo(sel, { opacity: 0, y: 60, rotation: -1.5 }, { opacity: 1, y: 0, rotation: 0, duration: 0.5, ease: "expo.out" }, t0)
    : tl.to(sel, { opacity: 0, y: 40, duration: 0.35, ease: "power2.in" }, t0);
  gsap.set(".strip", { xPercent: -50 });
  tl.set(["#head", "#quote", "#sign"], { opacity: 0 }, 0);
  $("#head .paper").style.clipPath = torn(1500, 120, 7, 14, 3);
  $("#quote .paper").style.clipPath = torn(1460, 180, 7, 14, 4);

  const hero = $("#hero");
  tl.set(note, { opacity: 0 }, 0);

  // ═════════════════════════ timeline (beat starts = v1) ═════════════════════════
  // 0.0  "Setelah seluruh pemeriksaan … inilah solusi terbaik … untuk Berkas 734. RMSE publik akhir: 2,82744."
  tl.set(CAM, cam(2440, 430, 1.28), 0);
  tl.set(hero, { opacity: 0 }, 0);
  tl.set(R.o, { x: 520, y: 900, rotation: 14 }, 0);
  tl.set(hand, { ...(() => { const g = grabPt(R, R.cx + 520, R.cy + 900, 14); return { x: g[0], y: g[1] }; })() }, 0);
  carry(R, 0.0, R.cx, R.cy, R.rot, 16, { from: [R.cx + 520, R.cy + 900, 14], reach: 0, d: 0.6 });
  tl.to(hand, { x: 3300, y: 1700, rotation: 6, duration: 0.55, ease: "power2.in" }, 0.68);
  tl.fromTo(hero, { opacity: 0, scale: 1.35, transformOrigin: "50% 50%" }, { opacity: 1, scale: 1, duration: 0.32, ease: "power4.out" }, 0.8);
  shake(1.08, 0.45);
  tl.to(CAM, { ...cam(2440, 425, 1.33), duration: 4.1, ease: "none" }, 1.1);

  // 5.4  "Dalam sembilan rolling-origin validation yang sama, … dari 5,71 pada baseline LightGBM menjadi 4,81."
  camTo(5.2, 2560, 560, 1.05, 0.9);
  tl.fromTo(note, { opacity: 0, scale: 1.5, rotation: 14 }, { opacity: 1, scale: 1, rotation: 5, duration: 0.34, ease: "expo.out" }, 5.4);
  tl.fromTo("#nA", { opacity: 0, y: 8 }, { opacity: 1, y: 0, duration: 0.3, ease: "expo.out" }, 5.75);

  // 9.4  "Artinya, terdapat perbaikan sekitar 15,8 persen, dengan hasil lebih baik pada kesembilan fold tersebut."
  tl.fromTo("#nB", { opacity: 0, scale: 1.2, transformOrigin: "50% 50%" }, { opacity: 1, scale: 1, duration: 0.3, ease: "power4.out" }, 9.4);
  tl.to(CAM, { ...cam(2560, 565, 1.09), duration: 3, ease: "none" }, 9.4);

  // 12.6  "Namun bagi kami, temuan terpenting bukan hanya angka akhirnya."  → pull back: the whole desk, every clue
  camTo(12.45, 1440, 810, 0.6667, 1.5, "power3.inOut");
  tl.to("#lamp", { opacity: 0.85, duration: 1.5 }, 12.45);

  // 14.7  "Kami belajar bahwa solusi yang baik dimulai dengan memahami bukti, bukan sekadar memilih algoritma."
  strip("#head", 14.7);
  camTo(15.0, 820, 700, 0.86, 1.2, "power2.inOut");
  tl.to(CAM, { ...cam(1300, 640, 0.86), duration: 1.4, ease: "sine.inOut" }, 16.2);

  // 17.9  "Kami memeriksa kualitas sensor, merekonstruksi informasi fisika, mengantisipasi distribution shift,
  //        menggabungkan model …, lalu menggunakan pola residual …"  → each clue is filed, in that order
  camTo(17.5, 1230, 860, 0.8, 0.8);
  const SLOT_X = FX + FW - 5 - 320, SLOT_Y = FY + 340, SROT = [-1.2, 0.8, -0.5, 1.0, -0.3], HR = [28, 8, 30, 22, 0];
  tl.set(hand, { x: 2400, y: 2000, rotation: 20 }, 17.5);
  cards.forEach((c, k) => carry(c, 17.9 + k * 1.0 - 0.3, SLOT_X, SLOT_Y + k * 3, SROT[k], 20 + k, { hr: HR[k], hr2: 0, reach: 0.3 }));

  // 23.0  [Diam sejenak] the report (with its sticky note) goes in on top
  camTo(22.8, 1900, 760, 0.74, 0.9);
  carry(R, 23.1, FX + 430, FY + 345, -0.4, 27, { scale: 0.97, reach: 0.4, d: 0.6 });
  tl.to(hand, { x: 3300, y: 2300, rotation: 10, duration: 0.5, ease: "power2.in" }, 24.15);

  // 24.1  "Karena dalam sebuah investigasi, petunjuk terpenting bukan selalu yang paling terlihat. Melainkan yang berhasil kita pahami."
  strip("#head", 23.85, false);
  strip("#quote", 24.1);
  tl.to("#dim", { opacity: 0.55, duration: 1.0 }, 24.1);
  camTo(24.9, 1560, 900, 0.86, 1.2);
  tl.set(coverWrap, { zIndex: 40 }, 25.1);
  tl.to(coverRot, { rotationY: 0, duration: 1.15, ease: "power3.inOut" }, 25.15);
  puff(26.25, FX, FY, FW, FH, 22, 7);
  shake(26.27, 0.5);
  tl.to(cards.map((c) => c.o), { x: "+=6", duration: 0.08, yoyo: true, repeat: 1, ease: "power1.out" }, 26.27);

  // 27.3  whip up off the desk, into Pak Anton's greenhouse (the world of slide 1)
  const G = window.GARDEN;
  const gcam = (fx, fy, z) => { let x = 960 - fx * z, y = 540 - fy * z; x = Math.min(0, Math.max(1920 - 1920 * z, x)); y = Math.min(0, Math.max(1080 - 1080 * z, y)); return { x, y, scale: z }; };
  strip("#quote", 27.2, false);
  tl.to("#view", { y: 420, filter: "blur(16px)", duration: 0.42, ease: "power2.in" }, 27.3);
  tl.to(["#lamp", "#dim"], { opacity: 0, duration: 0.4 }, 27.35);
  tl.set("#garden", { opacity: 1, y: -420, filter: "blur(16px)" }, 27.62);
  tl.to("#garden", { y: 0, filter: "blur(0px)", duration: 0.5, ease: "power3.out" }, 27.62);
  tl.set("#view", { opacity: 0 }, 28.1);
  tl.set("#gWorld", gcam(900, 620, 1.12), 0);
  tl.to("#gWorld", { ...gcam(960, 560, 1.0), duration: 2.4, ease: "power2.inOut" }, 27.62);
  // ambient life in the greenhouse (same as slide 1)
  G.swayers.forEach((w) => {
    tl.fromTo(w.g, { attr: { transform: `rotate(${f1(w.amp)} ${f1(w.nx)} ${f1(w.ny)})` } }, { attr: { transform: `rotate(${f1(-w.amp)} ${f1(w.nx)} ${f1(w.ny)})` }, duration: w.per, ease: "sine.inOut", yoyo: true, repeat: Math.ceil(9 / w.per) }, 27.0);
  });
  tl.to("#torso", { attr: { transform: "translate(0 -2) scale(1 1.012)" }, duration: 1.7, ease: "sine.inOut", yoyo: true, repeat: 5 }, 27.0);
  tl.to("#rays polygon", { opacity: 0.3, duration: 3.5, ease: "sine.inOut", yoyo: true, repeat: 2, stagger: 0.8 }, 27.0);

  // 27.6  "734 nilai kelembapan yang semula tidak diketahui kini memiliki rekonstruksi yang dapat diuji dan dipertanggungjawabkan."
  //       → the torn log page from slide 1: its "? ? ?" gap fills with the real predictions
  {
    const sh = $("#nbSheet");
    sh.querySelector(".paper").style.clipPath = torn(660, 310, 5, 12, 21);
    const xs = []; for (let x = 196; x <= 640; x += 22.2) xs.push(x);
    const gapA = 380, gapB = 566, seg = PR.slice(0, 160), sLo = Math.min(...seg), sHi = Math.max(...seg);
    svg(660, 310, sh,
      t(16, 136, 26, "Kelembapan", 'font-weight="700"') + t(16, 216, 26, "Sensor lain", 'font-weight="700"') +
      `<path d="M176,262 L650,262" stroke="${INK}" stroke-width="2.5"/><path d="M640,254 L652,262 L640,270" fill="none" stroke="${INK}" stroke-width="2.5"/>` + t(420, 298, 24, "Waktu", 'text-anchor="middle"') +
      `<line x1="196" y1="128" x2="${gapA - 8}" y2="128" stroke="${NAVY}" stroke-width="3"/><line x1="${gapB + 8}" y1="128" x2="640" y2="128" stroke="${NAVY}" stroke-width="3"/><line x1="196" y1="208" x2="640" y2="208" stroke="${NAVY}" stroke-width="3"/>` +
      xs.filter((x) => x < gapA - 6 || x > gapB + 6).map((x) => `<circle cx="${f1(x)}" cy="128" r="7.5" fill="${NAVY}"/>`).join("") + xs.map((x) => `<circle cx="${f1(x)}" cy="208" r="7.5" fill="${NAVY}"/>`).join("") +
      `<rect id="gapBox" x="${gapA}" y="100" width="${gapB - gapA}" height="56" fill="none" stroke="${RED}" stroke-width="3.5" stroke-dasharray="10 6"/>` +
      `<g id="gapQ">${[0, 1, 2].map((k) => t(gapA + 46 + k * 46, 141, 38, "?", 'font-weight="700" text-anchor="middle"', RED)).join("")}</g>` +
      `<polyline id="gapLine" points="${poly(seg, gapA - 8, gapB + 8, 106, 150, sLo, sHi)}" fill="none" stroke="${RED}" stroke-width="4" stroke-linejoin="round"/>` +
      `<g id="gapLbl" opacity="0"><rect x="${gapA - 46}" y="54" width="${gapB - gapA + 92}" height="40" fill="${RED}"/>${t((gapA + gapB) / 2, 83, 23, "734 nilai direkonstruksi", 'font-weight="700" text-anchor="middle"', IVORY)}</g>`);
    sh.appendChild(sh.querySelector(".lbl"));
    const gl = $("#gapLine"), len = 900; gl.style.strokeDasharray = len; gl.style.strokeDashoffset = len;
    tl.fromTo(sh, { y: -420, rotation: -9 }, { y: 0, rotation: -2.5, duration: 0.6, ease: "power3.out" }, 27.9);
    tl.to("#gapQ", { opacity: 0, duration: 0.25, ease: "power2.in" }, 28.35);
    tl.to(gl, { strokeDashoffset: 0, duration: 0.75, ease: "power1.inOut" }, 28.4);
    tl.set("#gapBox", { attr: { "stroke-dasharray": "0 0" } }, 29.1);
    tl.fromTo("#gapLbl", { opacity: 0, y: 10 }, { opacity: 1, y: 0, duration: 0.3, ease: "back.out(2)" }, 29.0);
  }

  //       … and the greenhouse answers: the plants recover, the sensor reports, Pak Anton smiles
  G.pairs.forEach((pp, k) => {
    const t0 = 29.15 + k * 0.18, o = `${pp.x} ${pp.baseY}`;
    tl.to(pp.gW, { opacity: 0, duration: 0.35, ease: "power1.in" }, t0);
    tl.fromTo(pp.gH, { opacity: 0, scaleY: 0.86, svgOrigin: o }, { opacity: 1, scaleY: 1, svgOrigin: o, duration: 0.7, ease: "back.out(1.8)" }, t0);
  });
  tl.to(".wfInk, .wf", { opacity: 1, duration: 0.15, stagger: 0.12 }, 29.2);
  tl.to(".wfInk, .wf", { opacity: 0.25, duration: 0.5, stagger: 0.12, yoyo: true, repeat: 5, ease: "sine.inOut" }, 29.9);
  tl.fromTo("#led", { attr: { r: 6.5 } }, { attr: { r: 10 }, duration: 0.3, yoyo: true, repeat: 7, ease: "sine.inOut" }, 29.2);
  tl.to("#headR", { attr: { transform: "rotate(-3 -5 40)" }, duration: 0.45, ease: "power2.inOut" }, 29.35);
  tl.to("#pupils", { attr: { transform: "translate(1 -1)" }, duration: 0.3, ease: "power2.out" }, 29.35);
  tl.to("#browN", { attr: { transform: "translate(0 -6) rotate(-6 7 -27)" }, duration: 0.3, ease: "power2.out" }, 29.45);
  tl.to("#browF", { attr: { transform: "translate(0 -6) rotate(6 36 -30)" }, duration: 0.3, ease: "power2.out" }, 29.45);
  tl.to("#mouth", { attr: { d: "M27,38 Q40,54 53,38" }, duration: 0.3, ease: "power2.out" }, 29.5);
  G.bubT.forEach((b, i) => tl.to(b, { attr: { transform: `translate(${[948, 972][i]} ${[560, 528][i]}) scale(1)` }, duration: 0.25, ease: "back.out(2.5)" }, 29.6 + i * 0.1));
  tl.to(G.bub, { attr: { transform: "translate(1036 452) scale(1)" }, duration: 0.4, ease: "back.out(2.2)" }, 29.8);

  // 30.6  "Berkas 734: Case Closed."  → the stamp lands on the whole frame, Pak Anton gives a thumbs up
  tl.fromTo("#bigStamp", { opacity: 0, scale: 2.3, rotation: -14 }, { opacity: 0.93, scale: 1, rotation: -7, duration: 0.2, ease: "power4.in" }, 30.85);
  [[16, -11], [-13, 9], [10, 7], [-6, -5], [3, 3], [0, 0]].forEach(([x, y], i) => tl.to("#garden", { x, y, duration: 0.05, ease: "none" }, 31.05 + i * 0.05));
  tl.set("#flash", { opacity: 0.6 }, 31.05);
  tl.to("#flash", { opacity: 0, duration: 0.35, ease: "power2.out" }, 31.06);
  tl.to(G.bub, { attr: { transform: "translate(1036 452) scale(0)" }, duration: 0.25, ease: "power2.in" }, 31.15);
  G.bubT.forEach((b, i) => tl.to(b, { attr: { transform: `translate(${[948, 972][i]} ${[560, 528][i]}) scale(0)` }, duration: 0.2, ease: "power2.in" }, 31.2));
  G.armMove(tl, G.arms.near, G.lerp2(G.REST_N, [185, -165]), 31.25, 0.45, "back.out(1.6)", 12);
  tl.to("#thumbUp", { opacity: 1, duration: 0.1 }, 31.5);
  tl.to("#torso", { attr: { transform: "translate(0 -10) scale(1 1.02)" }, duration: 0.18, ease: "power2.out", yoyo: true, repeat: 1 }, 31.35);

  // 32.0  "Kami Heisenberg. Terima kasih."
  tl.to("#gWorld", { ...gcam(930, 600, 1.06), duration: 3.0, ease: "sine.inOut" }, 32.0);
  tl.fromTo("#sign", { opacity: 0, y: 20 }, { opacity: 1, y: 0, duration: 0.8, ease: "power2.out" }, 32.6);

  tl.set({}, {}, DUR); // pin the root length
  window.SCENE_TL = tl;
})();

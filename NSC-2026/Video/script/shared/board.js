// board.js — shared investigation-board kit for the Berkas 734 videos (slides 3, 4, 8, 9, 14).
// Same world as slide 10: cork board 2880×1620 in a wooden frame, torn paper sheets, pins, yarn,
// stamps, a magnifier held by Pak Anton's hand. Each project copies this file to assets/board.js
// (run shared/sync.sh after editing it here).
(function () {
  const NS = "http://www.w3.org/2000/svg";
  const INK = "#2b2521", RED = "#a91d1a", NAVY = "#2f3d4f", GOLD = "#c9a13b", GREY = "#6c665e";
  const $ = (s) => document.querySelector(s);
  const f1 = (n) => (+n).toFixed(1);
  const rad = (d) => (d * Math.PI) / 180;
  function el(tag, attrs, parent) {
    const e = document.createElementNS(NS, tag);
    for (const k in attrs) e.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(e);
    return e;
  }
  const txt = (s, attrs, parent) => { const t = el("text", attrs, parent); t.textContent = s; return t; };
  function rng(seed) { return () => { seed |= 0; seed = (seed + 0x6d2b79f5) | 0; let t = Math.imul(seed ^ (seed >>> 15), 1 | seed); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }

  const BW = 2880, BH = 1620;

  function make(o) {
    const tl = gsap.timeline({ paused: true });
    const DUR = o.duration;
    const board = $("#board"), defs = board.querySelector("defs");
    const L = {};
    ["papers", "threads", "mid", "notes", "top", "frame"].forEach((k) => (L[k] = el("g", { id: "lay-" + k }, board)));
    L.notes.setAttribute("data-layout-allow-overlap", "");

    function tornPts(w, h, amp, step, seed) {
      const r = rng(seed), pts = [];
      for (let x = 0; x <= w; x += step) pts.push([x, r() * amp]);
      for (let y = 0; y <= h; y += step) pts.push([w - r() * amp, y]);
      for (let x = w; x >= 0; x -= step) pts.push([x, h - r() * amp]);
      for (let y = h; y >= 0; y -= step) pts.push([r() * amp, y]);
      return pts.map(([x, y]) => f1(x) + "," + f1(y)).join(" ");
    }
    let clipN = 0;
    // a sheet of paper: g(transform) > inner (animate this) > body + texture + c (content, local coords)
    function sheet(parent, x, y, w, h, s = {}) {
      const g = el("g", { transform: `translate(${x} ${y}) rotate(${s.rot || 0} ${w / 2} ${h / 2})` }, parent);
      const inner = el("g", {}, g);
      const id = "tp" + clipN++;
      const pts = s.torn === false ? `0,0 ${w},0 ${w},${h} 0,${h}` : tornPts(w, h, s.amp || 7, s.step || 14, s.seed || clipN * 7);
      const cp = el("clipPath", { id }, defs);
      el("polygon", { points: pts }, cp);
      const body = el("g", { filter: "url(#shPaper)" }, inner);
      el("polygon", { points: pts, fill: s.fill || "#efe5cf" }, body);
      if (s.tex !== false) el("image", { href: "assets/tex/paper.png", x: -20, y: -20, width: w + 40, height: h + 40, preserveAspectRatio: "none", "clip-path": `url(#${id})`, opacity: s.texOp ?? 1, style: s.blend ? "mix-blend-mode:multiply" : "" }, inner);
      if (s.grid) el("rect", { x: 0, y: 0, width: w, height: h, fill: `url(#${s.grid})`, "clip-path": `url(#${id})` }, inner);
      const c = el("g", {}, inner);
      return { g, inner, c, w, h, x, y };
    }
    function pin(parent, x, y, kind = "deco", col = NAVY) {
      const p = el("g", { transform: `translate(${x} ${y})` }, parent);
      const s = el("g", { filter: "url(#shPin)" }, p);
      if (kind === "ring") {
        el("circle", { cx: 0, cy: 0, r: 22, fill: "#efe5cf", stroke: "#8b857c", "stroke-width": 7 }, s);
        el("ellipse", { cx: -7, cy: -8, rx: 6, ry: 4, fill: "#fff", opacity: 0.7 }, s);
      } else if (kind === "res") {
        el("circle", { cx: 0, cy: 0, r: 19, fill: RED, stroke: "#5e0f0d", "stroke-width": 3 }, s);
        el("ellipse", { cx: -6, cy: -7, rx: 6, ry: 4, fill: "#fff", opacity: 0.45 }, s);
      } else {
        el("circle", { cx: 0, cy: 0, r: 13, fill: col, stroke: "#1a1410", "stroke-width": 2.5 }, s);
        el("ellipse", { cx: -4, cy: -5, rx: 4, ry: 2.6, fill: "#fff", opacity: 0.5 }, s);
      }
      return { o: p, s };
    }
    function thread(parent, d, col = "#3a2f28", w = 4.5) {
      const g = el("g", {}, parent);
      const base = el("path", { d, fill: "none", stroke: col, "stroke-width": w, "stroke-linecap": "round" }, g);
      const tw = el("path", { d, fill: "none", stroke: "#fff", "stroke-opacity": 0.22, "stroke-width": w * 0.45, "stroke-dasharray": "3 7", "stroke-linecap": "round" }, g);
      return { g, base, tw };
    }
    // lined index card
    function card(parent, x, y, w, h, rot, seed, fill = "#f7f1e1") {
      const c = sheet(parent, x, y, w, h, { torn: false, rot, fill, texOp: 0.7, blend: true, seed });
      el("line", { x1: 0, y1: 40, x2: w, y2: 40, stroke: "#c45a55", "stroke-opacity": 0.6, "stroke-width": 2.5 }, c.c);
      for (let ly = 80; ly < h; ly += 38) el("line", { x1: 0, y1: ly, x2: w, y2: ly, stroke: "#4a76a8", "stroke-opacity": 0.2, "stroke-width": 2 }, c.c);
      return c;
    }
    // a pinned note with one or two lines of text
    function note(parent, x, y, w, h, rot, lines, s = {}) {
      const n = sheet(parent, x, y, w, h, { torn: s.torn ? undefined : false, seed: s.seed || 5, rot, fill: s.fill || "#e3cf86", texOp: 0.6, blend: true, amp: 5, step: 12 });
      const fs = s.fs || [44, 50];
      lines.forEach((l, i) => txt(l, { x: s.cx ? w / 2 : 30, y: (s.y0 || 72) + i * (fs[1] + 12), "font-size": fs[Math.min(i, 1)], "font-weight": i === lines.length - 1 && lines.length > 1 ? 700 : s.bold ? 700 : 400, fill: s.col || INK, "text-anchor": s.cx ? "middle" : "start" }, n.c));
      if (s.pin !== false) pin(n.inner, s.pinX ?? w / 2, 18, "deco", s.pinCol || RED);
      return n;
    }
    // rubber stamp (rectangle + Rustic text) — animate .i
    function stamp(parent, x, y, text, s = {}) {
      const g = el("g", { transform: `translate(${x} ${y}) rotate(${s.rot ?? -6})`, opacity: 0 }, parent);
      const i = el("g", {}, g);
      const fs = s.fs || 56, w = s.w || text.length * fs * 0.62 + 60, h = fs * 1.5, col = s.col || RED;
      if (s.box !== false) {
        el("rect", { x: -w / 2, y: -h / 2 - fs * 0.12, width: w, height: h, fill: "none", stroke: col, "stroke-width": Math.max(5, fs / 9) }, i);
        el("rect", { x: -w / 2 + 9, y: -h / 2 - fs * 0.12 + 9, width: w - 18, height: h - 18, fill: "none", stroke: col, "stroke-width": 2, opacity: 0.7 }, i);
      }
      txt(text, { x: 0, y: fs * 0.36, "font-size": fs, fill: col, "text-anchor": "middle", class: "rus", opacity: 0.92 }, i);
      return { g, i };
    }

    // ── frame, title strip, case tag, act tag ──
    const fr = L.frame;
    [[0, 0, BW, 34], [0, BH - 34, BW, 34], [0, 0, 34, BH], [BW - 34, 0, 34, BH]].forEach(([x, y, w, h]) => el("rect", { x, y, width: w, height: h, fill: "#4a2f1b" }, fr));
    el("rect", { x: 17, y: 17, width: BW - 34, height: BH - 34, fill: "none", stroke: "#76502f", "stroke-width": 6 }, fr);
    el("rect", { x: 34, y: 34, width: BW - 68, height: BH - 68, fill: "none", stroke: "#22150b", "stroke-width": 5, opacity: 0.8 }, fr);
    const titleS = sheet(L.papers, 720, 62, 1440, 112, { seed: 23, amp: 7, step: 12 });
    txt(o.title, { x: 720, y: 80, "font-size": o.titleSize || 60, fill: RED, "text-anchor": "middle", class: "rus" }, titleS.c);
    pin(L.papers, 760, 92, "deco", RED); pin(L.papers, 2120, 92, "deco", RED);
    const tagCase = el("g", { transform: "translate(110 70) rotate(-4)" }, L.papers);
    el("rect", { x: 0, y: 0, width: 300, height: 84, fill: "#d9c9a3", filter: "url(#shPaper)" }, tagCase);
    txt("BERKAS 734", { x: 150, y: 58, "font-size": 46, fill: INK, "text-anchor": "middle", class: "rus" }, tagCase);
    const tagAct = el("g", { transform: "translate(2410 78) rotate(-3)" }, L.papers);
    el("rect", { x: 0, y: 0, width: 400, height: 78, fill: INK, filter: "url(#shPaper)" }, tagAct);
    el("rect", { x: 7, y: 7, width: 386, height: 64, fill: "none", stroke: "#efe5cf", "stroke-opacity": 0.55, "stroke-width": 2 }, tagAct);
    txt(o.act, { x: 200, y: 53, "font-size": 38, fill: "#efe5cf", "text-anchor": "middle", class: "rus" }, tagAct);

    // ── camera ──
    const cam = (fx, fy, s) => { let x = 960 - fx * s, y = 540 - fy * s; x = Math.min(0, Math.max(1920 - BW * s, x)); y = Math.min(0, Math.max(1080 - BH * s, y)); return { x, y, scale: s }; };
    const WIDE = cam(1440, 810, 0.6667);
    const camTo = (t, fx, fy, s, d = 1.2, ease = "power3.inOut") => tl.to("#bcam", { ...cam(fx, fy, s), duration: d, ease }, t);
    const camSet = (t, fx, fy, s) => tl.set("#bcam", cam(fx, fy, s), t);

    // ── motion helpers ──
    let maskN = 0;
    function drawIn(path, t, d, ease = "power2.out") {
      const len = path.getTotalLength();
      if (path.getAttribute("stroke-dasharray")) {
        const clone = path.cloneNode(); clone.removeAttribute("stroke-dasharray"); clone.removeAttribute("opacity"); clone.removeAttribute("mask");
        clone.setAttribute("stroke", "#fff"); clone.setAttribute("stroke-width", (+path.getAttribute("stroke-width") || 3) + 12);
        const m = el("mask", { id: "dm" + maskN++, maskUnits: "userSpaceOnUse", x: -200, y: -200, width: BW + 400, height: BH + 400 }, defs);
        m.appendChild(clone);
        path.setAttribute("mask", `url(#${m.id})`);
        clone.style.strokeDasharray = len; clone.style.strokeDashoffset = len;
        tl.to(clone, { strokeDashoffset: 0, duration: d, ease }, t);
      } else {
        path.style.strokeDasharray = len; path.style.strokeDashoffset = len;
        tl.to(path, { strokeDashoffset: 0, duration: d, ease }, t);
      }
    }
    const drawThread = (th, t, d, ease) => { tl.set(th.g, { opacity: 1 }, t); drawIn(th.base, t, d, ease); tl.fromTo(th.tw, { opacity: 0 }, { opacity: 1, duration: 0.2 }, t + d); };
    const slap = (g, t, from = 1.55, rot = 6, d = 0.34) => tl.fromTo(g, { opacity: 0, scale: from, rotation: rot, transformOrigin: "50% 50%" }, { opacity: 1, scale: 1, rotation: 0, duration: d, ease: "expo.out" }, t);
    const pinIn = (p, t) => {
      tl.fromTo(p.s, { opacity: 0, scale: 2.4, transformOrigin: "50% 50%" }, { opacity: 1, scale: 1, duration: 0.26, ease: "power4.out" }, t);
      tl.to(p.s, { scaleX: 1.12, scaleY: 0.9, duration: 0.05, ease: "power1.out" }, t + 0.26);
      tl.to(p.s, { scaleX: 1, scaleY: 1, duration: 0.12, ease: "power2.out" }, t + 0.31);
    };
    const stampIn = (st, t) => { tl.set(st.g, { opacity: 1 }, t); tl.fromTo(st.i, { scale: 1.9, opacity: 0, transformOrigin: "50% 50%" }, { scale: 1, opacity: 1, duration: 0.28, ease: "power4.out" }, t); };
    const fadeIn = (g, t, d = 0.4, dy = 12) => tl.fromTo(g, { opacity: 0, y: dy }, { opacity: 1, y: 0, duration: d, ease: "expo.out" }, t);
    const hide = (g, t, d = 0.4) => tl.to(g, { opacity: 0, duration: d }, t);
    const hideAtStart = (...gs) => tl.set(gs, { opacity: 0 }, 0);
    // a horizontal bar that grows (no number count-up)
    const grow = (rect, w, t, d = 0.9) => tl.fromTo(rect, { attr: { width: 0 } }, { attr: { width: w }, duration: d, ease: "power3.out" }, t);

    // ── magnifier with Pak Anton's hand (screen space, in #lensFx) ──
    function lens(R = 430, cx = 960, cy = 540) {
      const g = $("#lens"), LC = [cx, cy], SO = `${cx} ${cy}`;
      $("#holeC").setAttribute("r", R);
      const hA = rad(42), hx = LC[0] + Math.cos(hA) * (R + 10), hy = LC[1] + Math.sin(hA) * (R + 10);
      el("path", { d: `M${f1(hx)},${f1(hy)} L${f1(hx + Math.cos(hA) * 420)},${f1(hy + Math.sin(hA) * 420)}`, stroke: INK, "stroke-width": 64, "stroke-linecap": "round" }, g);
      el("path", { d: `M${f1(hx)},${f1(hy)} L${f1(hx + Math.cos(hA) * 420)},${f1(hy + Math.sin(hA) * 420)}`, stroke: "#6b4a2c", "stroke-width": 54, "stroke-linecap": "round" }, g);
      el("circle", { cx: LC[0], cy: LC[1], r: R, fill: "url(#glass)" }, g);
      el("circle", { cx: LC[0], cy: LC[1], r: R + 14, fill: "none", stroke: INK, "stroke-width": 40 }, g);
      el("circle", { cx: LC[0], cy: LC[1], r: R + 14, fill: "none", stroke: "#a98a4f", "stroke-width": 30 }, g);
      el("circle", { cx: LC[0], cy: LC[1], r: R + 22, fill: "none", stroke: "#d8bd7c", "stroke-width": 5, opacity: 0.8 }, g);
      el("path", { d: `M${LC[0] - R * 0.7},${LC[1] - R * 0.42} A${R - 40},${R - 40} 0 0 1 ${LC[0] - R * 0.25},${LC[1] - R * 0.85}`, fill: "none", stroke: "#fff", "stroke-width": 14, "stroke-linecap": "round", opacity: 0.28 }, g);
      const gx = hx + Math.cos(hA) * 250, gy = hy + Math.sin(hA) * 250;
      el("path", { d: `M${f1(gx + 30)},${f1(gy + 50)} L${f1(gx + 420)},${f1(gy + 260)}`, stroke: INK, "stroke-width": 128, "stroke-linecap": "round" }, g);
      el("path", { d: `M${f1(gx + 30)},${f1(gy + 50)} L${f1(gx + 420)},${f1(gy + 260)}`, stroke: "#6b7541", "stroke-width": 120, "stroke-linecap": "round" }, g);
      el("path", { d: `M${f1(gx + 40)},${f1(gy + 6)} L${f1(gx + 60)},${f1(gy + 104)}`, stroke: "#525b31", "stroke-width": 16, "stroke-linecap": "round" }, g);
      el("ellipse", { cx: f1(gx), cy: f1(gy), rx: 74, ry: 56, fill: "#c98a5e", stroke: INK, "stroke-width": 5, transform: `rotate(42 ${f1(gx)} ${f1(gy)})` }, g);
      [-30, -6, 18].forEach((q) => el("path", { d: `M${f1(gx - 40 + q * 0.6)},${f1(gy - 26 + q)} q26,-10 48,8`, fill: "none", stroke: INK, "stroke-width": 4, "stroke-linecap": "round", opacity: 0.7 }, g));
      el("ellipse", { cx: f1(gx - 52), cy: f1(gy - 30), rx: 26, ry: 18, fill: "#c98a5e", stroke: INK, "stroke-width": 4.5, transform: `rotate(-20 ${f1(gx - 52)} ${f1(gy - 30)})` }, g);
      tl.set(g, { opacity: 0 }, 0);
      return {
        in(t) {
          tl.set(g, { opacity: 1 }, t);
          tl.fromTo(g, { x: 760, y: 720, rotation: 8, svgOrigin: SO }, { x: 0, y: 0, rotation: 0, duration: 0.85, ease: "expo.out" }, t);
          tl.fromTo("#holeC", { attr: { cx: cx + 760, cy: cy + 720 } }, { attr: { cx, cy }, duration: 0.85, ease: "expo.out" }, t);
          tl.fromTo("#lensDark", { opacity: 0 }, { opacity: 0.62, duration: 0.6 }, t + 0.05);
        },
        hold(t, d) {
          const n = Math.max(1, Math.floor(d / 2.6));
          tl.to(g, { x: -6, y: 5, rotation: -0.6, duration: d / (n * 2), ease: "sine.inOut", yoyo: true, repeat: n * 2 - 1, svgOrigin: SO }, t);
          tl.to("#holeC", { attr: { cx: cx - 6, cy: cy + 5 }, duration: d / (n * 2), ease: "sine.inOut", yoyo: true, repeat: n * 2 - 1 }, t);
        },
        out(t) {
          tl.to(g, { x: 900, y: 760, rotation: 10, duration: 0.55, ease: "power2.in", svgOrigin: SO }, t);
          tl.to("#holeC", { attr: { cx: cx + 900, cy: cy + 760 }, duration: 0.55, ease: "power2.in" }, t);
          tl.to("#lensDark", { opacity: 0, duration: 0.5 }, t + 0.05);
          tl.set(g, { opacity: 0 }, t + 0.56);
        },
      };
    }

    // ── ambient: dust motes + moving grain ──
    const rd = rng(42), dust = $("#dust");
    for (let i = 0; i < 26; i++) {
      const m = document.createElement("div"); m.className = "mote";
      const sz = 2 + rd() * 4; m.style.width = m.style.height = sz.toFixed(1) + "px";
      m.style.left = (rd() * 1920).toFixed(0) + "px"; m.style.top = (120 + rd() * 900).toFixed(0) + "px"; m.style.opacity = (0.18 + rd() * 0.35).toFixed(2);
      dust.appendChild(m);
      tl.fromTo(m, { x: 0, y: 0 }, { x: (rd() - 0.5) * 220, y: -(140 + rd() * 260), duration: DUR, ease: "none" }, 0);
    }
    tl.fromTo("#grain", { x: 0, y: 0 }, { x: -60, y: -60, duration: DUR, ease: `steps(${Math.round(DUR * 15)})` }, 0);

    function register(id = "main") {
      tl.set({}, {}, DUR); // pin the root length
      window.SCENE_TL = tl; // index.html registers it on window.__timelines
    }

    return { tl, L, defs, BW, BH, sheet, pin, thread, card, note, stamp, cam, WIDE, camTo, camSet, drawIn, drawThread, slap, pinIn, stampIn, fadeIn, hide, hideAtStart, grow, lens, register };
  }

  window.BOARD = { make, el, txt, rng, f1, rad, INK, RED, NAVY, GOLD, GREY };
})();

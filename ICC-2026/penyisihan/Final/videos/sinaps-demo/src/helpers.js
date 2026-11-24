  // ---- helper bersama (disisipkan tools/build.mjs) ----
  // T0 = waktu nominal mulai frame di timeline lokal (0,5 dtk pertama dipakai transisi masuk)
  const ID = "__ID__", T0 = __T0__, DUR = __DUR__, VO_AT = __VOAT__, VOW = __VOW__;
  const END = T0 + DUR;
  const R = document.getElementById(ID);
  const S = R.querySelector(".scene");
  const $ = (q) => R.querySelectorAll(q);
  const $1 = (q) => R.querySelector(q);
  const tl = gsap.timeline({ paused: true, defaults: { ease: "expo.out", duration: 0.55 } });
  // selector string GSAP dicari di seluruh halaman gabungan; batasi ke frame ini
  const scope = (t) => (typeof t === "string" ? R.querySelectorAll(t) : t);
  // tanpa pantulan: back/elastic/bounce diganti kurva yang mendarat lalu diam (masuk = expo.out, keluar = power3.in)
  const calm = (v) => {
    if (v && typeof v === "object" && typeof v.ease === "string" && /back|elastic|bounce/.test(v.ease))
      v.ease = /\.in\b|\.in\(/.test(v.ease) && !/inOut/.test(v.ease) ? "power3.in" : /inOut/.test(v.ease) ? "power3.inOut" : "expo.out";
    return v;
  };
  for (const m of ["to", "from", "fromTo", "set"]) {
    const orig = tl[m].bind(tl);
    tl[m] = (t, ...a) => orig(scope(t), ...a.map(calm));
  }
  // waktu (lokal) kata ke-n di voiceover frame ini yang cocok dengan pola
  const w = (pat, n = 1) => {
    const re = new RegExp(pat, "i");
    let c = 0;
    for (const [t, s] of VOW) if (re.test(t) && ++c === n) return T0 + VO_AT + s;
    throw new Error(`${ID}: kata "${pat}" (#${n}) tidak ada di VO`);
  };
  const fmtID = (v, dec = 0) => {
    const [i, f] = v.toFixed(dec).split(".");
    return i.replace(/\B(?=(\d{3})+(?!\d))/g, ".") + (f ? "," + f : "");
  };
  // transisi masuk. Satu tata bahasa untuk seluruh film: "push" (kamera geser, adegan lama mundur ke kiri),
  // "cut" (potong keras, untuk pergantian babak) dan "zoom" (sekali, masuk ke logo). Jenis lama dipetakan ke push.
  const enter = (kind, x = 960, y = 540) => {
    if (kind === "none" || kind === "cut" || T0 === 0) return;
    if (!["push", "zoom"].includes(kind)) kind = "push";
    const d = 0.62;
    if (kind === "iris") {
      const ns = "http://www.w3.org/2000/svg";
      const svg = document.createElementNS(ns, "svg");
      svg.setAttribute("viewBox", "0 0 1920 1080");
      Object.assign(svg.style, { position: "absolute", inset: "0", width: "100%", height: "100%", pointerEvents: "none", zIndex: 50 });
      const ring = document.createElementNS(ns, "circle");
      ring.setAttribute("cx", x); ring.setAttribute("cy", y); ring.setAttribute("r", 0);
      ring.setAttribute("fill", "none"); ring.setAttribute("stroke", "#e07a1f"); ring.setAttribute("stroke-width", "14");
      svg.appendChild(ring);
      const dot = document.createElementNS(ns, "circle");
      dot.setAttribute("cx", x); dot.setAttribute("cy", y); dot.setAttribute("r", 0); dot.setAttribute("fill", "#f09a6c");
      svg.appendChild(dot);
      R.appendChild(svg);
      tl.fromTo(dot, { attr: { r: 0 } }, { attr: { r: 26 }, duration: 0.14, ease: "back.out(3)" }, 0);
      tl.to(dot, { attr: { r: 0 }, duration: 0.18, ease: "power2.in" }, 0.16);
      tl.fromTo(S, { clipPath: `circle(0px at ${x}px ${y}px)` }, { clipPath: `circle(2300px at ${x}px ${y}px)`, duration: d, ease: "power3.inOut" }, 0.1);
      tl.fromTo(ring, { attr: { r: 0 }, opacity: 1 }, { attr: { r: 2300 }, duration: d, ease: "power3.inOut" }, 0.1);
      tl.set(S, { clipPath: "none" }, 0.1 + d);
      tl.set(svg, { opacity: 0 }, 0.1 + d);
    } else if (kind === "push") {
      tl.fromTo(S, { x: 1920, boxShadow: "-30px 0 60px rgba(16,24,40,.16)" }, { x: 0, duration: d, ease: "power4.inOut" }, 0);
      tl.set(S, { boxShadow: "none" }, d);
    } else if (kind === "fade") {
      tl.fromTo(S, { opacity: 0, scale: 1.04, filter: "blur(10px)" }, { opacity: 1, scale: 1, filter: "blur(0px)", duration: d, ease: "sine.inOut" }, 0);
      tl.set(S, { filter: "none" }, d);
    } else if (kind === "bars") {
      // lima batang warna merek naik menutup layar, lalu terus naik membuka adegan baru
      const ov = overlay(52);
      const bs = ["#195764", "#e07a1f", "#aad39c", "#0f3a43", "#f09a6c"].map((c, i) => div(ov, { position: "absolute", top: "0", bottom: "0", left: `${i * 20}%`, width: "20.3%", background: c }));
      tl.set(S, { opacity: 0 }, 0);
      tl.fromTo(bs, { scaleY: 0, transformOrigin: "50% 100%" }, { scaleY: 1, duration: 0.26, ease: "power3.in", stagger: 0.035 }, 0);
      tl.set(S, { opacity: 1 }, 0.42);
      tl.to(bs, { scaleY: 0, transformOrigin: "50% 0%", duration: 0.32, ease: "power3.out", stagger: 0.035 }, 0.43);
      tl.set(ov, { display: "none" }, 0.95);
    } else if (kind === "zoom") {
      tl.fromTo(S, { opacity: 0, scale: 1.55, filter: "blur(18px)" }, { opacity: 1, scale: 1, filter: "blur(0px)", duration: 0.55, ease: "expo.out" }, 0.02);
      tl.set(S, { filter: "none" }, 0.6);
    } else if (kind === "whip") {
      tl.fromTo(S, { x: 1500, skewX: -10, filter: "blur(34px)" }, { x: 0, skewX: 0, filter: "blur(0px)", duration: 0.5, ease: "expo.out" }, 0);
      tl.set(S, { filter: "none" }, 0.52);
    } else if (kind === "slideup") {
      const ov = overlay(52);
      const p = div(ov, { position: "absolute", left: "0", right: "0", top: "0", height: "1080px", background: "#e07a1f" });
      tl.fromTo(p, { y: 1080 }, { y: -1080, duration: 0.62, ease: "power3.inOut" }, 0);
      tl.fromTo(S, { y: 1080 }, { y: 0, duration: 0.55, ease: "power4.inOut" }, 0.07);
      tl.set(ov, { display: "none" }, 0.7);
    } else if (kind === "glitch") {
      const ov = overlay(52);
      const strips = [0.12, 0.27, 0.41, 0.58, 0.7, 0.86].map((yy, i) => div(ov, { position: "absolute", left: "0", right: "0", top: `${yy * 100}%`, height: `${16 + (i % 3) * 22}px`, background: i % 2 ? "rgba(37,200,230,.75)" : "rgba(220,38,38,.75)", mixBlendMode: "multiply" }));
      tl.fromTo(S, { opacity: 0 }, { opacity: 1, duration: 0.4, ease: "steps(5)" }, 0);
      tl.fromTo(S, { x: -60, skewX: 16 }, { x: 0, skewX: 0, duration: 0.45, ease: "steps(6)" }, 0);
      strips.forEach((st, i) => tl.fromTo(st, { opacity: 0, x: (i % 2 ? 1 : -1) * 120 }, { opacity: 1, x: 0, duration: 0.05, yoyo: true, repeat: 7, ease: "steps(1)" }, i * 0.02));
      tl.set(ov, { display: "none" }, 0.6);
    }
  };
  // keluar: hanya saat frame berikutnya sedang masuk di atasnya (bukan exit sendiri)
  const leave = () => {
    tl.to(S, { x: -480, duration: 0.62, ease: "power4.inOut" }, END - 0.5);
  };
  const blinkAt = (lids, times) => times.forEach((t) => {
    tl.to(lids, { scaleY: 1, duration: 0.07, ease: "none", transformOrigin: "50% 50%" }, t);
    tl.to(lids, { scaleY: 0, duration: 0.09, ease: "none" }, t + 0.1);
  });
  // kedip manual tidak dipakai lagi: semua tokoh berkedip otomatis (lihat akhir helper)
  const blink = () => {};
  // gerak idle naik-turun yang terbatas (yoyo dengan repeat terhitung)
  const bob = (sel, from, to, amp = 8, per = 1.6, prop = "y") => {
    const n = Math.max(1, Math.floor((to - from) / (per / 2)) - 1);
    tl.fromTo(sel, { [prop]: 0 }, { [prop]: -amp, duration: per / 2, ease: "sine.inOut", yoyo: true, repeat: n }, from);
  };
  // masuk: sebagian besar gerak di beberapa frame pertama lalu ekor panjang, tanpa pantulan; tidak tumbuh dari nol
  const pop = (sel, t, o = {}) => tl.fromTo(sel, { scale: Math.max(0.82, o.from ?? 0.86), opacity: 0, transformOrigin: o.origin ?? "50% 50%" }, { scale: 1, opacity: 1, duration: o.d ?? 0.5, ease: o.ease ?? "expo.out", stagger: o.stagger ?? 0 }, t);
  const rise = (sel, t, o = {}) => tl.fromTo(sel, { y: o.y ?? 32, opacity: 0 }, { y: 0, opacity: 1, duration: o.d ?? 0.55, ease: o.ease ?? "expo.out", stagger: o.stagger ?? 0.06 }, t);
  const slideIn = (sel, t, o = {}) => tl.fromTo(sel, { x: o.x ?? -60, opacity: 0 }, { x: 0, opacity: 1, duration: o.d ?? 0.55, ease: o.ease ?? "expo.out", stagger: o.stagger ?? 0.06 }, t);
  const count = (el, from, to, t, d, o = {}) => {
    const p = { v: from };
    const put = () => { el.textContent = (o.pre ?? "") + fmtID(p.v, o.dec ?? 0) + (o.suf ?? ""); };
    tl.fromTo(p, { v: from }, { v: to, duration: d, ease: o.ease ?? "power2.out", onUpdate: put, onStart: put }, t);
    tl.set({}, { onComplete: put }, t + d);
  };
  const drawPath = (el, t, d, o = {}) => {
    const len = el.getTotalLength ? el.getTotalLength() : 1000;
    tl.fromTo(el, { strokeDasharray: len, strokeDashoffset: len }, { strokeDashoffset: 0, duration: d, ease: o.ease ?? "power2.inOut" }, t);
  };
  const typeText = (el, text, t, cps = 28) => {
    const p = { n: 0 };
    tl.fromTo(p, { n: 0 }, { n: text.length, duration: text.length / cps, ease: "none", onUpdate: () => { el.textContent = text.slice(0, Math.round(p.n)); } }, t);
  };
  const scaleBar = (sel, t, o = {}) => tl.fromTo(sel, { scaleX: 0, transformOrigin: "0% 50%" }, { scaleX: 1, duration: o.d ?? 0.9, ease: o.ease ?? "power3.out", stagger: o.stagger ?? 0.1 }, t);
  // ---- motion v2: latar hidup, kamera, efek benturan, teks kinetik ----
  const NS = "http://www.w3.org/2000/svg";
  const D = R.querySelector(".dolly") || S; // kamera frame (drift/shake), di dalam .scene
  let fxSeed = [...ID].reduce((a, c) => (a * 31 + c.charCodeAt(0)) >>> 0, 977);
  const frnd = () => ((fxSeed = (fxSeed * 1664525 + 1013904223) >>> 0) / 4294967296);
  const svgEl = (tag, attrs, parent) => {
    const e = document.createElementNS(NS, tag);
    for (const k in attrs) e.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(e);
    return e;
  };
  const div = (parent, style = {}, cls) => {
    const e = document.createElement("div");
    if (cls) e.className = cls;
    Object.assign(e.style, style);
    parent.appendChild(e);
    return e;
  };
  // lapisan di atas .scene (dipakai transisi)
  const overlay = (z) => div(R, { position: "absolute", inset: "0", zIndex: z, pointerEvents: "none" });
  const FX = div(D, {}, "fx");
  const fxSvg = () => svgEl("svg", { viewBox: "0 0 1920 1080" }, FX);

  // latar: permukaan kertas hangat yang diam (cahaya lembut di tengah, vinyet tipis, butir kertas).
  // Sengaja tidak bergerak: saat jeda presenter bicara, yang hidup hanya tokohnya.
  const ground = () => {
    const g = div(D, {}, "ground");
    D.insertBefore(g, D.firstChild);
    return g;
  };
  // (lama) kamera merayap sepanjang frame — dimatikan: jeda harus tenang
  const drift = () => {};
  // hentakan kecil sekali pakai (stempel mendarat): dua ayunan pendek, bukan gempa
  const thud = (t, amp = 6) => {
    tl.to(D, { y: amp, duration: 0.05, ease: "power2.out" }, t);
    tl.to(D, { y: 0, duration: 0.28, ease: "power3.out" }, t + 0.05);
  };
  // guncangan/burst/kilat/konfeti/stabilo: efek "AI default" — sekarang tidak menggambar apa pun
  const shake = () => {};
  const burst = () => {};
  const flash = () => {};
  const confetti = () => {};
  const mark = () => {};
  const hit = () => {};
  // kartu judul babak: dua panel menyapu, kata raksasa membanting, lalu menyapu keluar
  const bumper = (word, t, o = {}) => {
    const b = div(S, {}, "bump");
    const cols = o.cols ?? ["#e07a1f", "#195764"];
    const p1 = div(b, { background: cols[0] }, "bp"), p2 = div(b, { background: cols[1] }, "bp");
    const bw = div(b, {}, "bw"); bw.textContent = word;
    const bs = o.sub ? div(b, {}, "bs") : null; if (bs) bs.textContent = o.sub;
    const hold = o.hold ?? 0.8;
    tl.fromTo(p1, { clipPath: "inset(0 100% 0 0)" }, { clipPath: "inset(0 0% 0 0)", duration: 0.28, ease: "power4.inOut" }, t);
    tl.fromTo(p2, { clipPath: "inset(0 100% 0 0)" }, { clipPath: "inset(0 0% 0 0)", duration: 0.28, ease: "power4.inOut" }, t + 0.08);
    tl.fromTo(bw, { scale: 1.6, scaleX: 2.1, opacity: 0 }, { scale: 1, scaleX: 1, opacity: 1, duration: 0.42, ease: "expo.out" }, t + 0.2);
    if (bs) tl.fromTo(bs, { y: 30, opacity: 0 }, { y: 0, opacity: 1, duration: 0.35 }, t + 0.32);
    tl.to(bw, { scale: 1.07, duration: hold, ease: "none" }, t + 0.62);
    const out = t + 0.32 + hold;
    tl.to(bs ? [bw, bs] : bw, { opacity: 0, y: -50, duration: 0.2, ease: "power2.in" }, out);
    tl.to(p2, { clipPath: "inset(0 0 0 100%)", duration: 0.3, ease: "power4.inOut" }, out + 0.1);
    tl.to(p1, { clipPath: "inset(0 0 0 100%)", duration: 0.3, ease: "power4.inOut" }, out + 0.18);
    tl.set(b, { display: "none" }, out + 0.5);
    return out + 0.4;
  };
  // pecah teks jadi kata (tag <b>/<em> di dalamnya dipertahankan) lalu muncul berjenjang
  const splitWords = (el) => {
    const walk = (node) => [...node.childNodes].forEach((c) => {
      if (c.nodeType === 3) {
        const frag = document.createDocumentFragment();
        c.textContent.split(/(\s+)/).forEach((part) => {
          if (!part) return;
          if (/^\s+$/.test(part)) frag.appendChild(document.createTextNode(part));
          else { const s = document.createElement("span"); s.className = "wd"; s.style.display = "inline-block"; s.textContent = part; frag.appendChild(s); }
        });
        c.replaceWith(frag);
      } else if (c.nodeType === 1 && !c.classList.contains("wd")) walk(c);
    });
    walk(el);
    return [...el.querySelectorAll(".wd")];
  };
  const words = (sel, t, o = {}) => {
    const els = typeof sel === "string" ? [...R.querySelectorAll(sel)] : [sel].flat();
    els.forEach((el) => tl.fromTo(splitWords(el), { y: Math.min(o.y ?? 26, 30), opacity: 0 }, { y: 0, opacity: 1, duration: o.d ?? 0.5, ease: "expo.out", stagger: Math.min(o.stagger ?? 0.05, 0.06) }, t));
  };
  // kamera di dalam jendela rekaman: pusatkan titik (rx, ry) piksel rekaman 1920x1200 pada skala s
  const camTo = (el, rx, ry, s, t, d = 1.1, o = {}) => {
    const k = o.k ?? 0.71875, VW = o.vw ?? 1380, VH = o.vh ?? 862;
    const x = Math.min(0, Math.max(VW - VW * s, VW / 2 - rx * k * s)), y = Math.min(0, Math.max(VH - VH * s, VH / 2 - ry * k * s));
    tl.set(el, { transformOrigin: "0% 0%" }, 0);
    tl.to(el, { x, y, scale: s, duration: d, ease: o.ease ?? "power3.inOut" }, t);
    return { x, y, s };
  };
  if (R.dataset.amb !== "0") ground();
  // semua tokoh hidup saat jeda: kedip dengan jarak acak-tetap (berbiji) sampai akhir frame
  R.querySelectorAll("svg.dika, svg.sina").forEach((el, k) => {
    const lids = el.querySelectorAll(".dika-lid, .sina-lid");
    const ts = [];
    for (let t = 1.1 + k * 0.7 + frnd() * 0.8; t < END - 0.4; t += 2.8 + frnd() * 2.2) ts.push(+t.toFixed(2));
    blinkAt(lids, ts);
  });
  // ---- akhir helper ----

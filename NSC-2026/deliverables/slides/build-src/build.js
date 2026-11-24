// BERKAS 734 — deck generator (style: Black & Beige Grunge Crime Investigation Report)
const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const Lu = require("react-icons/lu");

const OUT = process.argv[2] || "deck.pptx";
const SCRIPT = process.argv[3];
const A = (k) => path.join(__dirname, "assets", k + (k === "bg" ? ".jpg" : ".png"));

// ---------- palette & fonts ----------
const INK = "191919", CHAR = "272727", IVORY = "F3EFDF", PAPER = "F5F1E4", BEIGE = "E3D6BC",
  TAN = "C4A57A", RED = "A71916", GRAY = "6F6A61", GREEN = "2B695E", MUTED = "B5AC9C";
const FONT = { H: "Rustic Printed Stamp", B: "Poppins Bold", P: "Poppins", L: "Poppins Light", G: "Gloria Hallelujah" };
// glyphs the template fonts lack -> fall back to Arial runs
const MISSING = { H: /[−≠→←↓Δ√≥²]/, B: /[→←↓Δ]/, P: /[→←↓Δ]/, L: /[→←↓Δ]/, G: /[≠→←↓Δ√≥]/ };

const pres = new pptxgen();
pres.defineLayout({ name: "CANVA", width: 20, height: 11.25 });
pres.layout = "CANVA";
pres.title = "Berkas 734 — The Missing Humidity Case";
pres.author = "Heisenberg";
pres.theme = { headFontFace: FONT.H, bodyFontFace: FONT.L };

// ---------- helpers ----------
function runs(text, f, base) {
  const re = MISSING[f];
  const out = [];
  let buf = "";
  for (const ch of text) {
    if (re.test(ch)) {
      if (buf) out.push({ text: buf, options: { ...base } });
      out.push({ text: ch, options: { ...base, fontFace: "Arial" } });
      buf = "";
    } else buf += ch;
  }
  if (buf) out.push({ text: buf, options: { ...base } });
  return out;
}
// txt(slide, text | [[text, {f,color,size,bold,breakLine}]...], opts)
function txt(s, text, o) {
  const f = o.f || "L";
  const base = { fontFace: FONT[f], fontSize: o.size || 16, color: o.color || CHAR };
  if (o.charSpacing) base.charSpacing = o.charSpacing;
  let content;
  if (Array.isArray(text)) {
    content = [];
    text.forEach(([t, ro = {}], i) => {
      const rf = ro.f || f;
      const rb = { fontFace: FONT[rf], fontSize: ro.size || base.fontSize, color: ro.color || base.color };
      if (ro.charSpacing) rb.charSpacing = ro.charSpacing;
      const r = runs(t, rf, rb);
      if (ro.breakLine) r[r.length - 1].options.breakLine = true;
      content.push(...r);
    });
  } else content = runs(text, f, base);
  const opts = {
    x: o.x, y: o.y, w: o.w, h: o.h, margin: o.margin ?? 0, align: o.align || "left",
    valign: o.valign || "top", isTextBox: true, rotate: o.rotate || 0, fit: "none",
    lineSpacingMultiple: o.lsm || 1.0, objectName: o.name,
  };
  if (o.paraSpaceAfter) opts.paraSpaceAfter = o.paraSpaceAfter;
  s.addText(content, opts);
}
function img(s, key, x, y, w, h, o = {}) {
  s.addImage({ path: A(key), x, y, w, h, rotate: o.rot || 0, flipH: !!o.flipH, flipV: !!o.flipV, transparency: o.tr || 0, altText: o.alt || key });
}
function bg(s) {
  s.background = { color: INK };
  s.addImage({ path: A("bg"), x: 0, y: 0, w: 20, h: 20, altText: "dark grunge texture" }); // square texture, cropped by slide edge
}
function shadow() { return { type: "outer", blur: 14, offset: 5, angle: 90, color: "000000", opacity: 0.5 }; }
function paper(s, x, y, w, h, o = {}) {
  s.addShape(pres.shapes.RECTANGLE, { x, y, w, h, fill: { color: o.fill || PAPER }, line: { type: "none" }, rotate: o.rot || 0, shadow: shadow() });
  if (o.tape !== false) {
    const tw = o.tapeW || 1.7;
    s.addShape(pres.shapes.RECTANGLE, { x: x + (o.tapeX ?? (w - tw) / 2), y: y - 0.22, w: tw, h: 0.48, fill: { color: "D9CBA6", transparency: 22 }, line: { type: "none" }, rotate: o.tapeRot ?? -4 });
  }
}
function rect(s, x, y, w, h, fill, o = {}) {
  s.addShape(o.round ? pres.shapes.ROUNDED_RECTANGLE : pres.shapes.RECTANGLE, {
    x, y, w, h, fill: fill ? { color: fill, transparency: o.tr || 0 } : { type: "none" },
    line: o.line ? { color: o.line, width: o.lw || 1.5, dashType: o.dash || "solid" } : { type: "none" },
    rectRadius: o.round ? o.round : undefined, rotate: o.rot || 0, shadow: o.shadow ? shadow() : undefined,
  });
}
function line(s, x1, y1, x2, y2, color, w = 1.5, o = {}) {
  if (o.end) return path_(s, [[x1, y1], [x2, y2]], color, w, o); // custGeom keeps the drawing direction for arrowheads
  s.addShape(pres.shapes.LINE, {
    x: Math.min(x1, x2), y: Math.min(y1, y2), w: Math.abs(x2 - x1) || 0.001, h: Math.abs(y2 - y1) || 0.001,
    flipH: x2 < x1 !== y2 < y1 && x2 !== x1 && y2 !== y1 ? true : false,
    line: { color, width: w, dashType: o.dash || "solid", beginArrowType: o.begin, endArrowType: o.end },
  });
}
function path_(s, pts, color, w = 2, o = {}) { // open polyline in absolute inches
  const xs = pts.map((p) => p[0]), ys = pts.map((p) => p[1]);
  const x0 = Math.min(...xs), y0 = Math.min(...ys);
  const W = Math.max(...xs) - x0 || 0.01, H = Math.max(...ys) - y0 || 0.01;
  s.addShape(pres.shapes.CUSTOM_GEOMETRY, {
    x: x0, y: y0, w: W, h: H, points: pts.map((p) => ({ x: p[0] - x0, y: p[1] - y0 })),
    line: { color, width: w, dashType: o.dash || "solid", endArrowType: o.end }, fill: { type: "none" },
  });
}
function dot(s, cx, cy, r, fill, o = {}) {
  s.addShape(pres.shapes.OVAL, { x: cx - r, y: cy - r, w: 2 * r, h: 2 * r, fill: fill ? { color: fill } : { type: "none" }, line: o.line ? { color: o.line, width: o.lw || 2 } : { type: "none" } });
}
function stamp(s, text, x, y, w, h, o = {}) {
  const c = o.color || RED;
  s.addShape(pres.shapes.RECTANGLE, { x, y, w, h, fill: { type: "none" }, line: { color: c, width: o.lw || 3.5 }, rotate: o.rot || 0 });
  txt(s, text, { x, y, w, h, f: "H", size: o.size || 26, color: c, align: "center", valign: "middle", rotate: o.rot || 0 });
}
function chrome(s, act, ex, dark = true) {
  const c = dark ? BEIGE : GRAY;
  txt(s, `CASE #734   ·   ${act}`, { x: 0.6, y: 0.34, w: 9, h: 0.32, f: "B", size: 12, color: c, charSpacing: 2 });
  txt(s, `EXHIBIT ${ex} / 14`, { x: 13.4, y: 0.34, w: 6, h: 0.32, f: "B", size: 12, color: c, charSpacing: 2, align: "right" });
}
function title(s, t, sub, o = {}) {
  txt(s, t, { x: o.x ?? 0.6, y: 0.74, w: o.w ?? 18.8, h: 1.0, f: "H", size: o.size || 60, color: o.color || IVORY });
  if (sub) txt(s, sub, { x: (o.x ?? 0.6) + 0.02, y: 1.72, w: o.w ?? 18.8, h: 0.5, f: "G", size: 20, color: o.subColor || BEIGE });
}
function footer(s, chips, prov, o = {}) {
  const y = 10.42;
  txt(s, o.label || "METHOD", { x: 0.6, y: y + 0.08, w: 3, h: 0.3, f: "B", size: 11, color: BEIGE, charSpacing: 2 });
  let x = 1.75;
  chips.forEach((c, i) => {
    if (c === "→") { txt(s, "→", { x, y, w: 0.4, h: 0.42, f: "B", size: 16, color: BEIGE, align: "center", valign: "middle" }); x += 0.5; return; }
    const w = c.length * 0.098 + 0.45;
    rect(s, x, y, w, 0.42, BEIGE);
    txt(s, c, { x, y, w, h: 0.42, f: "B", size: 12, color: INK, align: "center", valign: "middle" });
    x += w + 0.18;
  });
  if (prov) {
    const px = Math.max(x + 0.3, 11.2);
    txt(s, prov, { x: px, y: y - 0.14, w: 19.4 - px, h: 0.7, f: "L", size: 11, color: MUTED, align: "right", valign: "middle" });
  }
}
async function icon(Comp, color, px = 256) {
  const svg = ReactDOMServer.renderToStaticMarkup(React.createElement(Comp, { color: "#" + color, size: px, strokeWidth: 1.6 }));
  const buf = await sharp(Buffer.from(svg)).resize(px, px).png().toBuffer();
  return "image/png;base64," + buf.toString("base64");
}
async function ico(s, Comp, color, x, y, sz) { s.addImage({ data: await icon(Comp, color), x, y, w: sz, h: sz, altText: "icon" }); }
// horizontal bar chart drawn with shapes: linear, zero-based, dot-decimal labels (native charts follow the OS locale)
function hbars(s, rows, o) {
  const { x, y, w, labelW, vmin, vmax, ticks, fmt, barH = 0.7, gap = 0.35 } = o;
  const px0 = x + labelW, px1 = x + w, P = (v) => px0 + (px1 - px0) * (v - vmin) / (vmax - vmin);
  const y1 = y + rows.length * (barH + gap) + 0.05;
  ticks.forEach((t) => {
    line(s, P(t), y - 0.1, P(t), y1, "D8CFBC", 0.75);
    txt(s, fmt(t), { x: P(t) - 0.5, y: y1 + 0.06, w: 1, h: 0.3, f: "P", size: 12, color: GRAY, align: "center" });
  });
  line(s, P(0), y - 0.1, P(0), y1, INK, 1.75);
  rows.forEach(([lab, v, c, vlab], i) => {
    const by = y + i * (barH + gap) + gap / 2;
    txt(s, lab, { x, y: by, w: labelW - 0.25, h: barH, f: "B", size: 15, color: INK, align: "right", valign: "middle" });
    const a = Math.min(P(0), P(v)), bw = Math.abs(P(v) - P(0));
    rect(s, a, by, Math.max(bw, 0.02), barH, c);
    const lw = 1.4;
    txt(s, vlab, { x: v < 0 ? a - lw - 0.1 : a + bw + 0.1, y: by, w: lw, h: barH, f: "B", size: 18, color: INK, align: v < 0 ? "right" : "left", valign: "middle" });
  });
}
function wiggle(x0, x1, yc, amp, seed, n = 90) {
  const pts = [];
  for (let i = 0; i <= n; i++) {
    const t = i / n, x = x0 + (x1 - x0) * t;
    const v = 0.55 * Math.sin(t * 19 + seed) + 0.3 * Math.sin(t * 47 + seed * 2.3) + 0.15 * Math.sin(t * 101 + seed * 5.1);
    pts.push([x, yc + amp * v]);
  }
  return pts;
}

// ---------- speaker notes from script ----------
const notes = {};
if (SCRIPT && fs.existsSync(SCRIPT)) {
  const md = fs.readFileSync(SCRIPT, "utf8");
  const parts = md.split(/^### SLIDE (\d+)[^\n]*\n/m);
  for (let i = 1; i < parts.length; i += 2) {
    const n = +parts[i];
    let body = parts[i + 1].split(/\n---\s*\n/)[0];
    body = body.replace(/\*\*/g, "").replace(/^\*(.*)\*$/gm, "$1").replace(/\n{3,}/g, "\n\n").trim();
    notes[n] = body;
  }
}
function addNotes(s, n, extra) { s.addNotes([extra, notes[n]].filter(Boolean).join("\n\n")); }

// =====================================================================
async function build() {
  // ---------------- ACT I ----------------
  pres.addSection({ title: "Act I — The Mystery" });

  // SLIDE 01 — video slot (background only)
  {
    const s = pres.addSlide({ sectionTitle: "Act I — The Mystery" });
    bg(s);
    addNotes(s, 1, "[SLOT VIDEO — Slide 01 opening 15–20 dtk. Background saja; tempel MP4 '01_opening_case.mp4' full-bleed di slide ini, set Start: Automatically, freeze di frame akhir.]");
  }

  // SLIDE 02 — Entering the crime scene
  {
    const s = pres.addSlide({ sectionTitle: "Act I — The Mystery" });
    bg(s); chrome(s, "ACT I — THE MYSTERY", "02");
    title(s, "ENTERING THE CRIME SCENE", "One target missing. 24 channels remain.");
    img(s, "dashes", 17.9, 0.95, 0.95, 1.07, { rot: 10 });
    // hero logbook sheet
    paper(s, 0.6, 2.45, 18.8, 6.45, { tapeX: 1.0 });
    txt(s, "EVIDENCE 01: SENSOR LOG", { x: 1.1, y: 2.7, w: 6, h: 0.35, f: "B", size: 13, color: RED, charSpacing: 2 });
    txt(s, "Diagram skematis, tidak berskala", { x: 12.9, y: 2.7, w: 6.1, h: 0.35, f: "L", size: 12, color: GRAY, align: "right" });
    const X0 = 4.1, XD = 13.9, X1 = 18.8;
    txt(s, "TRAIN", { x: X0, y: 3.15, w: 5, h: 0.4, f: "H", size: 24, color: INK });
    txt(s, "PREDICTION WINDOW", { x: XD + 0.25, y: 3.15, w: 4.7, h: 0.4, f: "H", size: 24, color: RED });
    const lanes = [["Humidity (target)", RED], ["Temperature", INK], ["Pressure", INK], ["Other sensors", INK]];
    lanes.forEach(([lab, c], i) => {
      const yc = 4.25 + i * 1.12;
      txt(s, lab, { x: 1.1, y: yc - 0.2, w: 2.9, h: 0.4, f: "B", size: 15, color: c, valign: "middle" });
      line(s, X0, yc + 0.48, X1, yc + 0.48, "D8CFBC", 0.75);
      if (i === 0) {
        path_(s, wiggle(X0, XD - 0.1, yc, 0.32, 1.3), CHAR, 2.25);
        rect(s, XD + 0.2, yc - 0.42, X1 - XD - 0.3, 0.84, BEIGE);
        txt(s, "734 ?", { x: XD + 0.2, y: yc - 0.42, w: X1 - XD - 0.3, h: 0.84, f: "H", size: 34, color: RED, align: "center", valign: "middle" });
      } else {
        path_(s, wiggle(X0, X1, yc, 0.3, 2.1 + i * 1.7), i === 3 ? GRAY : CHAR, 1.75);
      }
    });
    line(s, XD, 3.15, XD, 8.55, RED, 2, { dash: "dash" });
    txt(s, "Can we reconstruct the missing values?", { x: 8.1, y: 8.12, w: 5.6, h: 0.5, f: "G", size: 18, color: RED, align: "right" });
    img(s, "arrowUp", 13.75, 7.55, 0.75, 0.88, { rot: 8 });
    // three numbers along bottom
    const nums = [["2,933", "TRAINING RECORDS"], ["734", "TARGET VALUES"], ["24", "EXOGENOUS CHANNELS"]];
    nums.forEach(([n, l], i) => {
      const x = 0.9 + i * 6.25;
      txt(s, n, { x, y: 9.12, w: 2.4, h: 0.9, f: "H", size: 52, color: i === 1 ? "E3B9A8" : IVORY, align: "right", valign: "middle" });
      txt(s, l, { x: x + 2.6, y: 9.12, w: 3.4, h: 0.9, f: "B", size: 15, color: BEIGE, valign: "middle", charSpacing: 1 });
    });
    footer(s, ["Multivariate Reconstruction", "15.3-Day Window"], "Data: laporan submission Heisenberg · NSC 2026");
    addNotes(s, 2);
  }

  // ---------------- ACT II ----------------
  pres.addSection({ title: "Act II — The Clues" });

  // SLIDE 03 — Contaminated evidence
  {
    const s = pres.addSlide({ sectionTitle: "Act II — The Clues" });
    bg(s); chrome(s, "ACT II — THE CLUES", "03");
    title(s, "CONTAMINATED EVIDENCE", "Clean unstable inputs selectively.");
    // left: grid paper with LOO mechanism
    img(s, "gridTape", 0.35, 2.25, 13.2, 6.46);
    const px0 = 1.5, py0 = 2.75;
    txt(s, "TEMPERATURE SENSOR · ONE POINT UNDER AUDIT", { x: 5.9, y: py0 + 0.12, w: 7, h: 0.35, f: "B", size: 13, color: RED, charSpacing: 1 });
    // axis baseline + ticks
    const bx0 = 2.0, bx1 = 11.8, by = 7.1;
    line(s, bx0, by, bx1, by, CHAR, 1.5);
    const tx = [3.3, 5.1, 6.9, 8.7, 10.5];
    ["t − 2", "t − 1", "t", "t + 1", "t + 2"].forEach((l, i) => {
      line(s, tx[i], by - 0.08, tx[i], by + 0.08, CHAR, 1.5);
      txt(s, l, { x: tx[i] - 0.6, y: by + 0.12, w: 1.2, h: 0.35, f: "B", size: 14, color: CHAR, align: "center" });
    });
    // quadratic through neighbours: y = a(x-6.9)^2 + c
    const qy = (x) => 6.1 - 0.055 * (x - 6.9) ** 2 + 0.05 * (x - 6.9);
    const curve = []; for (let x = 2.7; x <= 11.1; x += 0.1) curve.push([x, qy(x)]);
    path_(s, curve, GRAY, 2, { dash: "dash" });
    [0, 1, 3, 4].forEach((i) => dot(s, tx[i], qy(tx[i]), 0.17, PAPER, { line: CHAR, lw: 2.5 }));
    // estimate at t (filled ink diamond)
    s.addShape(pres.shapes.DIAMOND, { x: 6.9 - 0.2, y: qy(6.9) - 0.2, w: 0.4, h: 0.4, fill: { color: CHAR }, line: { type: "none" } });
    // observed spike (crimson)
    dot(s, 6.9, 3.85, 0.22, RED);
    line(s, 6.9, 4.08, 6.9, qy(6.9) - 0.22, RED, 2, { dash: "sysDot" });
    // residual bracket
    path_(s, [[7.25, 3.85], [7.45, 3.85], [7.45, qy(6.9)], [7.25, qy(6.9)]], RED, 2);
    txt(s, "residual", { x: 7.6, y: 4.6, w: 2, h: 0.5, f: "G", size: 20, color: RED });
    // legend
    const lgx = 9.4, lgy = 3.6;
    dot(s, lgx, lgy + 0.17, 0.11, PAPER, { line: CHAR, lw: 2 });
    txt(s, "4 neighbours (hidden point left out)", { x: lgx + 0.25, y: lgy, w: 3.4, h: 0.34, f: "L", size: 12, color: CHAR, valign: "middle" });
    s.addShape(pres.shapes.DIAMOND, { x: lgx - 0.12, y: lgy + 0.42, w: 0.24, h: 0.24, fill: { color: CHAR }, line: { type: "none" } });
    txt(s, "quadratic estimate", { x: lgx + 0.25, y: lgy + 0.37, w: 3.4, h: 0.34, f: "L", size: 12, color: CHAR, valign: "middle" });
    dot(s, lgx, lgy + 0.91, 0.12, RED);
    txt(s, "observed reading", { x: lgx + 0.25, y: lgy + 0.74, w: 3.4, h: 0.34, f: "L", size: 12, color: CHAR, valign: "middle" });
    txt(s, "Ilustrasi prosedur — tidak berskala", { x: 7.6, y: 7.62, w: 4.6, h: 0.3, f: "L", size: 11, color: GRAY, align: "right" });
    // right: audit ratios on beige clip paper
    img(s, "beigeClip", 13.75, 2.2, 5.85, 5.86);
    txt(s, "EXTREME-RESIDUAL RATIO", { x: 14.25, y: 2.85, w: 4.6, h: 0.35, f: "B", size: 15, color: INK });
    txt(s, "SD residual ÷ robust MAD scale · unitless", { x: 14.25, y: 3.22, w: 4.7, h: 0.3, f: "L", size: 11, color: GRAY });
    const rows = [["TEMP", "5.75", RED], ["PRESSURE", "6.86", RED], ["RH TARGET", "1.20", INK]];
    rows.forEach(([l, v, c], i) => {
      const y = 3.75 + i * 1.3;
      txt(s, l, { x: 14.25, y, w: 2.2, h: 1.0, f: "B", size: 16, color: CHAR, valign: "middle" });
      txt(s, v, { x: 16.3, y, w: 2.6, h: 1.0, f: "H", size: 58, color: c, align: "right", valign: "middle" });
      if (i < 2) line(s, 14.25, y + 1.15, 18.9, y + 1.15, "B9AD8C", 1, { dash: "dash" });
    });
    stamp(s, "INPUT NOISE CONFIRMED", 14.2, 8.45, 5.0, 0.85, { rot: -5, size: 24, color: "C9302C" });
    footer(s, ["Leave-One-Out Quadratic Interpolation", "Robust MAD", "Hampel Filter"], "Ilustrasi prosedur. Rasio dari laporan, Tabel I.");
    addNotes(s, 3);
  }

  // SLIDE 04 — The hidden clue
  {
    const s = pres.addSlide({ sectionTitle: "Act II — The Clues" });
    bg(s); chrome(s, "ACT II — THE CLUES", "04");
    title(s, "THE HIDDEN CLUE", "Hidden inside daily indices");
    // left: two notebook tearouts
    img(s, "tanNote", 0.55, 2.55, 6.6, 3.0);
    img(s, "tanNote2", 0.55, 5.95, 6.6, 3.0);
    [["PATH A", "Daily mean + max", 2.55], ["PATH B", "Ontario CHU index", 5.95]].forEach(([p, t, y]) => {
      txt(s, p, { x: 1.35, y: y + 0.7, w: 3, h: 0.35, f: "B", size: 14, color: RED, charSpacing: 2 });
      txt(s, t, { x: 1.35, y: y + 1.1, w: 5.1, h: 0.6, f: "H", size: 30, color: INK });
      txt(s, "inverse  →  reconstructed Tmin", { x: 1.35, y: y + 1.8, w: 5.3, h: 0.4, f: "P", size: 15, color: CHAR });
    });
    // arrows into seal
    path_(s, [[6.9, 4.1], [7.6, 4.5], [8.0, 5.2]], BEIGE, 3, { end: "triangle" });
    path_(s, [[6.9, 7.5], [7.6, 7.1], [8.0, 6.5]], BEIGE, 3, { end: "triangle" });
    // center seal
    dot(s, 9.65, 5.85, 1.75, PAPER, { line: RED, lw: 4 });
    dot(s, 9.65, 5.85, 1.55, null, { line: RED, lw: 1.5 });
    txt(s, "MATCH", { x: 7.9, y: 4.55, w: 3.5, h: 0.6, f: "H", size: 30, color: RED, align: "center" });
    txt(s, "SD Δ = 0.047°C", { x: 7.9, y: 5.25, w: 3.5, h: 0.6, f: "B", size: 24, color: INK, align: "center" });
    txt(s, "corr = 0.99986", { x: 7.9, y: 5.9, w: 3.5, h: 0.4, f: "P", size: 16, color: CHAR, align: "center" });
    txt(s, "Tmin reconstructed twice", { x: 7.9, y: 6.4, w: 3.5, h: 0.4, f: "L", size: 13, color: GRAY, align: "center" });
    path_(s, [[11.5, 5.85], [12.3, 5.85]], BEIGE, 3, { end: "triangle" });
    // right: physics chain
    paper(s, 12.55, 2.45, 6.85, 6.75, { tapeX: 4.6 });
    txt(s, "WHY IT MATTERS", { x: 13.05, y: 2.75, w: 5, h: 0.35, f: "B", size: 13, color: RED, charSpacing: 2 });
    const chain = [[Lu.LuThermometerSnowflake, "Tmin", "daily minimum temperature"], [Lu.LuCloudFog, "Dew-point proxy", "Tmin ≈ dew point (proxy)"], [Lu.LuDroplets, "Vapor pressure  e", "actual water vapour"], [Lu.LuPercent, "RH = 100 · e / es(T)", "relative humidity"]];
    for (let i = 0; i < chain.length; i++) {
      const [C, h, d] = chain[i]; const y = 3.3 + i * 1.42;
      dot(s, 13.55, y + 0.5, 0.45, IVORY, { line: i === 3 ? RED : CHAR, lw: 2 });
      await ico(s, C, i === 3 ? RED : CHAR, 13.27, y + 0.22, 0.56);
      txt(s, h, { x: 14.25, y: y + 0.08, w: 4.9, h: 0.5, f: "B", size: 19, color: i === 3 ? RED : INK });
      txt(s, d, { x: 14.25, y: y + 0.55, w: 4.9, h: 0.35, f: "L", size: 13, color: GRAY });
      if (i < 3) line(s, 13.55, y + 0.98, 13.55, y + 1.39, GRAY, 1.5, { end: "triangle" });
    }
    img(s, "magnifier", 9.3, 7.35, 0.85, 1.9, { rot: 45, alt: "magnifying glass" });
    txt(s, "Physical clue, not arbitrary features.", { x: 0.62, y: 9.25, w: 11, h: 0.55, f: "G", size: 22, color: IVORY });
    footer(s, ["Algebraic Inverse Reconstruction", "Dew-Point Proxy", "Physical Feature Engineering"], "Dua rumus saling konsisten, bukan dua sensor independen · rumus lengkap di A4");
    addNotes(s, 4);
  }

  // SLIDE 05 — The crime scene has changed
  {
    const s = pres.addSlide({ sectionTitle: "Act II — The Clues" });
    bg(s); chrome(s, "ACT II — THE CLUES", "05");
    title(s, "THE CRIME SCENE HAS CHANGED", "The future ≠ the past");
    // two condition cards
    const cards = [["TRAIN CONDITION", "27.51°C", CHAR, 0.6, -1.2], ["TEST CONDITION", "24.64°C", RED, 10.4, 1.2]];
    for (const [l, v, c, x, r] of cards) {
      paper(s, x, 2.6, 9.0, 3.6, { rot: r, tapeX: 0.6 });
      await ico(s, Lu.LuThermometer, c, x + 0.6, 3.25, 1.6);
      txt(s, l, { x: x + 2.5, y: 3.15, w: 6, h: 0.4, f: "B", size: 16, color: c, charSpacing: 2, rotate: r });
      txt(s, v, { x: x + 2.4, y: 3.6, w: 6.2, h: 1.55, f: "H", size: 96, color: c, rotate: r });
      txt(s, "mean temperature", { x: x + 2.5, y: 5.2, w: 6, h: 0.4, f: "L", size: 15, color: GRAY, rotate: r });
    }
    // shift tag between cards
    dot(s, 10.0, 4.4, 0.75, RED);
    txt(s, "SHIFT", { x: 9.25, y: 4.05, w: 1.5, h: 0.7, f: "H", size: 22, color: IVORY, align: "center", valign: "middle" });
    // irrigation strip
    paper(s, 0.6, 6.75, 12.4, 2.9, { tape: false, fill: IVORY });
    txt(s, "IRRIGATION SENSOR RECORDS", { x: 1.0, y: 6.95, w: 7, h: 0.35, f: "B", size: 13, color: INK, charSpacing: 2 });
    txt(s, "skematis", { x: 10.5, y: 6.95, w: 2.2, h: 0.35, f: "L", size: 11, color: GRAY, align: "right" });
    const ix0 = 1.0, ixd = 8.3, ix1 = 12.6, iy = 8.35;
    const irr = []; for (let i = 0; i <= 60; i++) { const x = ix0 + (ixd - ix0) * i / 60; irr.push([x, iy - (i % 12 < 3 ? 0.65 : 0.05 * Math.sin(i))]); }
    path_(s, irr, CHAR, 2);
    path_(s, [[ixd, iy], [ix1, iy]], RED, 3);
    line(s, ixd, 7.45, ixd, 9.1, GRAY, 1.25, { dash: "dash" });
    txt(s, "train: varies", { x: ix0, y: 8.85, w: 4, h: 0.4, f: "G", size: 16, color: CHAR });
    txt(s, "test: recorded constant", { x: ixd + 0.15, y: 8.85, w: 4.3, h: 0.4, f: "G", size: 16, color: RED });
    // decision sticker
    img(s, "tanNote2", 13.6, 6.55, 5.8, 3.2, { rot: 2 });
    txt(s, "DECISION", { x: 14.35, y: 7.2, w: 4.5, h: 0.35, f: "B", size: 13, color: RED, charSpacing: 2, rotate: 2 });
    txt(s, "SOIL + IRRIGATION FEATURES EXCLUDED", { x: 14.35, y: 7.6, w: 4.6, h: 1.4, f: "H", size: 30, color: INK, rotate: 2, lsm: 0.95 });
    img(s, "redX", 17.75, 8.35, 1.35, 1.55, { tr: 10 });
    footer(s, ["Distribution Shift Analysis", "Support Check", "Feature Selection"], "Rerata train → test · irigasi tercatat konstan (bukan bukti pompa berhenti)");
    addNotes(s, 5);
  }

  // ---------------- ACT III ----------------
  pres.addSection({ title: "Act III — The Investigation" });

  // SLIDE 06 — Assembling the investigation team
  {
    const s = pres.addSlide({ sectionTitle: "Act III — The Investigation" });
    bg(s); chrome(s, "ACT III — THE INVESTIGATION", "06");
    title(s, "ASSEMBLING THE INVESTIGATION TEAM", "Each model joins for a reason", { size: 56 });
    const team = [
      [Lu.LuShield, "ROBUST SIGNAL", "LightGBM Huber", "Limits the pull of extreme residuals"],
      [Lu.LuPuzzle, "DIVERSE ERRORS", "CatBoost Huber", "Learns patterns and errors differently"],
      [Lu.LuRuler, "LINEAR STRUCTURE", "ElasticNet", "L1 + L2 regularised linear view"],
      [Lu.LuDroplets, "VAPOR-PRESSURE VIEW", "Ridge-e", "Ridge on vapour-pressure physics"],
      [Lu.LuSearch, "LARGE-ERROR SENSITIVITY", "LightGBM L2", "Stays sensitive to big misses"],
    ];
    const cw = 3.4, gap = 0.3, x0 = (20 - (5 * cw + 4 * gap)) / 2;
    for (let i = 0; i < 5; i++) {
      const [C, role, name, fn] = team[i];
      const x = x0 + i * (cw + gap), r = [-1.5, 1, -0.8, 1.4, -1.2][i], y = 2.6;
      paper(s, x, y, cw, 5.6, { rot: r, tapeW: 1.2 });
      txt(s, `SPECIALIST 0${i + 1}`, { x: x + 0.3, y: y + 0.35, w: cw - 0.6, h: 0.3, f: "B", size: 12, color: RED, charSpacing: 2, rotate: r });
      dot(s, x + cw / 2, y + 1.65, 0.72, null, { line: RED, lw: 2.5 });
      await ico(s, C, RED, x + cw / 2 - 0.42, y + 1.23, 0.84);
      txt(s, role, { x: x + 0.25, y: y + 2.6, w: cw - 0.5, h: 0.95, f: "H", size: 22, color: INK, align: "center", valign: "middle", rotate: r, lsm: 0.95 });
      line(s, x + 0.5, y + 3.7, x + cw - 0.5, y + 3.7, "CDBF9F", 1, { dash: "dash" });
      txt(s, name, { x: x + 0.2, y: y + 3.85, w: cw - 0.4, h: 0.5, f: "B", size: 19, color: INK, align: "center", rotate: r });
      txt(s, fn, { x: x + 0.3, y: y + 4.45, w: cw - 0.6, h: 0.8, f: "L", size: 13, color: GRAY, align: "center", rotate: r });
    }
    // eliminated strip
    rect(s, x0, 8.7, 4.6, 0.62, null, { line: MUTED, dash: "dash", lw: 1.25 });
    txt(s, "Ridge (plain): eliminated", { x: x0, y: 8.7, w: 4.6, h: 0.62, f: "P", size: 15, color: MUTED, align: "center", valign: "middle" });
    line(s, x0 + 0.35, 9.01, x0 + 4.25, 9.01, MUTED, 1.5);
    txt(s, "→  Five complementary models", { x: x0 + 4.85, y: 8.7, w: 6, h: 0.62, f: "B", size: 17, color: IVORY, valign: "middle" });
    txt(s, "CatBoost residual corr. vs primary model: 0.64 (audit)", { x: 11.6, y: 8.7, w: 7.2, h: 0.62, f: "G", size: 15, color: BEIGE, align: "right", valign: "middle" });
    footer(s, ["Gradient Boosting", "Huber & L2 Loss", "Linear Regularization", "Residual Diversity"], "Bobot model bergantung waktu, tidak ditampilkan di kartu");
    addNotes(s, 6);
  }

  // SLIDE 07 — Testing their alibis
  {
    const s = pres.addSlide({ sectionTitle: "Act III — The Investigation" });
    bg(s); chrome(s, "ACT III — THE INVESTIGATION", "07");
    title(s, "TESTING THEIR ALIBIS", "Train on the past. Test on the next 15 days.");
    paper(s, 0.6, 2.45, 13.4, 7.4, { tapeX: 1.2 });
    // scale: days 0..61 → x
    const gx0 = 2.35, gx1 = 13.5, D = 61, X = (d) => gx0 + (gx1 - gx0) * d / D;
    // enlarged example fold
    txt(s, "EXAMPLE FOLD", { x: 1.05, y: 2.75, w: 4, h: 0.32, f: "B", size: 13, color: RED, charSpacing: 2 });
    rect(s, X(0), 3.25, X(30) - X(0), 0.75, CHAR);
    txt(s, "PAST / TRAIN  (≥ 30 days)", { x: X(0), y: 3.25, w: X(30) - X(0), h: 0.75, f: "B", size: 16, color: IVORY, align: "center", valign: "middle" });
    rect(s, X(30), 3.25, X(45) - X(30), 0.75, RED);
    txt(s, "VALIDATE 15 DAYS", { x: X(30), y: 3.25, w: X(45) - X(30), h: 0.75, f: "B", size: 16, color: IVORY, align: "center", valign: "middle" });
    line(s, X(30), 3.0, X(30), 4.25, INK, 2.5);
    txt(s, "CUTOFF", { x: X(30) - 0.8, y: 4.27, w: 1.6, h: 0.32, f: "B", size: 12, color: INK, align: "center", charSpacing: 2 });
    // nine origins
    txt(s, "9 ROLLING ORIGINS", { x: 1.05, y: 4.75, w: 4, h: 0.32, f: "B", size: 13, color: RED, charSpacing: 2 });
    for (let i = 0; i < 9; i++) {
      const y = 5.2 + i * 0.47, c = 30 + 2 * i;
      txt(s, `F${i + 1}`, { x: 1.05, y, w: 0.8, h: 0.34, f: "B", size: 12, color: GRAY, valign: "middle" });
      rect(s, X(0), y + 0.04, X(c) - X(0), 0.26, "8E877B");
      rect(s, X(c), y + 0.04, X(c + 15) - X(c), 0.26, RED, { tr: 15 });
    }
    rect(s, X(32), 5.1, X(59) - X(32), 4.3, null, { line: RED, lw: 2, dash: "dash" });
    txt(s, "overlapping validation windows", { x: X(32), y: 9.42, w: X(59) - X(32), h: 0.35, f: "G", size: 14, color: RED, align: "center" });
    txt(s, "schematic · days to scale", { x: 1.05, y: 9.42, w: 4.5, h: 0.35, f: "L", size: 11, color: GRAY });
    // right: metric note
    img(s, "tanNote", 14.35, 2.45, 5.2, 3.75);
    txt(s, "METRIC", { x: 15.1, y: 3.15, w: 4, h: 0.32, f: "B", size: 13, color: RED, charSpacing: 2 });
    txt(s, "RMSE", { x: 15.1, y: 3.5, w: 4, h: 0.8, f: "H", size: 48, color: INK });
    txt(s, "√ mean( (ŷ − y)² )", { x: 15.1, y: 4.35, w: 4.1, h: 0.45, f: "P", size: 18, color: INK });
    txt(s, "↓ lower is better", { x: 15.1, y: 4.95, w: 4, h: 0.45, f: "G", size: 17, color: RED });
    const facts = [["9", "rolling origins"], ["2-day", "step between cutoffs"], ["15 d", "validation horizon"]];
    facts.forEach(([n, l], i) => {
      const y = 6.55 + i * 0.68;
      txt(s, n, { x: 14.45, y, w: 1.5, h: 0.6, f: "H", size: 30, color: IVORY, align: "right", valign: "middle" });
      txt(s, l, { x: 16.15, y, w: 3.3, h: 0.6, f: "P", size: 15, color: BEIGE, valign: "middle" });
    });
    stamp(s, "NOT 9 INDEPENDENT TESTS", 14.45, 8.7, 5.0, 0.8, { rot: -4, size: 22, color: "C9302C" });
    footer(s, ["Rolling-Origin CV", "Out-of-Fold (OOF)", "RMSE"], "Meta-model & koreksi diaudit terpisah (nested) · detail di A2");
    addNotes(s, 7);
  }

  // SLIDE 08 — Combining the evidence
  {
    const s = pres.addSlide({ sectionTitle: "Act III — The Investigation" });
    bg(s); chrome(s, "ACT III — THE INVESTIGATION", "08");
    title(s, "COMBINING THE EVIDENCE", "Time matters — not just more parameters");
    // top process
    paper(s, 0.6, 2.45, 18.8, 3.55, { tapeX: 8.5, fill: IVORY });
    const models = ["LightGBM Huber", "CatBoost Huber", "ElasticNet", "Ridge-e", "LightGBM L2"];
    models.forEach((m, i) => {
      const y = 2.72 + i * 0.6;
      rect(s, 1.0, y, 3.4, 0.46, PAPER, { line: CHAR, lw: 1.25 });
      txt(s, m, { x: 1.0, y, w: 3.4, h: 0.46, f: "B", size: 13, color: INK, align: "center", valign: "middle" });
      path_(s, [[4.45, y + 0.23], [6.7, 4.22]], GRAY, 1.25);
    });
    dot(s, 7.75, 4.22, 1.05, PAPER, { line: RED, lw: 3.5 });
    txt(s, "NNLS", { x: 6.7, y: 3.82, w: 2.1, h: 0.55, f: "H", size: 32, color: RED, align: "center", valign: "middle" });
    txt(s, "weights ≥ 0", { x: 6.7, y: 4.36, w: 2.1, h: 0.35, f: "P", size: 12, color: CHAR, align: "center" });
    line(s, 8.85, 4.22, 10.6, 4.22, CHAR, 2.5, { end: "triangle" });
    // clock with time bands (conceptual)
    s.addShape(pres.shapes.PIE, { x: 10.8, y: 3.0, w: 2.45, h: 2.45, angleRange: [0, 90], fill: { color: "D9CBA6" }, line: { color: PAPER, width: 2 } });
    s.addShape(pres.shapes.PIE, { x: 10.8, y: 3.0, w: 2.45, h: 2.45, angleRange: [90, 180], fill: { color: TAN }, line: { color: PAPER, width: 2 } });
    s.addShape(pres.shapes.PIE, { x: 10.8, y: 3.0, w: 2.45, h: 2.45, angleRange: [180, 270], fill: { color: "8E877B" }, line: { color: PAPER, width: 2 } });
    s.addShape(pres.shapes.PIE, { x: 10.8, y: 3.0, w: 2.45, h: 2.45, angleRange: [270, 360], fill: { color: "B9AD8C" }, line: { color: PAPER, width: 2 } });
    dot(s, 12.025, 4.225, 0.12, INK);
    line(s, 12.025, 4.225, 12.025, 3.35, INK, 2.5);
    line(s, 12.025, 4.225, 12.6, 4.6, INK, 2.5);
    txt(s, "A separate weight set for each time-of-day band", { x: 13.6, y: 3.15, w: 5.5, h: 0.9, f: "B", size: 17, color: INK, lsm: 1.05 });
    txt(s, "+ 25% shrinkage toward the global blend, so weights do not chase validation noise", { x: 13.6, y: 4.1, w: 5.5, h: 1.0, f: "L", size: 14, color: CHAR });
    txt(s, "bands: konseptual", { x: 10.6, y: 5.5, w: 2.85, h: 0.3, f: "L", size: 11, color: GRAY, align: "center" });
    // bottom evidence chart (native)
    paper(s, 0.6, 6.45, 12.6, 3.55, { tape: false });
    txt(s, "NESTED VALIDATION · ΔRMSE vs single blend", { x: 1.0, y: 6.65, w: 9, h: 0.35, f: "B", size: 13, color: RED, charSpacing: 1 });
    hbars(s, [["Time-based bands", -0.08, GREEN, "−0.080"], ["Random control", -0.007, "8E877B", "−0.007"]], {
      x: 1.0, y: 7.15, w: 11.6, labelW: 3.1, vmin: -0.09, vmax: 0, ticks: [-0.08, -0.06, -0.04, -0.02], fmt: (t) => "−" + Math.abs(t).toFixed(2), barH: 0.72, gap: 0.38,
    });
    // right takeaway
    img(s, "beigeClip", 13.75, 6.3, 3.8, 3.81, { rot: 3 });
    txt(s, "−0.080", { x: 14.0, y: 6.95, w: 3.2, h: 0.85, f: "H", size: 46, color: GREEN, align: "center", rotate: 3 });
    txt(s, "vs  −0.007", { x: 14.0, y: 7.8, w: 3.2, h: 0.6, f: "H", size: 28, color: GRAY, align: "center", rotate: 3 });
    txt(s, "Equal number of parameters", { x: 14.05, y: 8.6, w: 3.2, h: 0.8, f: "G", size: 15, color: INK, align: "center", rotate: 3 });
    footer(s, ["Time-Banded NNLS", "25% Shrinkage", "Equal-Parameter Random Control"], "Kontrol acak = pengelompokan OOF acak, bukan pengacakan train/test");
    addNotes(s, 8);
  }

  // ---------------- ACT IV ----------------
  pres.addSection({ title: "Act IV — The Breakthrough" });

  // SLIDE 09 — The pattern nobody noticed
  {
    const s = pres.addSlide({ sectionTitle: "Act IV — The Breakthrough" });
    bg(s); chrome(s, "ACT IV — THE BREAKTHROUGH", "09");
    title(s, "THE PATTERN NOBODY NOTICED", "The errors were not random");
    paper(s, 0.6, 2.45, 10.6, 7.3, { tapeX: 1.0 });
    txt(s, "VALIDATION RESIDUALS OVER TIME", { x: 1.1, y: 2.75, w: 8, h: 0.35, f: "B", size: 13, color: RED, charSpacing: 1 });
    const zx0 = 1.4, zx1 = 10.6, zy = 6.0;
    line(s, zx0, zy, zx1, zy, CHAR, 1.75);
    txt(s, "0", { x: 1.05, y: zy - 0.2, w: 0.3, h: 0.4, f: "B", size: 14, color: CHAR });
    txt(s, "over-predicted", { x: 1.5, y: 3.25, w: 3, h: 0.35, f: "L", size: 12, color: GRAY });
    txt(s, "under-predicted", { x: 1.5, y: 8.55, w: 3, h: 0.35, f: "L", size: 12, color: GRAY });
    // smooth drifting residuals (schematic)
    const pts = [];
    for (let i = 0; i < 34; i++) { const x = 1.7 + i * 0.26; const v = 1.55 * Math.sin(i / 5.2 + 0.4) + 0.35 * Math.sin(i / 1.7); pts.push([x, zy - v]); }
    path_(s, pts, RED, 1.75);
    pts.forEach(([x, y], i) => dot(s, x, y, 0.085, y > zy ? RED : CHAR));
    // magnifier over a run below zero
    dot(s, 6.85, 7.35, 0.95, null, { line: RED, lw: 2.5 });
    txt(s, "Nearby errors drift together", { x: 5.0, y: 8.45, w: 5.9, h: 0.45, f: "G", size: 19, color: RED, align: "right" });
    txt(s, "Ilustrasi pola residual; statistik dari laporan", { x: 1.1, y: 9.2, w: 8, h: 0.3, f: "L", size: 11, color: GRAY });
    // right: big number on torn fragment
    img(s, "creamStrip", 11.55, 2.35, 8.1, 3.4);
    txt(s, "0.93", { x: 12.0, y: 2.95, w: 7.2, h: 2.3, f: "H", size: 170, color: INK, align: "center", valign: "middle" });
    txt(s, "Lag-1 autocorrelation of level-model errors", { x: 11.9, y: 5.9, w: 7.5, h: 0.45, f: "B", size: 18, color: IVORY, align: "center" });
    txt(s, "(residual autocorrelation, not target autocorrelation)", { x: 11.9, y: 6.35, w: 7.5, h: 0.4, f: "L", size: 13, color: BEIGE, align: "center" });
    stamp(s, "NEW LEAD: MOTION", 13.45, 7.35, 4.6, 0.95, { rot: -5, size: 30, color: "C9302C" });
    txt(s, "Predict how much humidity changes, not just its level", { x: 12.1, y: 8.65, w: 7.2, h: 0.5, f: "G", size: 16, color: BEIGE, align: "center" });
    footer(s, ["Residual Autocorrelation Analysis", "→", "Increment Prediction Hypothesis"], "0.93 dari laporan §V-D, tidak dihitung dari diagram");
    addNotes(s, 9);
  }

  // SLIDE 10 — video slot (background only)
  {
    const s = pres.addSlide({ sectionTitle: "Act IV — The Breakthrough" });
    bg(s);
    addNotes(s, 10, "[SLOT VIDEO — Slide 10 '10_temporal_reconciliation.mp4' (75 dtk). Background saja; tempel video di sini, siapkan poster frame statis sebagai cadangan.]");
  }

  // SLIDE 11 — The breakthrough is real
  {
    const s = pres.addSlide({ sectionTitle: "Act IV — The Breakthrough" });
    bg(s); chrome(s, "ACT IV — THE BREAKTHROUGH", "11");
    title(s, "THE BREAKTHROUGH IS REAL", "A measurable breakthrough");
    img(s, "gridTape", 0.3, 2.2, 13.6, 6.66);
    txt(s, "PUBLIC RMSE  ·  lower is better", { x: 6.2, y: 2.95, w: 8, h: 0.35, f: "B", size: 13, color: RED, charSpacing: 1 });
    txt(s, "BEFORE RECONCILIATION", { x: 1.95, y: 3.6, w: 5, h: 0.4, f: "B", size: 16, color: GRAY, charSpacing: 1 });
    txt(s, "3.02586", { x: 1.9, y: 4.05, w: 5.0, h: 1.6, f: "H", size: 92, color: CHAR });
    img(s, "solidArrow", 6.85, 4.4, 1.0, 0.92);
    txt(s, "AFTER", { x: 8.05, y: 3.6, w: 5, h: 0.4, f: "B", size: 16, color: GREEN, charSpacing: 1 });
    txt(s, "2.86595", { x: 8.0, y: 4.05, w: 5.1, h: 1.6, f: "H", size: 92, color: GREEN });
    line(s, 1.95, 6.15, 12.7, 6.15, "B9AD8C", 1.25, { dash: "dash" });
    txt(s, [["ΔRMSE = ", { f: "B", size: 26, color: INK }], ["−0.15991", { f: "H", size: 40, color: RED }]], { x: 1.95, y: 6.4, w: 6.2, h: 0.85, valign: "middle" });
    txt(s, "after Temporal Reconciliation", { x: 1.95, y: 7.25, w: 6, h: 0.4, f: "G", size: 16, color: CHAR });
    // forward blocks
    txt(s, "FORWARD AUDIT · separate check", { x: 8.3, y: 6.4, w: 4.6, h: 0.35, f: "B", size: 12, color: CHAR, charSpacing: 1 });
    [["B1", "−0.043"], ["B2", "−0.154"], ["B3", "−0.112"]].forEach(([b, v], i) => {
      const x = 8.3 + i * 1.5;
      txt(s, [["✓ ", { f: "P", color: GREEN }], [b, { f: "B", color: INK }]], { x, y: 6.85, w: 1.4, h: 0.4, size: 16 });
      txt(s, v, { x, y: 7.22, w: 1.4, h: 0.4, f: "P", size: 15, color: GREEN });
    });
    // right: horizon note
    img(s, "clipPaper", 14.15, 2.25, 5.5, 5.51, { rot: 2 });
    txt(s, "WHY 4 : 1 ?", { x: 14.75, y: 2.85, w: 4.0, h: 0.6, f: "H", size: 32, color: INK });
    txt(s, "OOF RMSE of predicted change · 6,471 rows", { x: 14.75, y: 3.45, w: 4.3, h: 0.35, f: "L", size: 12, color: GRAY });
    const hz = [["30 MIN", "1.81", "1.91"], ["2 HOURS", "3.52", "3.57"]];
    hz.forEach(([h, m, l], i) => {
      const y = 4.05 + i * 1.3;
      txt(s, h, { x: 14.75, y, w: 4, h: 0.35, f: "B", size: 15, color: RED, charSpacing: 1 });
      txt(s, [["increment ", { f: "L", size: 13, color: CHAR }], [m, { f: "B", size: 22, color: GREEN }], ["   level-derived ", { f: "L", size: 13, color: CHAR }], [l, { f: "B", size: 22, color: GRAY }]], { x: 14.75, y: y + 0.38, w: 4.5, h: 0.55, valign: "middle" });
    });
    txt(s, "30 MIN > 2 H extra signal", { x: 14.75, y: 6.75, w: 4.4, h: 0.45, f: "G", size: 17, color: RED });
    txt(s, "Skor publik berpasangan; OOF & audit maju bukan skor publik", { x: 0.62, y: 9.2, w: 13, h: 0.4, f: "L", size: 12, color: MUTED });
    footer(s, ["Horizon Error Analysis", "Temporal Reconciliation", "Forward Audit"], "Data: laporan submission Heisenberg");
    addNotes(s, 11);
  }

  // SLIDE 12 — The hidden bias
  {
    const s = pres.addSlide({ sectionTitle: "Act IV — The Breakthrough" });
    bg(s); chrome(s, "ACT IV — THE BREAKTHROUGH", "12");
    title(s, "THE HIDDEN BIAS", "Direction matters · Bias = Prediction − Actual");
    paper(s, 0.6, 2.45, 18.8, 4.35, { tapeX: 9.0 });
    // badge
    rect(s, 1.0, 2.75, 1.9, 0.45, RED);
    txt(s, "CATBOOST", { x: 1.0, y: 2.75, w: 1.9, h: 0.45, f: "B", size: 14, color: IVORY, align: "center", valign: "middle", charSpacing: 2 });
    txt(s, "SIGNED BIAS  (%RH)", { x: 3.15, y: 2.78, w: 5, h: 0.4, f: "B", size: 13, color: CHAR, charSpacing: 1 });
    // axis −3.5 .. +1.0
    const ax0 = 1.6, ax1 = 18.4, vmin = -3.5, vmax = 1.0, AX = (v) => ax0 + (ax1 - ax0) * (v - vmin) / (vmax - vmin), ay = 5.4;
    line(s, ax0, ay, ax1, ay, CHAR, 1.75);
    [-3, -2, -1, 0, 1].forEach((v) => {
      line(s, AX(v), ay - 0.1, AX(v), ay + 0.1, CHAR, 1.5);
      txt(s, v === 0 ? "0" : (v > 0 ? "+" : "−") + Math.abs(v), { x: AX(v) - 0.5, y: ay + 0.18, w: 1, h: 0.35, f: "P", size: 13, color: GRAY, align: "center" });
    });
    line(s, AX(0), 3.35, AX(0), 6.35, INK, 2.5);
    txt(s, "zero bias", { x: AX(0) + 0.12, y: 3.3, w: 1.6, h: 0.35, f: "L", size: 12, color: CHAR });
    // markers
    dot(s, AX(-0.006), ay, 0.2, CHAR);
    txt(s, [["IN-SAMPLE  ", { f: "B", size: 15, color: CHAR }], ["−0.006", { f: "H", size: 26, color: CHAR }]], { x: AX(0) - 3.85, y: 3.75, w: 3.65, h: 0.6, align: "right", valign: "middle" });
    line(s, AX(0) - 0.15, 4.2, AX(-0.006), ay - 0.25, CHAR, 1.25);
    dot(s, AX(-2.89), ay, 0.26, RED);
    txt(s, [["FORWARD AUDIT  ", { f: "B", size: 15, color: RED }], ["−2.89", { f: "H", size: 30, color: RED }]], { x: AX(-2.89) - 0.6, y: 3.6, w: 5, h: 0.7, valign: "middle" });
    line(s, AX(-2.89), 4.3, AX(-2.89), ay - 0.3, RED, 1.25);
    // underprediction arrow
    line(s, AX(-0.4), 6.15, AX(-3.3), 6.15, RED, 3, { end: "triangle" });
    txt(s, "UNDERPREDICTION", { x: AX(-3.3), y: 5.85, w: 3.4, h: 0.3, f: "B", size: 12, color: RED, charSpacing: 2 });
    // lower flow
    const steps = [["OOF bias estimate", "−1.86 %RH", "from out-of-fold predictions"], ["50% partial correction", "½ × OOF", "not the audit value −2.89"], ["Negative controls", "2 / 2 rejected", "no benefit when the logic is wrong"]];
    steps.forEach(([h, v, d], i) => {
      const x = 0.6 + i * 6.35;
      img(s, i === 2 ? "tanNote2" : "tanNote", x, 7.05, 5.75, 2.95);
      txt(s, `STEP ${i + 1}`, { x: x + 0.75, y: 7.6, w: 4, h: 0.3, f: "B", size: 12, color: RED, charSpacing: 2 });
      txt(s, h, { x: x + 0.75, y: 7.92, w: 4.7, h: 0.45, f: "B", size: 18, color: INK });
      txt(s, v, { x: x + 0.75, y: 8.38, w: 4.7, h: 0.7, f: "H", size: 34, color: i === 2 ? RED : INK });
      txt(s, d, { x: x + 0.75, y: 9.1, w: 4.7, h: 0.35, f: "L", size: 13, color: CHAR });
      if (i < 2) img(s, "chevrons", x + 5.55, 8.1, 0.75, 0.56);
    });
    footer(s, ["Residual Bias Analysis", "OOF-Based Partial Bias Correction", "Negative Control"], "−1.86 (OOF) dan −2.89 (audit maju) adalah instrumen berbeda");
    addNotes(s, 12, "[Negative control: koreksi arah salah → tidak membaik; koreksi pada model hampir tak bias → tidak membaik.]");
  }

  // SLIDE 13 — The rejected evidence
  {
    const s = pres.addSlide({ sectionTitle: "Act IV — The Breakthrough" });
    bg(s); chrome(s, "ACT IV — THE BREAKTHROUGH", "13");
    title(s, "THE REJECTED EVIDENCE", "More complex ≠ better");
    paper(s, 0.6, 2.45, 18.8, 4.55, { tapeX: 1.0 });
    txt(s, "PUBLIC RMSE  ·  higher = worse", { x: 1.1, y: 2.75, w: 8, h: 0.35, f: "B", size: 13, color: RED, charSpacing: 1 });
    const vmin = 2.84, vmax = 2.95, dx0 = 2.0, dx1 = 18.0, DX = (v) => dx0 + (dx1 - dx0) * (v - vmin) / (vmax - vmin), dy = 4.95;
    line(s, dx0, dy + 0.9, dx1, dy + 0.9, CHAR, 1.5);
    [2.84, 2.86, 2.88, 2.90, 2.92, 2.94].forEach((v) => {
      line(s, DX(v), dy + 0.82, DX(v), dy + 0.98, CHAR, 1.5);
      txt(s, v.toFixed(2), { x: DX(v) - 0.5, y: dy + 1.05, w: 1, h: 0.35, f: "P", size: 13, color: GRAY, align: "center" });
    });
    line(s, DX(2.86595) + 0.3, dy, DX(2.93028) - 0.34, dy, RED, 3.5, { end: "triangle" });
    dot(s, DX(2.86595), dy, 0.28, GREEN);
    dot(s, DX(2.93028), dy, 0.28, RED);
    txt(s, [["ACCEPTED BASELINE\n", { f: "B", size: 13, color: GREEN, breakLine: false }], ["2.86595", { f: "H", size: 34, color: GREEN }]], { x: DX(2.86595) - 1.9, y: 3.2, w: 3.8, h: 1.25, align: "center", valign: "bottom" });
    txt(s, [["+ INCREMENT PACKAGE\n", { f: "B", size: 13, color: RED }], ["2.93028", { f: "H", size: 34, color: RED }]], { x: DX(2.93028) - 1.9, y: 3.2, w: 3.8, h: 1.25, align: "center", valign: "bottom" });
    txt(s, "+0.06433  (worse)", { x: DX(2.86595) + 1.5, y: dy + 0.2, w: 5.5, h: 0.45, f: "G", size: 18, color: RED, align: "center" });
    stamp(s, "REJECTED", 15.75, 4.2, 3.3, 0.95, { rot: -9, size: 40 });
    // caveats
    const cav = [[Lu.LuCalendarClock, "REAL-TIME NEEDS CAUSAL DATA", "Do not deploy without a causal-information test"], [Lu.LuSprout, "NO CROP-OUTCOME CLAIM", "Harvest and plant health were not tested"]];
    for (let i = 0; i < 2; i++) {
      const [C, h, d] = cav[i], x = 0.6 + i * 9.5;
      img(s, i ? "tanNote2" : "tanNote", x, 7.25, 8.9, 2.95);
      dot(s, x + 1.55, 8.65, 0.55, IVORY);
      await ico(s, C, RED, x + 1.17, 8.27, 0.76);
      txt(s, h, { x: x + 2.4, y: 7.9, w: 6.2, h: 0.65, f: "H", size: 24, color: INK, valign: "middle" });
      txt(s, d, { x: x + 2.4, y: 8.6, w: 6.2, h: 0.5, f: "P", size: 16, color: CHAR });
    }
    footer(s, ["Rejected Experiment", "Deployment Assumptions", "Public Leaderboard Feedback"], "Feedback leaderboard publik ikut memengaruhi sebagian koreksi pasca-model");
    addNotes(s, 13);
  }

  // ---------------- ACT V ----------------
  pres.addSection({ title: "Act V — Case Closed" });

  // SLIDE 14 — Case closed
  {
    const s = pres.addSlide({ sectionTitle: "Act V — Case Closed" });
    bg(s); chrome(s, "ACT V — CASE CLOSED", "14");
    txt(s, "BERKAS 734", { x: 0.6, y: 0.95, w: 9, h: 0.9, f: "H", size: 48, color: BEIGE });
    img(s, "foot", 7.4, 0.9, 1.15, 1.5, { rot: 25, tr: 35 });
    txt(s, "PUBLIC RMSE", { x: 0.65, y: 2.75, w: 9, h: 0.45, f: "B", size: 20, color: BEIGE, charSpacing: 3 });
    txt(s, "2.82744", { x: 0.5, y: 3.15, w: 9.6, h: 2.4, f: "H", size: 150, color: IVORY });
    txt(s, "BEST DOCUMENTED TEAM CONFIGURATION", { x: 0.65, y: 5.6, w: 9, h: 0.4, f: "B", size: 14, color: BEIGE, charSpacing: 2 });
    txt(s, "734 values reconstructed", { x: 0.65, y: 6.05, w: 8, h: 0.6, f: "G", size: 24, color: IVORY });
    // right paper with OOF chart
    paper(s, 10.4, 1.55, 9.0, 6.2, { tapeX: 0.6 });
    txt(s, "POOLED OOF RMSE · 6,480 rows", { x: 10.85, y: 1.9, w: 6.0, h: 0.4, f: "B", size: 15, color: INK, charSpacing: 1 });
    txt(s, "same 9 rolling origins · different population from public score", { x: 10.85, y: 2.3, w: 8.2, h: 0.35, f: "L", size: 12, color: GRAY });
    hbars(s, [["LightGBM baseline", 5.71, "8E877B", "5.71"], ["Full pipeline", 4.81, GREEN, "4.81"]], {
      x: 10.85, y: 3.0, w: 7.6, labelW: 2.6, vmin: 0, vmax: 6, ticks: [1, 2, 3, 4, 5, 6], fmt: (t) => String(t), barH: 0.85, gap: 0.45,
    });
    txt(s, [["15.8% lower", { f: "H", size: 34, color: GREEN }], ["   ·   better on 9/9 overlapping origins", { f: "P", size: 15, color: CHAR }]], { x: 10.85, y: 6.45, w: 8.3, h: 0.75, valign: "middle" });
    stamp(s, "CASE CLOSED", 0.75, 6.85, 5.4, 1.1, { rot: -4, size: 44, color: "D9413A", lw: 4.5 });
    // evidence trail
    const trail = [[Lu.LuFileSearch, "DATA AUDIT"], [Lu.LuAtom, "PHYSICS"], [Lu.LuLayers, "ENSEMBLE"], [Lu.LuActivity, "TEMPORAL RECONSTRUCTION"], [Lu.LuScale, "BIAS CHECK"]];
    const tw = 2.85, tg = 0.45, tx0 = 10.4 - (5 * tw + 4 * tg - 9.0);
    for (let i = 0; i < 5; i++) {
      const [C, l] = trail[i], x = 2.35 + i * (tw + tg) + 0.0;
      rect(s, x, 8.3, tw, 1.55, IVORY, { shadow: true, rot: [-2, 1.5, -1, 2, -1.5][i] });
      await ico(s, C, RED, x + tw / 2 - 0.3, 8.42, 0.6);
      txt(s, l, { x: x + 0.1, y: 9.08, w: tw - 0.2, h: 0.65, f: "B", size: 13, color: INK, align: "center", valign: "middle", rotate: [-2, 1.5, -1, 2, -1.5][i] });
      if (i < 4) txt(s, "→", { x: x + tw, y: 8.75, w: tg, h: 0.6, f: "B", size: 20, color: BEIGE, align: "center", valign: "middle" });
    }
    footer(s, [], "Public ≠ private  ·  OOF ≠ leaderboard  ·  estimasi, bukan nilai aktual yang terungkap", { label: "HEISENBERG" });
    addNotes(s, 14);
  }

  await pres.writeFile({ fileName: OUT });
  console.log("wrote", OUT);
}
build().catch((e) => { console.error(e); process.exit(1); });

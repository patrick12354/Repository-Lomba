(function () {
  const D = window.SK;
  const $ = (s, r) => (r || document).querySelector(s);
  const $$ = (s, r) => Array.from((r || document).querySelectorAll(s));

  const P = {
    up: '<path d="M7 17 17 7M8 7h9v9"/>', search: '<circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/>', bell: '<path d="M6 9a6 6 0 1 1 12 0c0 6 2 7 2 7H4s2-1 2-7M10 20a2 2 0 0 0 4 0"/>', gear: '<circle cx="12" cy="12" r="3"/><path d="M12 3v3M12 18v3M3 12h3M18 12h3M5.6 5.6l2.1 2.1M16.3 16.3l2.1 2.1M18.4 5.6l-2.1 2.1M7.7 16.3l-2.1 2.1"/>', check: '<path d="m5 12 5 5 9-10"/>', x: '<path d="M6 6l12 12M18 6 6 18"/>', truck: '<path d="M3 7h11v9H3zM14 10h4l3 3v3h-7"/><circle cx="7" cy="18" r="2"/><circle cx="17" cy="18" r="2"/>', clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>', play: '<path d="M8 5v14l11-7z" fill="currentColor"/>', prev: '<path d="M18 6 9 12l9 6zM6 6v12"/>', next: '<path d="m6 6 9 6-9 6zM18 6v12"/>', layers: '<path d="m12 3 9 5-9 5-9-5zM3 13l9 5 9-5"/>', plus: '<path d="M12 5v14M5 12h14"/>', minus: '<path d="M5 12h14"/>', pin: '<path d="M12 22s7-6.5 7-12a7 7 0 1 0-14 0c0 5.5 7 12 7 12"/><circle cx="12" cy="10" r="2.5" fill="#fff"/>', box: '<path d="m12 3 8 4.5v9L12 21l-8-4.5v-9zM4 7.5l8 4.5 8-4.5M12 12v9"/>', list: '<path d="M9 6h11M9 12h11M9 18h11M4 6h.01M4 12h.01M4 18h.01"/>', chart: '<path d="M4 19V5M4 19h16M8 15l4-5 3 3 4-6"/>', sliders: '<path d="M4 8h10M18 8h2M4 16h2M10 16h10"/><circle cx="16" cy="8" r="2"/><circle cx="8" cy="16" r="2"/>', shield: '<path d="M12 3 5 6v6c0 4.5 3 7.5 7 9 4-1.5 7-4.5 7-9V6z"/><path d="m9 12 2 2 4-4"/>', cal: '<rect x="4" y="5" width="16" height="15" rx="3"/><path d="M4 10h16M9 3v4M15 3v4"/>', swap: '<path d="M4 8h14l-3-3M20 16H6l3 3"/>', wave: '<path d="M3 9c3-3 5-3 8 0s5 3 10 0M3 15c3-3 5-3 8 0s5 3 10 0"/>', drop: '<path d="M12 3s7 7.2 7 12a7 7 0 1 1-14 0c0-4.8 7-12 7-12z"/>', menu: '<path d="M4 8h16M4 16h10"/>', fire: '<path d="M12 3c1 4 6 6 6 11a6 6 0 1 1-12 0c0-3 2-4 3-6 1 2 2 2 3-5z"/>', cog: '<circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="3"/>', leaf: '<path d="M5 19C5 10 11 4 20 4c0 9-6 15-15 15zM5 19 14 10"/>',
  };
  const ic = (n, cls) => `<svg class="${cls || "ic"}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${P[n]}</svg>`;

  const rp = (v) => "Rp " + (v / 1e9).toFixed(v >= 1e11 ? 0 : 1) + " B";
  const num = (n) => Math.round(n).toLocaleString("en-US");
  const shortD = (s, y) => {
    const d = new Date(s + "T00:00:00Z");
    return d.getUTCDate() + " " + ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][d.getUTCMonth()] + (y ? " " + d.getUTCFullYear() : "");
  };
  const MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  const mLab = (m) => MON[+m.slice(5) - 1];

  const ab = D.byCrit.filter((c) => "AB".includes(c.crit));
  const abReady = ab.reduce((a, c) => a + c.ready, 0), abTotal = ab.reduce((a, c) => a + c.total, 0);
  const abPct = Math.round((abReady / abTotal) * 100);
  const allReady = D.counts.READY, allPct = Math.round((allReady / D.total) * 100);
  const MARK = '<svg class="logo-mark" viewBox="0 0 32 32" aria-hidden="true"><rect x="1" y="1" width="30" height="30" rx="9" fill="var(--logo, #16181b)"/><path d="M16 7.5 24 12v8.4L16 25l-8-4.6V12z M8 12l8 4.5 8-4.5M16 16.5V25" fill="none" stroke="#fff" stroke-width="1.9" stroke-linejoin="round"/><path d="m12 9.8 8 4.5" stroke="#f2b33d" stroke-width="1.9" stroke-linecap="round"/></svg>';
  const PROOF = [["Anchor, refractory type LF931", 25, 200], ["Oil, lubricant iso VG 68 5L", 26, 205], ["Studbolt, 1INX85MM B8M/8M", 28, 204], ["O-ring, nbr 137MM ID", 10, 52]];
  const NAV = ["Shutdown", "To do", "Stock", "Forecast", "What if", "Data check"];

  /* ---------- gauges ---------- */
  function tickGauge(p, on, off) {
    const n = 48, R = 104, cx = 130, cy = 122;
    let s = "";
    for (let i = 0; i < n; i++) {
      const t = i / (n - 1), a = Math.PI * (1 - t);
      const inner = R - 24, x1 = cx + Math.cos(a) * inner, y1 = cy - Math.sin(a) * inner, x2 = cx + Math.cos(a) * R, y2 = cy - Math.sin(a) * R;
      s += `<line x1="${x1.toFixed(1)}" y1="${y1.toFixed(1)}" x2="${x2.toFixed(1)}" y2="${y2.toFixed(1)}" stroke="${t * 100 <= p ? on : off}" stroke-width="5" stroke-linecap="round"/>`;
    }
    return `<svg viewBox="0 0 260 132" role="img" aria-label="${p} percent of A and B parts ready">${s}</svg>`;
  }
  function needleGauge(p) {
    const a0 = Math.PI, a1 = 0, a = a0 + (a1 - a0) * (p / 100);
    const R = 92, cx = 110, cy = 102;
    const pt = (an, r) => [(cx + Math.cos(an) * r).toFixed(1), (cy - Math.sin(an) * r).toFixed(1)];
    const [ax, ay] = pt(a0, R), [bx, by] = pt(a, R), [ex, ey] = pt(a1, R), [nx, ny] = pt(a, R + 11);
    const [ix, iy] = pt(a0, R - 16), [jx, jy] = pt(a, R - 16);
    return `<svg viewBox="0 0 220 112" role="img" aria-label="Needle at ${p} percent"><path d="M${ix} ${iy} A${R - 16} ${R - 16} 0 0 1 ${jx} ${jy} L${cx} ${cy} Z" fill="rgb(255 255 255 / .55)"/><path d="M${ax} ${ay} A${R} ${R} 0 0 1 ${ex} ${ey}" stroke="rgb(0 0 0 / .16)" stroke-width="1.5" fill="none"/><path d="M${bx} ${by} A${R} ${R} 0 0 1 ${ex} ${ey}" stroke="#111" stroke-width="4" fill="none" stroke-linecap="round"/><line x1="${cx}" y1="${cy}" x2="${nx}" y2="${ny}" stroke="#111" stroke-width="1.4"/><circle cx="${cx}" cy="${cy}" r="3.5" fill="#111"/><circle cx="${nx}" cy="${ny}" r="2.5" fill="#111"/></svg>`;
  }

  /* ---------- ref 3 cards ---------- */
  const dots = (arr, color) => `<div class="dotrow" style="color:${color || "currentColor"}">${arr.map((s) => `<i style="width:${s}px;height:${s}px"></i>`).join("")}</div>`;
  function spark(vals, dotted) {
    const W = 120, H = 34, max = Math.max(...vals), min = Math.min(...vals);
    const pts = vals.map((v, i) => [(i / (vals.length - 1)) * W, H - 4 - ((v - min) / (max - min || 1)) * (H - 8)]);
    return `<svg viewBox="-3 -3 ${W + 6} ${H + 6}" width="100%" aria-hidden="true"><polyline points="${pts.map((p) => p.map((n) => n.toFixed(1)).join(",")).join(" ")}" fill="none" stroke="currentColor" stroke-width="1.6" ${dotted ? 'stroke-dasharray="2 4"' : ""} stroke-linecap="round"/>${pts.filter((_, i) => i % 3 === 0).map((p) => `<circle cx="${p[0].toFixed(1)}" cy="${p[1].toFixed(1)}" r="2.2" fill="currentColor"/>`).join("")}</svg>`;
  }
  function bars(vals) {
    const max = Math.max(...vals) || 1;
    return `<svg viewBox="0 0 ${vals.length * 11} 34" width="100%" aria-hidden="true">${vals.map((v, i) => `<rect x="${i * 11 + 2}" y="${34 - Math.max(2, (v / max) * 34)}" width="3" height="${Math.max(2, (v / max) * 34)}" rx="1.5" fill="currentColor"/>`).join("")}</svg>`;
  }
  function metricCards() {
    const weeks = D.weeks.map((w) => w.count);
    const items = [
      { glow: 1, icon: "clock", label: "Too late to buy", sub: "Lead time past 1 Nov", n: D.counts.TOO_LATE, viz: dots([6, 10, 14, 8, 6, 12]) },
      { icon: "cal", label: "Order this week", sub: "Last safe day 2 and 4 Oct", n: D.counts.ORDER_NOW, viz: bars(weeks) },
      { icon: "box", label: "Need more than Max", sub: "One turnaround beats the old Max", n: D.exceeds, small: "/" + D.total, viz: `<div class="dotrow" style="color:var(--ink)">${[0, 1, 2, 3, 4].map((i) => `<i style="width:10px;height:10px;${i < 2 ? "" : "background:none;box-shadow:inset 0 0 0 1.4px currentColor"}"></i>`).join("")}</div>` },
      { icon: "chart", label: "Forecast hit rate", sub: "vs 84 for the baseline", n: Math.round(D.proof.engine * 100), small: "/100", viz: spark([84, 85, 86, 88, 87, 89, 90, 91]) },
      { icon: "swap", label: "Use a twin", sub: "Same part, another number", n: D.alerts.twin, viz: spark([3, 5, 3, 6, 4, 6, 3, 5, 4], true) },
      { icon: "wave", label: "Spend on over-Max parts", sub: "Of Rp 1,634 B purchased", n: Math.round(D.pctAbove * 100), small: "%", viz: dots([3, 5, 7, 9, 7, 5, 3, 5, 7]) },
    ];
    return items.map((c) => `<button type="button" class="mcard ${c.glow ? "glow" : ""}">
      <div class="mcard-top"><div><span class="mcard-ico">${ic(c.icon)}</span><div class="mcard-label">${c.label}</div><div class="mcard-sub">${c.sub}</div></div><span class="arrow">${ic("up", "")}</span></div>
      <div class="mcard-foot"><div class="mcard-num num">${c.n}${c.small ? `<small>${c.small}</small>` : ""}</div><div class="mcard-viz">${c.viz}</div></div>
    </button>`).join("");
  }

  function band() {
    const w = D.weeks, W = 520, H = 150, max = Math.max(...w.map((x) => x.count));
    const step = W / w.length;
    const bar = w.map((x, i) => {
      const h = Math.max(3, Math.sqrt(x.count / max) * 96), bx = i * step + step / 2;
      const lab = x.week < 0 ? "Too late" : x.week === 0 ? "This week" : shortD(x.start);
      return `<rect x="${bx - 9}" y="${116 - h}" width="18" height="${h}" rx="3" fill="${x.week < 0 ? "#e8583f" : x.week === 0 ? "#e8a33a" : "rgb(255 255 255 / .26)"}"/><text x="${bx}" y="${112 - h}" text-anchor="middle" font-size="12" font-weight="600" fill="#fff" dy="-4">${x.count}</text><text x="${bx}" y="136" text-anchor="middle" font-size="11" fill="rgb(255 255 255 / .6)">${lab}</text>`;
    }).join("");
    return `<div class="band"><div class="inner band-in">
      <div><div class="band-head"><h3>Order runway</h3><div class="ghost-pills"><button type="button">Smaller</button><button type="button" aria-pressed="true">Same as last</button><button type="button">Bigger</button></div></div>
        <div class="runway"><svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Parts by last safe order week. Bar height uses a square root scale"><line x1="0" x2="${W}" y1="116" y2="116" stroke="rgb(255 255 255 / .16)"/>${bar}</svg></div>
      </div>
      <div><div class="band-head"><h3>Twin stock you can move</h3><span style="font-size:13px;color:rgb(255 255 255 / .7)"><b class="num" style="color:#fff">${D.twinCount}</b> for this turnaround</span></div>
        <div class="offers">${D.twins.map((t) => `<div class="offer"><div><div class="offer-name">${t.name}</div><div class="offer-sub">to ${t.no} from ${t.twin.donor}</div></div><div class="offer-grid"><div><small>Need</small><b class="num">${num(t.gap)}</b></div><div style="text-align:right"><small>Twin has spare</small><b class="num">${num(t.twin.surplus)}</b></div></div></div>`).join("")}</div>
      </div>
    </div></div>`;
  }

  /* ---------- matrix ---------- */
  const SC = { READY: "var(--ready)", LATER: "#6f93d8", PLAN: "var(--plan)", ORDER_NOW: "var(--plan)", TOO_LATE: "var(--act)" };
  const ORD = { READY: 0, LATER: 1, PLAN: 2, ORDER_NOW: 3, TOO_LATE: 4 };
  const matrix = () => {
    const cols = D.grid.slice().sort((a, b) => ORD[a[1]] - ORD[b[1]]);
    return `<div class="matrix" role="img" aria-label="${D.total} turnaround parts, ${D.counts.READY} ready, ${D.counts.ORDER_NOW} order this week, ${D.counts.TOO_LATE} too late">${cols.map((c) => `<i style="background:${SC[c[1]]}"></i>`).join("")}</div>`;
  };

  /* ---------- option A ---------- */
  function callouts(model) {
    return D.machines[model].parts.map((p, i) => `<div class="callout c${i}" data-anchor="${p.anchor}"><span class="co-go">${ic("up", "")}</span><h4>${p.name}</h4><div class="co-tag">${p.tag} · class ${p.crit}</div><div class="co-num num">${num(p.stock)}<small> / ${num(p.need)} ${p.unit}</small></div><div class="co-lead">Takes ${p.lead} days to arrive</div></div>`).join("");
  }
  function viewA() {
    const m = D.machines.pump;
    return `<div class="a-page"><div class="inner">
      <div class="a-top"><div class="logo" style="--logo:var(--accent)">${MARK}Sparekit</div>
        <nav class="a-nav" aria-label="Main">${NAV.map((n, i) => `<button type="button" ${i === 0 ? 'aria-current="page"' : ""} data-go="${i === 1 ? "todo" : i === 0 ? "shutdown" : ""}">${n}</button>`).join("")}</nav>
        <div class="a-right"><div class="search">${ic("search")}Find a part</div><button type="button" class="icbtn" aria-label="Alerts">${ic("bell")}<i class="badge"></i></button><button type="button" class="icbtn" aria-label="Settings">${ic("gear")}</button><span class="chipuser">MP</span></div></div>
      <div class="a-grid">
        <div style="min-width:0">
          <div class="crumb">Plant ${"›"} Cracker unit ${"›"} <b style="color:var(--ink2);font-weight:500">Turnaround 1 Nov 2026</b></div>
          <h1 class="a-title">Are we ready for<br>the next turnaround?</h1>
          <div class="tag-row" id="a-tags">${D.classes.filter((c) => ["Pumps", "Furnaces", "Heat exchangers"].includes(c.cls)).map((c) => {
            const k = c.cls === "Pumps" ? "pump" : c.cls === "Furnaces" ? "furnace" : "exchanger";
            return `<button type="button" class="tag" data-model="${k}" aria-pressed="${k === "pump"}"><span class="sq">${c.short}</span>${c.cls}</button>`;
          }).join("")}</div>
          <div class="stage" id="a-stage">
            <div class="thumbs" id="a-thumbs"></div>
            <canvas id="a-canvas" aria-label="3D model of a centrifugal pump. Drag to rotate."></canvas>
            <svg class="leaders" id="a-leaders" aria-hidden="true"></svg>
            <div id="a-callouts">${callouts("pump")}</div>
            <div class="stage-tools"><button type="button" class="pillbtn" id="a-explode">${ic("layers")}<span>Open the machine</span></button><span class="pillnote">Drag to rotate · <span id="a-short">${m.short} of ${m.total} ${m.cls.toLowerCase()} parts short</span></span></div>
          </div>
        </div>
        <aside class="side">
          <div class="period"><span>Turnaround size</span><span class="sw"><button type="button">Smaller</button><button type="button" aria-pressed="true">Same as last</button><button type="button">Bigger</button></span></div>
          <div class="panel"><div class="panel-head">A and B readiness <span class="arrow" style="width:26px;height:26px;background:none;color:var(--ink2);box-shadow:inset 0 0 0 1px var(--line)">${ic("up", "")}</span></div>
            <div class="gauge">${tickGauge(abPct, "#f0671c", "#ece5de")}<div class="gauge-num"><b class="num">${abPct}%</b><span>${abTotal - abReady} A and B parts short</span></div></div>
            ${D.byCrit.map((c) => `<div class="kv"><span><i class="crit ${c.crit}" style="font-style:normal">${c.crit}</i>${c.ready} of ${c.total} ready</span><b>${Math.round((c.ready / c.total) * 100)}%</b></div>`).join("")}
          </div>
          <div class="panel"><div class="panel-head">Alerts <span class="num" style="font-weight:500;color:var(--ink2);font-size:12px">${D.days} days left</span></div>
            <div class="alert act"><i></i><div>${D.counts.TOO_LATE} parts can no longer arrive<small>Expedite or use a twin</small></div><time>Late</time></div>
            <div class="alert plan"><i></i><div>${D.counts.ORDER_NOW} must be ordered this week<small>Terminal lug, O-ring EPDM</small></div><time>2 Oct</time></div>
            <div class="alert ready"><i></i><div>${D.counts.READY} parts are ready<small>Nothing to do</small></div><time>Today</time></div>
          </div>
        </aside>
      </div>
      <div class="panel" style="margin-top:14px">
        <div class="matrix-head"><div><div style="font-size:13.5px;font-weight:600;margin-bottom:7px">Every part the last turnaround used</div><b class="num">${D.total}</b> <span>parts, one square each · ${rp(D.gapValue)} to buy</span></div><div class="legend"><span><i style="background:var(--ready)"></i>Ready ${D.counts.READY}</span><span><i style="background:var(--plan)"></i>Order this week ${D.counts.ORDER_NOW}</span><span><i style="background:var(--act)"></i>Too late ${D.counts.TOO_LATE}</span></div></div>
        ${matrix()}
      </div>
      <div class="section-gap"><div class="section-title">Where the turnaround stands <small>Data as of ${shortD(D.asOf, true)}</small></div><div class="cards">${metricCards()}</div></div>
    </div>${band()}</div>`;
  }

  /* ---------- option B ---------- */
  function monthChart(W, H, opts) {
    const o = opts || {}, m = D.months, n = m.length, pad = 26;
    const max = Math.max(...m.map((x) => x.parts));
    const x = (i) => (i / (n - 1)) * (W - 8) + 4, y = (v) => H - pad - (v / max) * (H - pad - 8);
    const path = (key) => m.map((d, i) => (i ? "L" : "M") + x(i).toFixed(1) + " " + y(d[key]).toFixed(1)).join(" ");
    const smooth = (key) => {
      let s = `M${x(0)} ${y(m[0][key])}`;
      for (let i = 1; i < n; i++) {
        const mx = (x(i - 1) + x(i)) / 2;
        s += ` C${mx} ${y(m[i - 1][key])} ${mx} ${y(m[i][key])} ${x(i)} ${y(m[i][key])}`;
      }
      return s;
    };
    return { x, y, path, smooth, pad, max, n };
  }
  function viewB() {
    const W = 560, H = 150, c = monthChart(W, H), cur = 6;
    const ticks = D.months.map((d, i) => (i % 2 === 0 ? `<text x="${c.x(i)}" y="${H - 8}" text-anchor="middle" font-size="10" fill="var(--ink3)" ${i === cur ? 'font-weight="700" style="fill:var(--ink)"' : ""}>${mLab(d.month)}</text>` : "")).join("");
    const grid = [0, 200, 400, 600].map((v) => `<line x1="0" x2="${W}" y1="${c.y(v)}" y2="${c.y(v)}" stroke="rgb(0 0 0 / .05)"/>`).join("");
    const area = `${c.smooth("parts")} L${c.x(c.n - 1)} ${H - c.pad} L${c.x(0)} ${H - c.pad} Z`;
    const nodes = ["A", "B", "S", "C"].map((k, i) => {
      const a = (i / 4) * Math.PI * 2 - Math.PI / 2, x = 100 + Math.cos(a) * 62, y = 100 + Math.sin(a) * 62;
      return `<circle cx="${x}" cy="${y}" r="11" fill="#14492f"/><text x="${x}" y="${y + 3.5}" text-anchor="middle" font-size="10" font-weight="600" fill="#fff">${k}</text>`;
    }).join("");
    const outer = Array.from({ length: 16 }, (_, i) => {
      const a = (i / 16) * Math.PI * 2, r = 88;
      return `<circle cx="${100 + Math.cos(a) * r}" cy="${100 + Math.sin(a) * r}" r="4.5" fill="${i % 4 === 0 ? "transparent" : "#bcc5bf"}"/>`;
    }).join("");
    return `<div class="b-page"><div class="b-sky" aria-hidden="true"></div><div class="inner">
      <div class="b-glass"><div class="b-map" id="b-map">
        <div class="b-head">
          <div class="b-logo">Spare<em>kit</em></div>
          <nav class="b-nav" aria-label="Main">${NAV.slice(0, 5).map((n, i) => `<button type="button" ${i === 0 ? 'aria-current="page"' : ""} data-go="${i === 1 ? "todo" : ""}">${n}</button>`).join("")}</nav>
          <div class="a-right" style="margin-left:auto"><div class="search">${ic("search")}Find a part</div><button type="button" class="icbtn" aria-label="Alerts">${ic("bell")}</button><button type="button" class="icbtn" aria-label="Settings">${ic("gear")}</button><div class="b-user"><i>MP</i><span>Maintenance planner<small>Turnaround ${shortD(D.taDate, true)}</small></span></div></div>
        </div>
        <canvas id="b-canvas" aria-label="3D model of the plant site with shortage contours"></canvas>
        <span class="b-note">Layout is a sketch. Furnace heights and contours use real counts.</span>
        <div class="b-bubbles" id="b-bubbles">${D.classes.map((c) => {
          const icon = { Pumps: "drop", Furnaces: "fire", Compressors: "wave", Turbines: "cog", "Heat exchangers": "swap" }[c.cls];
          return `<div class="bubble ${c.cls === "Furnaces" ? "lg" : ""}" data-anchor="${c.cls}"><i>${ic(icon, "")}</i><b class="num">${c.short}<small> / ${c.total}</small></b><span>${c.cls} short</span></div>`;
        }).join("")}</div>
        <div class="pin" id="b-pin" data-anchor="pin">${ic("pin")}</div>
        <div class="b-legend"><div class="ends"><span>Low</span><span style="color:var(--act-ink)">High</span></div><div class="grad"></div><span style="color:var(--ink2)">Parts short for the turnaround</span></div>
        <div class="b-tools"><button type="button" class="icbtn" aria-label="Layers">${ic("layers")}</button><button type="button" class="icbtn" aria-label="Zoom in">${ic("plus")}</button><button type="button" class="icbtn" aria-label="Zoom out">${ic("minus")}</button></div>
        <div class="b-cards">
          <div class="gcard"><div class="gcard-head">Parts used per month<div class="tabs"><span class="on">All time</span><span>Last TA</span><span>This year</span></div></div>
            <svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Parts moved each month, with turnaround parts dashed. Peak in December 2025 and January 2026.">
              <defs><linearGradient id="bg1" x1="0" x2="1"><stop offset="0" stop-color="#3fa85a"/><stop offset=".5" stop-color="#d9c41c"/><stop offset="1" stop-color="#f0a42a"/></linearGradient><linearGradient id="bg2" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="#d9c41c" stop-opacity=".25"/><stop offset="1" stop-color="#d9c41c" stop-opacity="0"/></linearGradient></defs>
              ${grid}<path d="${area}" fill="url(#bg2)"/><path d="${c.smooth("parts")}" fill="none" stroke="url(#bg1)" stroke-width="2.5"/><path d="${c.smooth("parts_ta")}" fill="none" stroke="#e8583f" stroke-width="1.6" stroke-dasharray="3 5"/>
              <line x1="${c.x(cur)}" x2="${c.x(cur)}" y1="6" y2="${H - c.pad}" stroke="#e3b713" stroke-width="2"/><circle cx="${c.x(cur)}" cy="${c.y(D.months[cur].parts)}" r="5.5" fill="#e3b713" stroke="#fff" stroke-width="2"/>
              <g transform="translate(${c.x(cur) + 14},${c.y(D.months[cur].parts) - 34})"><rect width="172" height="44" rx="10" fill="#fff" opacity=".96"/><text x="11" y="17" font-size="10" fill="var(--ink2)">Nov 2025, last turnaround starts</text><text x="11" y="34" font-size="12.5" font-weight="600" fill="var(--ink)">${D.months[cur].parts} parts, ${D.months[cur].parts_ta} for TA</text></g>
              ${ticks}
            </svg>
          </div>
          <div class="gcard"><div class="gcard-head">Turnaround clock</div>
            <div class="flow"><div class="flow-num"><b class="num">${D.days}</b><span>days left</span></div>
              <svg viewBox="0 0 200 200" role="img" aria-label="A and B parts are ${abPct} percent ready"><circle cx="100" cy="100" r="62" fill="none" stroke="#fff"/><circle cx="100" cy="100" r="62" fill="none" stroke="#14492f" stroke-width="2" stroke-dasharray="${(abPct / 100) * 389.6} 400" transform="rotate(-90 100 100)"/><circle cx="100" cy="100" r="42" fill="#fff" opacity=".65"/>${outer}${nodes}<text x="100" y="100" text-anchor="middle" font-size="19" font-weight="600" fill="var(--ink)">${abPct}%</text><text x="100" y="115" text-anchor="middle" font-size="9" fill="var(--ink2)">A + B ready</text></svg></div>
            <div class="fresh"><i>${ic("clock")}</i><div>2 orders due this week<small>2 Oct and 4 Oct are the last safe days</small></div></div>
          </div>
          <div class="gcard"><div class="gcard-head">Max vs one turnaround<span style="display:flex;gap:9px;font-size:11px;font-weight:400;color:var(--ink2)"><span><i style="display:inline-block;width:8px;height:8px;border-radius:50%;background:var(--ready);margin-right:4px"></i>Max</span><span><i style="display:inline-block;width:8px;height:8px;border-radius:50%;background:var(--plan);margin-right:4px"></i>Used</span></span></div>
            <ul class="dumb">${PROOF.map((p) => `<li><div class="ln"><span>${p[0]}</span><span class="num">${p[1]} → <b style="color:var(--act-ink)">${p[2]}</b></span></div><div class="tr"><em style="width:${(p[2] / 205) * 100}%;background:var(--plan)"></em><em style="width:${(p[1] / 205) * 100}%;background:var(--ready)"></em></div></li>`).join("")}</ul>
            <div class="offset"><svg viewBox="0 0 28 28" aria-hidden="true"><path d="M14 2C7 9 5 14 5 18a9 9 0 0 0 18 0c0-4-2-9-9-16z" fill="#2fb765"/><path d="M14 2v25a9 9 0 0 0 9-9c0-4-2-9-9-16z" fill="#7be89c"/></svg><div><span>Stock sitting above Max</span><b class="num">${rp(D.overValue)}</b></div></div>
          </div>
        </div>
      </div></div>
      <div class="b-lower"><div class="section-title">Where the turnaround stands <small>Data as of ${shortD(D.asOf, true)}</small></div><div class="cards">${metricCards()}</div></div>
    </div><div style="position:relative">${band()}</div></div>`;
  }

  /* ---------- option C ---------- */
  function viewC() {
    return `<div class="c-page"><div class="inner">
      <div class="c-top"><button type="button" class="c-round" aria-label="Menu">${ic("menu")}</button><div class="c-logo"><i style="--logo:#111">${MARK}</i>sparekit</div>
        <nav class="c-nav" aria-label="Main">${NAV.slice(0, 4).map((n, i) => `<button type="button" ${i === 0 ? 'aria-current="page"' : ""} data-go="${i === 1 ? "todo" : ""}">${n}</button>`).join("")}</nav>
        <div class="a-right" style="margin-left:0"><button type="button" class="c-round" aria-label="Find a part">${ic("search")}</button><button type="button" class="c-round" aria-label="Alerts">${ic("bell")}</button><span style="font-size:12.5px;line-height:1.2;font-weight:600">Planner<small style="display:block;font-weight:400;color:var(--ink2);font-size:11px">Cracker unit</small></span></div></div>
      <div class="c-grid">
        <div>
          <h1 class="c-h1">Turnaround<br>readiness</h1>
          <div class="c-chips" id="c-chips"><button type="button" data-k="ab" aria-pressed="true">A + B parts</button><button type="button" data-k="all" aria-pressed="false">All 360</button></div>
          <div class="c-big"><b class="num"><span id="c-num">${abPct}</span><sup>%</sup></b><div class="c-delta"><b id="c-short">${abTotal - abReady} short</b>${D.days} days left<br>${shortD(D.taDate, true)}</div></div>
          <div class="needle" id="c-needle">${needleGauge(abPct)}</div>
          <div class="c-two">
            <button type="button" class="mcard"><div class="mcard-top"><span class="mcard-ico">${ic("box")}</span><span class="arrow">${ic("up", "")}</span></div><div><div class="mcard-sub">To buy, priced parts</div><div class="mcard-num num">${rp(D.gapValue).replace(" B", "")}<small>B</small></div></div></button>
            <button type="button" class="mcard"><i class="c-alert"></i><div class="mcard-top"><span class="mcard-ico">${ic("wave")}</span><span class="arrow">${ic("up", "")}</span></div><div><div class="mcard-sub">Stock above Max</div><div class="mcard-num num">${rp(D.overValue).replace(" B", "")}<small>B</small></div></div></button>
          </div>
        </div>
        <div class="c-3d"><canvas id="c-canvas" aria-label="3D model of a centrifugal pump in graphite. Drag to rotate."></canvas><div class="caption"><span class="tagpill num">${D.machines.pump.short} of ${D.machines.pump.total} pump parts short</span><button type="button" class="pillbtn" id="c-explode" style="height:30px;font-size:12px">Open</button></div></div>
        <div class="cards c-cards">${metricCards()}</div>
      </div>
    </div>${band()}</div>`;
  }

  /* ---------- ref 4: to do ---------- */
  const done = new Set();
  let selMonth = 6;
  const taskList = () => D.tasks.filter((t) => !done.has(t.no));
  const pill = (t) => (t.twin ? `Twin +${num(t.twin.surplus)}` : t.status === "ORDER_NOW" ? `By ${shortD(t.orderBy)}` : `${t.lead} d to arrive`);
  const cls = (t) => (t.twin ? "twin" : t.status === "ORDER_NOW" ? "now" : "late");
  function unitDots(t) {
    const cap = 28, total = Math.max(1, t.need), have = Math.min(t.stock, t.need);
    const n = Math.min(cap, total), g = Math.round((have / total) * n);
    return `<div class="unitdots" role="img" aria-label="${num(t.stock)} of ${num(t.need)} ${t.unit} in stock${total > cap ? ", scaled" : ""}">${Array.from({ length: n }, (_, i) => `<i style="background:${i < g ? "#37b679" : t.twin ? "#6cc4b4" : "#e98a7b"}"></i>`).join("")}</div>`;
  }
  const taskCard = (t) => `<article class="task ${cls(t)}">
    <div class="task-h"><span class="tav ${t.crit}">${t.crit}</span><div style="min-width:0"><div class="task-name">${t.name}</div><span class="task-pill">${ic("clock", "ic")}${pill(t)}</span></div></div>
    <div class="task-stats"><span>${ic("box")}<b>${num(t.stock)}</b>/${num(t.need)} ${t.unit}</span><span>${ic("cal")}${t.status === "TOO_LATE" ? "Late" : shortD(t.orderBy)}</span></div>
    <hr>
    <div class="task-tag"><b>${t.tag}</b><span>${t.nEq} ${t.nEq === 1 ? "place" : "places"}</span></div>
    ${unitDots(t)}
    <div class="task-foot"><span class="task-id">${t.no}</span><div class="do"><button type="button" class="n" data-no="${t.no}" data-act="reject" aria-label="Reject ${t.name}">${ic("x", "")}</button><button type="button" class="y" data-no="${t.no}" data-act="ok" aria-label="${t.twin ? "Move from twin" : `Order ${t.gap} ${t.unit}`}: ${t.name}">${ic("check", "")}</button></div></div>
  </article>`;

  function todoInner(thumb) {
    const left = taskList();
    const decided = done.size, total = D.alerts.act;
    const first = left[0];
    return `<div class="td-frame">
      <div class="td-brand">${MARK}<span>Sparekit</span></div>
      <div class="player"><div class="player-time num">${decided} of ${total} decided</div><div class="player-bar" role="img" aria-label="Queue: ${D.counts.TOO_LATE} turnaround parts too late, the rest other urgent parts"><i style="width:${Math.max(0.5, (decided / total) * 100)}%;background:var(--ready)"></i><i style="width:${(D.counts.TOO_LATE / total) * 100}%;background:var(--act)"></i><i style="width:${(D.counts.ORDER_NOW / total) * 100 + 1}%;background:var(--plan)"></i></div><div class="player-ctl"><button type="button" aria-label="Previous part">${ic("prev")}</button><button type="button" class="main" aria-label="Decide next part" data-next="1">${ic("play")}</button><button type="button" aria-label="Skip part" data-skip="1">${ic("next")}</button></div></div>
      <div class="presence"><span><b class="num" style="color:var(--act-ink)">${D.alerts.act}</b> act now</span><span><b class="num">${D.alerts.twin}</b> use twin</span><span><b class="num">${num(D.alerts.plan)}</b> plan</span></div>
      <div class="td-rail"><button type="button" aria-label="Shutdown" data-go="shutdown">${ic("cal")}</button><button type="button" class="on" aria-label="To do">${ic("list")}</button><button type="button" aria-label="Stock">${ic("box")}</button><button type="button" aria-label="Forecast">${ic("chart")}<span class="count">3</span></button><button type="button" aria-label="What if">${ic("sliders")}</button><button type="button" class="gap" aria-label="Data check">${ic("shield")}</button></div>
      <div class="td-main">
        <div class="td-top"><div><h2 class="td-h">What should we do?</h2><div class="td-sub">Parts used per month, ${mLab(D.months[0].month)} 2025 to ${mLab(D.months[16].month)} 2026</div></div><div class="td-range"><span class="on">Months</span><span>Weeks</span><span>Days</span></div></div>
        <div class="dates" id="td-dates">${D.months.map((m, i) => `<button type="button" class="date ${m.parts_ta > 150 ? "ta" : ""}" data-m="${i}" aria-pressed="${i === selMonth}"><b>${mLab(m.month)}</b>${m.month.slice(2, 4)}</button>`).join("")}</div>
        <div class="tl" id="td-tl">${timeline()}</div>
        <div class="td-section"><h3 class="td-h">Urgent now</h3><span class="td-sub">${D.alertTotal.toLocaleString("en-US")} parts have an action. The most urgent sit first.</span></div>
        <div class="tasks">${left.length ? left.slice(first ? 1 : 0).map(taskCard).join("") : ""}${!left.length ? `<div class="toast-done">You decided every part in this sample. Reset by switching option.</div>` : ""}</div>
      </div>
      <aside class="td-side">
        <div style="display:grid;gap:7px"><h4>Use twin</h4>${D.twins.slice(0, 2).map((t) => `<div class="mini"><span class="tav ${t.crit}">${t.crit}</span><div style="min-width:0"><b>${t.name}</b><small>+${num(t.twin.surplus)} on ${t.twin.donor}</small></div></div>`).join("")}</div>
        <div style="display:grid;gap:7px"><h4>This week</h4>${D.now.map((t) => `<div class="mini"><span class="tav ${t.crit}">${t.crit}</span><div style="min-width:0"><b>${t.name}</b><small>Need ${num(t.need)} ${t.unit}</small></div><span class="when">${shortD(t.orderBy)}</span></div>`).join("")}</div>
        <div class="bigstat"><small>Cost to close the gap</small><b class="num">${rp(D.gapValue)}</b>${thumb ? `<img src="${thumb}" alt="">` : ""}</div>
      </aside>
      ${first ? `<div class="lift ${cls(first)}"><div class="lift-eyebrow">Decide next</div><div class="task-h"><span class="tav ${first.crit}">${first.crit}</span><div style="min-width:0"><div class="task-name">${first.name}</div><span class="task-pill" style="background:var(--act)">${ic("truck")}${pill(first)}</span></div></div>${unitDots(first)}<div class="task-stats"><span>${ic("box")}<b>${num(first.stock)}</b>/${num(first.need)} ${first.unit}</span><span class="num">${first.tag}</span></div><div class="do-big"><button type="button" class="n" data-no="${first.no}" data-act="reject">Reject</button><button type="button" class="y" data-no="${first.no}" data-act="ok">${first.twin ? "Move from twin" : `Order ${num(first.gap)} ${first.unit}`}</button></div></div>` : ""}
    </div>`;
  }
  function timeline() {
    const W = 880, H = 190, c = monthChart(W, H);
    const step = (key) => {
      let s = "";
      D.months.forEach((d, i) => {
        const x = c.x(i), y = c.y(d[key]);
        if (!i) s = `M${x} ${y}`;
        else {
          const mid = (c.x(i - 1) + x) / 2, py = c.y(D.months[i - 1][key]);
          s += ` L${mid - 5} ${py} L${mid + 5} ${y} L${x} ${y}`;
        }
      });
      return s;
    };
    const g = [200, 400, 600].map((v) => `<line x1="0" x2="${W}" y1="${c.y(v)}" y2="${c.y(v)}" stroke="rgb(0 0 0 / .07)"/><text x="0" y="${c.y(v) - 4}" font-size="11" fill="var(--ink3)">${v}</text>`).join("");
    const m = D.months[selMonth];
    return `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Parts moved each month as a solid line, turnaround parts as a dotted line."><rect x="${c.x(6)}" width="${c.x(8) - c.x(6)}" y="0" height="${H - c.pad}" fill="rgb(255 255 255 / .4)" rx="8"/>${g}<path d="${step("parts")}" fill="none" stroke="#3b8f83" stroke-width="2"/><path d="${step("parts_ta")}" fill="none" stroke="#d8402a" stroke-width="2" stroke-dasharray="1 6" stroke-linecap="round"/>${D.months.map((d, i) => `<text x="${c.x(i)}" y="${H - 7}" text-anchor="middle" font-size="11" fill="var(--ink2)">${mLab(d.month)}</text>`).join("")}<text x="${(c.x(6) + c.x(8)) / 2}" y="${H - c.pad - 7}" text-anchor="middle" font-size="11" fill="var(--ink2)">Last turnaround</text></svg>
      <div class="tl-pop" style="left:${(c.x(selMonth) / W) * 100}%"><div class="strip"><i style="width:${(m.parts_ta / m.parts) * 100}%;background:var(--act)"></i><i style="flex:1;background:#58c29a"></i></div><div class="lab">${mLab(m.month)} ${m.month.slice(0, 4)}</div><b class="num">${m.parts}</b><small>parts moved<br>${m.parts_ta} for TA</small></div>`;
  }

  /* ---------- mount ---------- */
  const THUMB = { a: null };
  const ROOT = {
    a: $("#opt-a"),
    b: $("#opt-b"),
    c: $("#opt-c"),
  };
  const state = { view: "a", screen: "shutdown", compare: false, x: 50 };
  try { Object.assign(state, JSON.parse(localStorage.getItem("sk-cur") || "{}")); state.compare = false; } catch (e) {}
  const scenes = {};

  function mount() {
    ROOT.a.querySelector(".screen-shutdown").innerHTML = viewA();
    ROOT.b.querySelector(".screen-shutdown").innerHTML = viewB();
    ROOT.c.querySelector(".screen-shutdown").innerHTML = viewC();
    renderTodo();
  }
  function renderTodo() {
    ["a", "b", "c"].forEach((k) => {
      ROOT[k].querySelector(".screen-todo").innerHTML = `<div class="td-page"><div class="inner">${todoInner(THUMB.a && THUMB.a.pump)}</div></div>`;
    });
  }

  /* leaders from fixed callout cards to the live 3D anchors */
  function drawLeaders(api) {
    const stage = $("#a-stage"), svg = $("#a-leaders");
    if (!stage || !stage.offsetWidth || getComputedStyle(svg).display === "none") return;
    const sr = stage.getBoundingClientRect();
    let html = "";
    $$("#a-callouts .callout").forEach((c) => {
      const p = api.project(c.dataset.anchor);
      if (!p) return;
      const r = c.getBoundingClientRect();
      const left = r.left - sr.left + r.width / 2 < p.x;
      const sx = left ? r.right - sr.left : r.left - sr.left, sy = r.top - sr.top + 22;
      const ex = sx + (left ? 18 : -18);
      html += `<polyline points="${sx.toFixed(1)},${sy.toFixed(1)} ${ex.toFixed(1)},${sy.toFixed(1)} ${p.x.toFixed(1)},${p.y.toFixed(1)}"/><circle cx="${p.x.toFixed(1)}" cy="${p.y.toFixed(1)}" r="4"/>`;
    });
    if (svg._h !== html) {
      svg.innerHTML = html;
      svg._h = html;
    }
  }
  function placeBubbles(api) {
    const top = $("#b-canvas").offsetTop;
    $$("#b-map [data-anchor]").forEach((b) => {
      const p = api.project(b.dataset.anchor);
      if (p) b.style.transform = `translate3d(${p.x.toFixed(1)}px,${(p.y + top).toFixed(1)}px,0)`;
    });
  }
  function ensureScene(k) {
    if (scenes[k] || !window.THREE || !window.SKScenes) return;
    try {
      if (k === "a") {
        scenes.a = SKScenes.Machine($("#a-canvas"), { palette: "hall", model: "pump", onFrame: drawLeaders });
        if (THUMB.a) $("#a-thumbs").innerHTML = Object.keys(THUMB.a).map((m, i) => `<button type="button" class="thumb" data-model="${m}" aria-pressed="${i === 0}" aria-label="Show ${m}"><img src="${THUMB.a[m]}" alt=""></button>`).join("");
      }
      if (k === "b") scenes.b = SKScenes.Plant($("#b-canvas"), { furnaces: D.furnaces, classes: D.classes, onFrame: placeBubbles });
      if (k === "c") scenes.c = SKScenes.Machine($("#c-canvas"), { palette: "deck", model: "pump", fitK: 1.3 });
    } catch (e) {
      console.error(e);
      const cv = $(`#${k}-canvas`);
      if (cv) cv.insertAdjacentHTML("afterend", `<p style="position:absolute;inset:auto 0 50%;text-align:center;color:var(--ink2);font-size:13px">3D needs WebGL, which this browser has turned off.</p>`);
    }
  }
  function setModel(m) {
    scenes.a && scenes.a.load(m);
    $("#a-callouts").innerHTML = callouts(m);
    $$("#a-tags .tag, #a-thumbs .thumb").forEach((b) => b.setAttribute("aria-pressed", b.dataset.model === m));
    const x = D.machines[m];
    $("#a-short").textContent = `${x.short} of ${x.total} ${x.cls.toLowerCase()} parts short`;
    $("#a-explode span").textContent = "Open the machine";
    $("#a-canvas").setAttribute("aria-label", `3D model of ${m}. Drag to rotate.`);
    $("#a-leaders")._h = null;
  }

  const BRIEF = {
    before: "<b>Before.</b> Screenshot of the running app at 1440 px. Top nav, flat white panels, 2D isometric furnace chart.",
    a: "<b>A · Machine Hall.</b> Hero and side panel from reference 2, metric cards and dark band from 3, to-do from 4. Real 3D machines with callouts on parts that are actually short.",
    b: "<b>B · Plant Map.</b> Hero from reference 1: glass panels over a 3D clay model of the plant with shortage contours. Metric cards from 3, to-do from 4, closest to the mint look.",
    c: "<b>C · Control Deck.</b> Layout from reference 3 first: big number, needle, six cards, dark band. The machine turns graphite and sits in the amber haze. To-do from 4.",
  };

  function apply() {
    const v = state.view;
    const before = v === "before";
    $("#opt-before").hidden = !before;
    ["a", "b", "c"].forEach((k) => {
      ROOT[k].hidden = v !== k;
      ROOT[k].querySelector(".screen-shutdown").hidden = state.screen !== "shutdown";
      ROOT[k].querySelector(".screen-todo").hidden = state.screen !== "todo";
    });
    $$(".before img").forEach((i) => (i.hidden = i.dataset.s !== state.screen));
    $$("#seg-view button").forEach((b) => b.setAttribute("aria-pressed", b.dataset.v === v));
    $$("#seg-screen button").forEach((b) => b.setAttribute("aria-pressed", b.dataset.s === state.screen));
    $("#brief").innerHTML = BRIEF[v];
    const tog = $("#btn-compare");
    tog.disabled = before;
    tog.setAttribute("aria-pressed", state.compare && !before);
    renderCompare();
    Object.entries(scenes).forEach(([k, s]) => (k === v && state.screen === "shutdown" ? s.start() : s.stop()));
    if (!before && state.screen === "shutdown") {
      ensureScene(v);
      scenes[v] && scenes[v].start();
    }
    try { localStorage.setItem("sk-cur", JSON.stringify({ view: state.view, screen: state.screen })); } catch (e) {}
  }
  function renderCompare() {
    const on = state.compare && state.view !== "before";
    const c = $("#cmp");
    c.hidden = !on;
    if (!on) return;
    $("#cmp-img").style.clipPath = `inset(0 ${100 - state.x}% 0 0)`;
    $("#cmp-handle").style.left = state.x + "%";
    const src = $(`.before img[data-s="${state.screen}"]`);
    $("#cmp-pic").src = src.src;
  }

  /* picks */
  const picks = { hero: "", cards: "", todo: "" };
  try { Object.assign(picks, JSON.parse(localStorage.getItem("sk-picks") || "{}")); } catch (e) {}
  function renderPicks() {
    $$(".pick [data-group]").forEach((b) => b.setAttribute("aria-pressed", picks[b.dataset.group] === b.dataset.val));
    const note = $("#pick-note").value.trim();
    const lines = [`Hero: ${picks.hero || "-"}`, `Kartu metrik: ${picks.cards || "-"}`, `To-do: ${picks.todo || "-"}`];
    if (note) lines.push(`Catatan: ${note}`);
    $("#pick-out").textContent = lines.join("\n");
    $$("#seg-view button").forEach((b) => b.classList.toggle("is-pick", picks.hero === b.dataset.v?.toUpperCase()));
    try { localStorage.setItem("sk-picks", JSON.stringify(picks)); } catch (e) {}
  }

  document.addEventListener("click", (e) => {
    const t = e.target.closest("button");
    if (!t) return;
    if (t.dataset.v) { state.view = t.dataset.v; apply(); return; }
    if (t.dataset.s) { state.screen = t.dataset.s; apply(); return; }
    if (t.dataset.go) { state.screen = t.dataset.go; apply(); scrollTo({ top: 0 }); return; }
    if (t.dataset.model) { setModel(t.dataset.model); return; }
    if (t.id === "a-explode") { const o = scenes.a && scenes.a.toggleExplode(); $("#a-explode span").textContent = o ? "Close the machine" : "Open the machine"; return; }
    if (t.id === "c-explode") { const o = scenes.c && scenes.c.toggleExplode(); t.textContent = o ? "Close" : "Open"; return; }
    if (t.id === "btn-compare") { state.compare = !state.compare; apply(); return; }
    if (t.id === "btn-pick") { const p = $("#pick"); p.hidden = !p.hidden; t.setAttribute("aria-pressed", !p.hidden); return; }
    if (t.dataset.group) { picks[t.dataset.group] = t.dataset.val; renderPicks(); return; }
    if (t.id === "pick-copy") {
      const txt = $("#pick-out").textContent;
      const ok = () => { t.textContent = "Tersalin"; setTimeout(() => (t.textContent = "Salin pilihan"), 1500); };
      (navigator.clipboard ? navigator.clipboard.writeText(txt) : Promise.reject()).then(ok, () => {
        const r = document.createRange(); r.selectNodeContents($("#pick-out")); const s = getSelection(); s.removeAllRanges(); s.addRange(r); t.textContent = "Tekan Ctrl+C";
      });
      return;
    }
    if (t.dataset.m != null) {
      selMonth = +t.dataset.m;
      $$("[data-m]").forEach((b) => b.setAttribute("aria-pressed", +b.dataset.m === selMonth));
      $$(".tl").forEach((tl) => (tl.innerHTML = timeline()));
      return;
    }
    if (t.dataset.no) { done.add(+t.dataset.no); renderTodo(); return; }
    if (t.dataset.next) { const n = taskList()[0]; if (n) { done.add(n.no); renderTodo(); } return; }
    if (t.dataset.skip) { const n = taskList()[0]; if (n) { D.tasks.push(D.tasks.splice(D.tasks.indexOf(n), 1)[0]); renderTodo(); } return; }
    const c = t.closest("#c-chips");
    if (c && t.dataset.k) {
      const all = t.dataset.k === "all";
      $$("#c-chips button").forEach((b) => b.setAttribute("aria-pressed", b === t));
      const p = all ? allPct : abPct;
      $("#c-num").textContent = p;
      $("#c-short").textContent = (all ? D.total - allReady : abTotal - abReady) + " short";
      $("#c-needle").innerHTML = needleGauge(p);
    }
  });
  $("#pick-note").addEventListener("input", renderPicks);

  /* compare drag */
  (function () {
    const h = $("#cmp-handle");
    let on = false;
    const mv = (e) => {
      const r = $("#stage").getBoundingClientRect();
      state.x = Math.max(0, Math.min(100, ((e.clientX - r.left) / r.width) * 100));
      renderCompare();
    };
    h.addEventListener("pointerdown", (e) => { on = true; h.setPointerCapture(e.pointerId); mv(e); });
    h.addEventListener("pointermove", (e) => on && mv(e));
    h.addEventListener("pointerup", () => (on = false));
    h.addEventListener("keydown", (e) => {
      if (e.key === "ArrowLeft") state.x = Math.max(0, state.x - 4);
      if (e.key === "ArrowRight") state.x = Math.min(100, state.x + 4);
      renderCompare();
    });
  })();

  /* boot */
  if (window.THREE && window.SKScenes) {
    try { THUMB.a = SKScenes.thumbs("hall"); } catch (e) { console.error(e); }
  }
  mount();
  apply();
  renderPicks();
})();

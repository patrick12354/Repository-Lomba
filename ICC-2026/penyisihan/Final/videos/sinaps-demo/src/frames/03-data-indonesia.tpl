<!doctype html>
<html><head><meta charset="UTF-8" /></head><body><template>
<style>
<!-- @base -->
#f03 { position: absolute; inset: 0; background: transparent; overflow: hidden; }
#f03 .rail { position: absolute; left: 0; top: 0; width: 5760px; height: 1080px; }
#f03 .pnl { position: absolute; top: 0; width: 1920px; height: 1080px; }
/* panel A: peta + 18,5% */
#f03 .pa .big { position: absolute; left: 110px; top: 110px; font-family: 'Oswald', sans-serif; font-weight: 700; font-size: 300px; line-height: .85; color: var(--brick); letter-spacing: -.01em; }
#f03 .pa .big small { font-size: 150px; }
#f03 .pa .say { position: absolute; left: 790px; top: 150px; width: 700px; font-size: 64px; line-height: 1.12; font-weight: 700; }
#f03 .pa .say b { color: var(--brick); }
#f03 .pa .intro { position: absolute; left: 0; right: 0; top: 160px; text-align: center; font: 700 76px/1.1 'Oswald', sans-serif; text-transform: uppercase; letter-spacing: .03em; color: var(--ink); }
#f03 .pa .intro b { color: var(--nt-d); }
#f03 .pa .map { position: absolute; left: 150px; top: 520px; width: 1620px; }
#f03 .pa .dk { position: absolute; left: 880px; top: 420px; }
/* panel B: otak + 1.900.000 */
#f03 .pb .brain { position: absolute; left: 10px; top: 210px; width: 860px; height: 685px; }
#f03 .pb .clock { position: absolute; left: 1650px; top: 120px; display: flex; align-items: center; gap: 20px; }
#f03 .pb .clock svg { width: 150px; height: 150px; }
#f03 .pb .clock span { font: 700 44px 'Geist', sans-serif; color: var(--muted); font-variant-numeric: tabular-nums; }
#f03 .pb .stat { position: absolute; right: 110px; top: 330px; text-align: right; }
#f03 .pb .num { font-family: 'Oswald', sans-serif; font-weight: 700; font-size: 222px; line-height: .9; color: var(--ink); font-variant-numeric: tabular-nums; letter-spacing: -.01em; }
#f03 .pb .lbl { font-size: 60px; font-weight: 700; margin-top: 26px; color: var(--ink); }
#f03 .pb .lbl b { color: var(--bad); }
#f03 .pb .rule { width: 620px; height: 8px; border-radius: 4px; background: var(--line); margin: 34px 0 0 auto; position: relative; }
#f03 .pb .rule i { position: absolute; right: 0; top: 0; bottom: 0; width: 46%; background: var(--bad); }
#f03 .pb .win45 { position: absolute; right: 110px; top: 760px; display: flex; align-items: center; gap: 26px; font: 700 44px 'Arvo', serif; color: var(--ink-2); }
#f03 .pb .win45 svg { width: 110px; height: 110px; }
#f03 .pb .win45 b { color: var(--nt-d); font: 700 120px/1 'Oswald', sans-serif; margin-right: 6px; }
/* panel C: radiolog */
#f03 .pc .rad { position: absolute; left: 90px; top: 170px; }
#f03 .pc .tag { position: absolute; left: 130px; top: 110px; padding: 10px 22px; border-radius: 999px; background: var(--teal); color: #fff; font: 700 30px 'Geist', sans-serif; }
#f03 .pc .q { position: absolute; }
#f03 .pc .tag2 { position: absolute; left: 300px; top: 110px; padding: 10px 22px; border-radius: 999px; background: var(--nt); color: #fff; font: 700 30px 'Geist', sans-serif; white-space: nowrap; }
#f03 .pc .card { position: absolute; right: 90px; top: 110px; width: 760px; height: 860px; border-radius: 28px; padding: 56px 60px; background: #fff; border: 2px solid var(--line); box-shadow: 0 1px 2px rgba(16,24,40,.04), 0 14px 36px rgba(16,24,40,.07); }
#f03 .pc .card .h { font: 600 36px 'Geist', sans-serif; color: var(--muted); }
#f03 .pc .row { margin-top: 34px; }
#f03 .pc .row .lb { display: flex; justify-content: space-between; align-items: baseline; font-size: 44px; font-weight: 700; }
#f03 .pc .row .v { font-family: 'Oswald', sans-serif; font-weight: 700; font-size: 140px; line-height: 1; }
#f03 .pc .row .track { margin-top: 16px; height: 38px; border-radius: 19px; background: #f1f5f9; overflow: hidden; }
#f03 .pc .row .fill { height: 100%; border-radius: 19px; }
#f03 .pc .cmpx { margin-top: 40px; display: flex; align-items: center; gap: 26px; padding: 22px 28px; border-radius: 22px; background: var(--bad-soft); }
#f03 .pc .cmpx .x { font: 700 130px/1 'Oswald', sans-serif; color: var(--bad); }
#f03 .pc .cmpx .xt { font-size: 36px; line-height: 1.2; font-weight: 700; color: var(--ink); }
</style>
<div id="f03" data-composition-id="f03" data-width="1920" data-height="1080">
  <div class="rail">
    <div class="pnl pa" style="left: 1920px">
      <div class="big"><span class="v">0</span><small>%</small></div>
      <div class="say">kematian di Indonesia akibat <b>stroke.</b></div>
      <svg class="map" viewBox="0 0 1610 560"><g class="islands"></g><g class="pings"></g></svg>
    </div>
    <div class="pnl pb" style="left: 0px">
      <svg class="brain" viewBox="0 0 1080 860"><path class="outline" d="M180,430 C150,300 230,170 380,130 C470,80 600,80 700,120 C820,150 920,240 940,360 C960,470 900,560 800,590 C760,600 720,600 690,610 C660,650 640,700 610,760 C590,800 560,800 560,760 C560,720 570,680 560,650 C500,640 420,640 330,620 C230,600 190,520 180,430 Z M690,610 C740,600 820,610 840,660 C830,720 740,740 680,700" fill="none" stroke="#d1d5db" stroke-width="3" /><g class="edges"></g><g class="nodes"></g></svg>
      <div class="clock">
        <svg viewBox="-40 -40 80 80"><circle r="34" fill="none" stroke="#e5e7eb" stroke-width="6" /><circle class="clock-arc" r="34" fill="none" stroke="#dc2626" stroke-width="6" stroke-linecap="round" stroke-dasharray="213.6" stroke-dashoffset="0" transform="rotate(-90)" /><line class="clock-hand" x1="0" y1="0" x2="0" y2="-22" stroke="#10313a" stroke-width="5" stroke-linecap="round" /></svg>
      </div>
      <div class="stat">
        <div class="num">0</div>
        <div class="lbl">neuron <b>hilang</b> setiap menit</div>
      </div>
      <div class="win45"><svg width="70" height="70" viewBox="0 0 70 70"><path d="M18,8 h34 M18,62 h34 M22,8 c0,18 26,18 26,27 c0,9 -26,9 -26,27 M48,8 c0,18 -26,18 -26,27 c0,9 26,9 26,27" fill="none" stroke="#10313a" stroke-width="5" stroke-linecap="round" /><path class="sand" d="M28,52 h14 l-7,-9 z" fill="#e07a1f" /></svg><span><b>4,5 jam</b><br />batas waktu obat</span></div>
    </div>
    <div class="pnl pc" style="left: 3840px">
      <div class="q" style="left:420px; top:430px"><!-- @include mhs w=118 q=1 --></div>
      <div class="q" style="left:525px; top:476px"><!-- @include mhs w=118 hair=#3b2a20 skin=#e2b08e --></div>
      <div class="q" style="left:630px; top:453px"><!-- @include mhs w=118 skin=#a96f4c q=1 --></div>
      <div class="q" style="left:735px; top:499px"><!-- @include mhs w=118 hair=#5a3a28 --></div>
      <div class="q" style="left:840px; top:465px"><!-- @include mhs w=118 skin=#e2b08e hair=#2a2220 q=1 --></div>
      <div class="q" style="left:480px; top:660px"><!-- @include mhs w=118 skin=#c48d68 --></div>
      <div class="q" style="left:590px; top:695px"><!-- @include mhs w=118 hair=#3b2a20 q=1 --></div>
      <div class="q" style="left:700px; top:672px"><!-- @include mhs w=118 skin=#a96f4c --></div>
      <div class="q" style="left:810px; top:712px"><!-- @include mhs w=118 skin=#e2b08e q=1 --></div>
      <div class="q" style="left:920px; top:677px"><!-- @include mhs w=118 hair=#5a3a28 skin=#d39a76 --></div>
      <div class="rad"><!-- @include dika p=f03r w=330 hair=#9aa3a8 brow=#6b7280 glasses=1 skin=#e2b08e skin2=#c48d68 scrub=#5c4a7a smile=0 worried=1 brows=0 wbrows=1 sweat=1 --></div>
      <div class="tag">Radiolog</div>
      <div class="tag2">juga mengajar di kampus</div>
      <div class="card">
        <div class="h">Radiolog per 100.000 penduduk</div>
        <div class="row">
          <div class="lb"><span>Indonesia</span><span class="v" style="color: var(--bad)">0,8</span></div>
          <div class="track"><div class="fill" style="width: 6.3%; background: var(--bad)"></div></div>
        </div>
        <div class="row">
          <div class="lb"><span>Uni Eropa</span><span class="v" style="color: var(--teal)">12,7</span></div>
          <div class="track"><div class="fill" style="width: 100%; background: var(--teal)"></div></div>
        </div>
        <div class="cmpx"><span class="x">16×</span><span class="xt">lebih sedikit dari rerata Uni Eropa</span></div>
      </div>
    </div>
  </div>
</div>
<!-- @sfx woosh_up@0.0:0.5 punch_hit@0.42:0.4 tick@~jam:0.4 tock@~terus:0.4 tick@~berjalan:0.4 whoosh_deep@~Setiap-0.4:0.45 heartbeat_fast@~Setiap:0.4 tock@~otak:0.35 riser@~otak-0.2:0.35 counter_roll@~satu-0.6:0.4 impact_boom@~neuron+0.15:0.6 slide@~obat-0.2:0.4 clock_fast@~empat-0.3:0.4 punch_hit@~jam.2:0.5 swipe_zip@~Indonesia-0.8:0.45 data_chirps@~stroke:0.35 counter_roll@~delapan-0.3:0.4 impact_boom@~persen+0.2:0.55 snap@~kematian-0.3:0.4 swipe_zip@~Tapi-0.1:0.45 tension_hit@~langka:0.4 crowd_murmur@~Radiolog:0.25 counter_roll@~nol-0.2:0.35 punch_hit@~delapan.2:0.5 swish_fast@~enam-0.4:0.4 bass_drop@~kali-0.1:0.5 mar6@~Uni:0.4 pop@~mengajar-0.1:0.45 bubble@~kampus:0.35 -->
<script>
(() => {
/* @helpers */
  const ns = "http://www.w3.org/2000/svg";
  const RAIL = $1(".rail");
  // ---- panel A: kepulauan Indonesia (dari bujur/lintang yang disederhanakan) ----
  const P = (lon, lat) => [((lon - 95) * 34.8).toFixed(1), ((7 - lat) * 30).toFixed(1)];
  const I = {
    sumatra: [[95.3,5.6],[97.5,5.2],[98.7,3.8],[100.4,2.2],[101.5,1.6],[103.6,0.9],[104.5,-1],[106,-3],[105.9,-5.8],[104.6,-5.9],[103,-4.5],[101.6,-3.2],[100.3,-1],[99,1],[97.6,2.4],[96.2,4]],
    jawa: [[105.2,-6.8],[106,-5.9],[107,-6],[108.3,-6.3],[110.4,-6.9],[111.5,-6.6],[112.6,-6.9],[114.4,-7.7],[114.4,-8.6],[112,-8.3],[110,-8.1],[108,-7.8],[106.4,-7.4]],
    bali: [[115,-8.1],[115.7,-8.4],[115.2,-8.8]],
    lombok: [[116,-8.4],[116.7,-8.3],[116.4,-8.9]],
    sumbawa: [[116.8,-8.4],[119,-8.3],[118.8,-8.8],[117,-9]],
    flores: [[119.8,-8.4],[122.9,-8.1],[122.8,-8.7],[120,-8.8]],
    sumba: [[119,-9.4],[120.8,-9.6],[120.2,-10.3],[119,-9.8]],
    timor: [[123.5,-10.2],[125.1,-9.2],[127.3,-8.4],[124.9,-10],[123.7,-10.5]],
    kalimantan: [[109,1.5],[109.6,2],[111,1.6],[113,3],[115.4,4.5],[117,6.9],[119.2,5.2],[118,4.3],[118.5,3],[117.8,1],[119,0.9],[117.5,-0.8],[116.5,-2.5],[116,-3.8],[114.6,-4.1],[113,-3.1],[111.7,-3],[110.2,-2.9],[110,-1.2],[109,0]],
    sulawesi: [[119.4,-5.5],[120.4,-5.6],[120.3,-3],[121,-2.7],[122.5,-4.7],[123.2,-4.5],[121.9,-2.5],[122.9,-0.9],[121,-1.3],[120.6,-0.9],[121.3,0.4],[123,0.5],[124.8,1.5],[125.2,1.4],[123.5,0.9],[120.1,0.7],[119.8,-0.3],[118.8,-2.5],[119.4,-3.5]],
    halmahera: [[127.6,1.9],[128.2,1.5],[127.9,0.3],[128.7,-0.3],[127.8,-0.8],[127.3,0.7]],
    seram: [[128.2,-2.9],[130.8,-3.3],[129.5,-3.6],[128.2,-3.5]],
    buru: [[126,-3.1],[127.2,-3.3],[126.8,-3.8],[126,-3.6]],
    bangka: [[105.2,-1.6],[106.8,-2.7],[106.6,-3.1],[105.6,-2.2]],
    papua: [[131,-1.2],[132.3,-0.4],[134,-0.9],[135,-3.3],[137.5,-1.5],[141,-2.6],[141,-9.1],[139,-8.1],[138,-8.4],[137.6,-6.5],[136,-4.6],[134.2,-3.9],[133,-4],[132,-2.9],[133.4,-2.4],[132,-2.2]],
  };
  const G = $1(".islands");
  Object.entries(I).forEach(([name, pts]) => {
    const path = document.createElementNS(ns, "path");
    const xy = pts.map(([a, b]) => P(a, b).map(Number));
    const n = xy.length;
    let d = `M${xy[0][0]},${xy[0][1]}`;
    for (let i = 0; i < n; i++) {
      const p0 = xy[(i - 1 + n) % n], p1 = xy[i], p2 = xy[(i + 1) % n], p3 = xy[(i + 2) % n];
      const c1 = [p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6];
      const c2 = [p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6];
      d += ` C${c1.map((v) => v.toFixed(1))} ${c2.map((v) => v.toFixed(1))} ${p2.map((v) => v.toFixed(1))}`;
    }
    path.setAttribute("d", d + "Z");
    path.setAttribute("class", "isl");
    path.setAttribute("fill", "#e8f1f2"); path.setAttribute("stroke", "#195764");
    path.setAttribute("stroke-width", "3"); path.setAttribute("stroke-linejoin", "round");
    G.appendChild(path);
  });
  const pings = [[106.8,-6.2],[110.4,-7],[98.7,3.6],[104.7,-2.9],[119.4,-5.1],[116.8,-1.2],[124.8,1.5],[115.2,-8.6],[140.7,-2.5],[100.4,-0.9],[107.6,-6.9],[122.5,-4.0],[109.3,-0.1]];
  const PG = $1(".pings");
  pings.forEach(([a, b]) => {
    const [x, y] = P(a, b);
    PG.append(svgEl("circle", { cx: x, cy: y, r: 22, fill: "none", stroke: "#dc2626", "stroke-width": 3, class: "pr" }), svgEl("circle", { cx: x, cy: y, r: 8, fill: "#dc2626", class: "pd" }));
  });
  enter("push");
  // ---- panel A: peta + 18,5% (setelah panel otak) ----
  const tA = w("Indonesia") - 0.75;
  tl.to(RAIL, { x: -1920, duration: 0.75, ease: "power3.inOut" }, tA);
  [...$(".isl")].forEach((el, i) => {
    drawPath(el, tA + 0.3 + i * 0.05, 1.0);
    tl.fromTo(el, { fillOpacity: 0 }, { fillOpacity: 1, duration: 0.5 }, tA + 0.7 + i * 0.05);
  });
  const t1 = w("stroke");
  pop($(".pings .pd"), t1, { from: 0, stagger: 0.08, ease: "back.out(3)" });
  tl.fromTo($(".pings .pr"), { scale: 0.3, opacity: 0.9, transformOrigin: "50% 50%" }, { scale: 2.4, opacity: 0, duration: 1.3, ease: "power2.out", stagger: { each: 0.08, repeat: 1, repeatDelay: 0.5 } }, t1 + 0.1);
  tl.fromTo(".pa .big", { opacity: 0, y: 40 }, { opacity: 1, y: 0, duration: 0.45 }, w("delapan") - 0.4);
  count($1(".pa .big .v"), 0, 18.5, w("delapan") - 0.3, w("persen") - w("delapan") + 0.4, { dec: 1 });
  words(".pa .say", w("kematian") - 0.4, { stagger: 0.06 });

  // ---- panel B: otak, neuron padam ----
  let seed = 20261023;
  const rnd = () => ((seed = (seed * 1664525 + 1013904223) >>> 0) / 4294967296);
  const ctx = document.createElement("canvas").getContext("2d");
  const outline = $1(".pb .outline");
  const shape = new Path2D(outline.getAttribute("d"));
  const pts = [];
  while (pts.length < 480) {
    const x = 150 + rnd() * 820, y = 80 + rnd() * 740;
    if (ctx.isPointInPath(shape, x, y)) pts.push({ x, y, r: 3 + rnd() * 5, lost: rnd() < 0.42, o: rnd() });
  }
  const E = $1(".pb .edges"), N = $1(".pb .nodes");
  pts.forEach((p, i) => {
    pts.map((q, j) => [j, (q.x - p.x) ** 2 + (q.y - p.y) ** 2]).filter(([j]) => j > i).sort((a, b) => a[1] - b[1]).slice(0, 2).forEach(([j, d]) => {
      if (d > 5200) return;
      E.appendChild(svgEl("line", { x1: p.x.toFixed(1), y1: p.y.toFixed(1), x2: pts[j].x.toFixed(1), y2: pts[j].y.toFixed(1), class: p.lost || pts[j].lost ? "e lost" : "e", stroke: "#7fa9b1", "stroke-width": 2 }));
    });
    const c = svgEl("circle", { cx: p.x.toFixed(1), cy: p.y.toFixed(1), r: p.r.toFixed(1), class: p.lost ? "n lost" : "n live", fill: "#195764" }, N);
    c.dataset.o = p.o.toFixed(3);
  });
  const nodes = [...$(".pb .n")].sort((a, b) => a.dataset.o - b.dataset.o);
  const lost = [...$(".pb .n.lost")].sort((a, b) => a.dataset.o - b.dataset.o);
  const tB = 0.35;
  drawPath(outline, tB + 0.2, 0.9);
  tl.fromTo(nodes, { scale: 0, transformOrigin: "50% 50%" }, { scale: 1, duration: 0.35, ease: "back.out(3)", stagger: { each: 0.8 / nodes.length } }, tB + 0.3);
  tl.fromTo($(".pb .e"), { opacity: 0 }, { opacity: 1, duration: 0.6, stagger: { each: 0.7 / 700 } }, tB + 0.5);
  pop(".pb .clock", tB + 0.5);
  tl.fromTo(".pb .clock-arc", { strokeDashoffset: 0 }, { strokeDashoffset: 213.6, duration: tA - tB, ease: "none" }, tB + 0.5);
  tl.fromTo(".pb .clock-hand", { rotation: 0, svgOrigin: "0 0" }, { rotation: 360 * Math.round((tA - tB) / 2), duration: tA - tB, ease: "none" }, tB + 0.5);
  const tc = w("satu") - 0.4;
  rise(".pb .stat .num", w("otak") - 0.3, { y: 30 });
  count($1(".pb .stat .num"), 0, 1900000, tc, w("neuron") - tc + 0.15, { ease: "power1.in" });
  tl.to(lost, { attr: { fill: "#d1d5db" }, scale: 0.55, y: 22, duration: 0.4, ease: "power2.out", stagger: { each: 1.1 / lost.length } }, w("kehilangan"));
  tl.to($(".pb .e.lost"), { attr: { stroke: "#eef0f3" }, duration: 0.4, stagger: { each: 1.1 / 400 } }, w("kehilangan") + 0.1);
  rise(".pb .stat .lbl", w("kehilangan"));
  const t45 = w("empat") - 0.3;
  tl.fromTo(".pb .win45", { x: 120, opacity: 0 }, { x: 0, opacity: 1, duration: 0.5, ease: "back.out(1.8)" }, w("obat") - 0.2);
  tl.fromTo(".pb .win45 svg", { rotation: 0, transformOrigin: "50% 50%" }, { rotation: 180, duration: 0.6, ease: "back.inOut(1.5)" }, t45);
  tl.fromTo(".pb .win45 .sand", { scale: 0.2, transformOrigin: "35px 52px" }, { scale: 1, duration: 1.4, ease: "none" }, t45 + 0.6);

  // ---- panel C: radiolog yang langka ----
  const tC = w("Tapi") - 0.15;
  tl.to(RAIL, { x: -3840, duration: 0.75, ease: "power3.inOut" }, tC);
  tl.fromTo(".pc .rad", { y: 520 }, { y: 0, duration: 0.6, ease: "back.out(1.5)" }, tC + 0.5);
  pop(".pc .tag", tC + 0.9);
  bob(".pc .dika-rig", tC + 1.0, END, 4, 2.2);
  blink(".pc .rad .dika-lid", [tC + 1.6, tC + 4.6, tC + 7.0]);
  tl.fromTo(".pc .rad .dika-head", { rotation: 0, svgOrigin: "160 240" }, { rotation: 7, duration: 0.3, yoyo: true, repeat: 1, ease: "sine.inOut" }, w("hanya", 2) + 0.2);
  const qs = [...$(".pc .q")];
  qs.forEach((el, i) => tl.fromTo(el, { x: 220, opacity: 0 }, { x: 0, opacity: 1, duration: 0.45, ease: "back.out(1.6)" }, tC + 0.4 + i * 0.06));
  tl.fromTo($(".pc .mhs-q"), { scale: 0, transformOrigin: "30% 100%" }, { scale: 1, duration: 0.3, ease: "back.out(3)", stagger: 0.05 }, tC + 0.9);
  tl.fromTo(".pc .card", { x: 520, opacity: 0 }, { x: 0, opacity: 1, duration: 0.6, ease: "power3.out" }, w("hanya", 2) - 0.4);
  rise(".pc .card .h", w("hanya", 2) - 0.2, { y: 16 });
  const rows = [...$(".pc .row")];
  rise(rows[0], w("nol") - 0.4, { y: 20 });
  count(rows[0].querySelector(".v"), 0, 0.8, w("nol") - 0.2, 1.0, { dec: 1 });
  scaleBar(rows[0].querySelector(".fill"), w("nol"), { d: 0.9 });
  rise(rows[1], w("enam") - 0.4, { y: 20 });
  count(rows[1].querySelector(".v"), 0, 12.7, w("enam") - 0.3, 0.9, { dec: 1 });
  scaleBar(rows[1].querySelector(".fill"), w("enam") - 0.3, { d: 0.9 });
  tl.fromTo(".pc .cmpx", { y: 40, opacity: 0 }, { y: 0, opacity: 1, duration: 0.35 }, w("kali") - 0.2);
  tl.fromTo(".pc .cmpx .x", { scale: 2.6, opacity: 0 }, { scale: 1, opacity: 1, duration: 0.35, ease: "power4.in", transformOrigin: "50% 60%" }, w("kali") - 0.25);
  pop(".pc .tag2", w("mengajar") - 0.1, { from: 0.4, origin: "0% 50%" });
  tl.fromTo($(".pc .mhs-q"), { scale: 1 }, { scale: 1.15, duration: 0.2, yoyo: true, repeat: 1, ease: "power2.out", immediateRender: false, transformOrigin: "30% 100%" }, w("kampus"));
  leave();
  window.__timelines[ID] = tl;
})();
</script>
</template></body></html>

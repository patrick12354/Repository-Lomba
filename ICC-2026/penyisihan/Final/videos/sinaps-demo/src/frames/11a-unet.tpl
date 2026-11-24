<!doctype html>
<html><head><meta charset="UTF-8" /></head><body><template>
<style>
<!-- @base -->
#f11a { position: absolute; inset: 0; background: transparent; overflow: hidden; }
/* kartu "Modul visi" persis seperti di frame 11: titik awal pembukaan */
#f11a .ghost { position: absolute; left: 990px; top: 405px; width: 400px; height: 130px; border-radius: 22px; padding: 22px 26px; background: #fff; border: 2px solid #195764; box-shadow: 0 1px 2px rgba(16,24,40,.04), 0 10px 26px rgba(16,24,40,.06); }
#f11a .ghost .t { font: 700 38px 'Geist', sans-serif; color: var(--ink); }
#f11a .ghost .s { margin-top: 6px; font: 600 27px 'Geist', sans-serif; color: var(--muted); }
/* isi ditengahkan vertikal (baris spesifikasi di bawah dihapus); kartu .ghost tetap di koordinat frame 11 */
#f11a .lift { position: absolute; left: 0; top: 56px; width: 1920px; height: 1080px; }
#f11a .u { position: absolute; left: 0; top: 0; width: 1920px; height: 1080px; overflow: visible; }
#f11a .ins { position: absolute; left: 110px; top: 150px; width: 330px; height: 330px; }
#f11a .ins .sl { position: absolute; width: 230px; height: 230px; border-radius: 10px; overflow: hidden; background: #000; box-shadow: 0 0 0 2px #fff, 0 10px 22px rgba(16,24,40,.22); }
#f11a .ins .sl img { width: 100%; height: 100%; display: block; }
#f11a .cap { position: absolute; font: 600 30px/1.3 'Geist', sans-serif; color: var(--ink-2); white-space: nowrap; }
#f11a .cap b { color: var(--ink); font-weight: 700; }
#f11a .cap .m { font-family: 'Geist Mono', monospace; }
#f11a .name { position: absolute; left: 600px; top: 120px; width: 740px; text-align: center; font: 700 96px/1 'Geist', sans-serif; letter-spacing: -0.035em; color: var(--ink); }
#f11a .name span { color: var(--muted); font-weight: 600; }
#f11a .arm { position: absolute; font: 700 38px 'Geist', sans-serif; }
#f11a .arm small { display: block; margin-top: 4px; font: 600 28px 'Geist', sans-serif; color: var(--ink-2); }
#f11a .out { position: absolute; left: 1500px; top: 150px; width: 310px; height: 310px; border-radius: 12px; overflow: hidden; background: #000; box-shadow: 0 0 0 3px var(--ink), 0 18px 40px rgba(16,24,40,.2); }
#f11a .out img { position: absolute; inset: 0; width: 100%; height: 100%; }
#f11a .out .pr { image-rendering: pixelated; }
#f11a .use { position: absolute; left: 1500px; top: 580px; width: 330px; }
#f11a .use .t { font: 600 30px/1.3 'Geist', sans-serif; color: var(--ink-2); }
#f11a .use .d { margin-top: 22px; font: 600 72px/1 'Geist Mono', monospace; letter-spacing: -0.04em; color: var(--nt-d); }
#f11a .use .d small { display: block; margin-top: 8px; font: 600 28px 'Geist', sans-serif; letter-spacing: 0; color: var(--ink-2); }
</style>
<div id="f11a" data-composition-id="f11a" data-width="1920" data-height="1080">
  <div class="lift">
  <div class="ins">
    <div class="sl"><img src="../../assets/mri/unet/adc_z15.png" alt="" /></div>
    <div class="sl"><img src="../../assets/mri/unet/adc_z14.png" alt="" /></div>
    <div class="sl"><img src="../../assets/mri/unet/adc_z13.png" alt="" /></div>
    <div class="sl"><img src="../../assets/mri/unet/dwi_z15.png" alt="" /></div>
    <div class="sl"><img src="../../assets/mri/unet/dwi_z14.png" alt="" /></div>
    <div class="sl"><img src="../../assets/mri/unet/dwi_z13.png" alt="" /></div>
  </div>
  <div class="cap c-in" style="left: 110px; top: 512px"><b>3 DWI + 3 ADC</b>, slice bertetangga<br /><span class="m">6 × 192 × 192</span></div>
  <div class="name">U-Net <span>2.5D</span></div>
  <svg class="u" viewBox="0 0 1920 1080" fill="none"></svg>
  <div class="arm a-enc" style="left: 430px; top: 748px; color: #195764">encoder<small>mengenali lesinya</small></div>
  <div class="arm a-dec" style="left: 1176px; top: 748px; color: #4f8a5c">decoder<small>kembali ke 192 × 192</small></div>
  <div class="cap c-skip" style="left: 760px; top: 222px"><b>skip connection</b> menjaga tepi lesi</div>
  <div class="out"><img src="../../assets/mri/unet/dwi_z14.png" alt="" /><img class="pr" src="../../assets/mri/unet/pred_z14.png" alt="" /></div>
  <div class="cap c-out" style="left: 1500px; top: 476px"><b>peta lesi</b> per piksel</div>
  <div class="use"><div class="t">pembanding setelah mahasiswa submit</div><div class="d">0,738<small>Dice · 36 kasus uji</small></div></div>
  </div>
  <div class="ghost"><div class="t">Modul visi</div><div class="s">U-Net 2.5D</div></div>
</div>
<script>
(() => {
/* @helpers */
  // arsitektur UNet(cin=6, base=32) di mvp/pipeline/kaggle/train_unet.py; angka dari metrics.json (run3).
  // Gambar: kasus bank sub-1413 slice 13-15, prediksi U-Net asli (assets/mri/unet, tools/ekspor_unet.py).

  // ---- pembukaan: f11 dihapus kertas yang melebar dari kartu "Modul visi", kartu lalu larut ----
  tl.fromTo(S, { clipPath: "inset(405px 530px 545px 990px round 22px)" }, { clipPath: "inset(0px 0px 0px 0px round 0px)", duration: 0.46, ease: "power2.inOut" }, 0.0);
  tl.set(S, { clipPath: "none" }, 0.47);

  // ---- diagram U ringkas: batang = peta fitur (tinggi ~ resolusi, tebal ~ kanal), tanpa label per lapis ----
  const svg = $1(".u");
  const H = [210, 140, 92, 60, 40], Y = [300, 500, 650, 755, 835], WC = [12, 18, 26, 36, 50];
  const enc = [[520, 556], [610, 646], [700, 744], [800, 852], [912, 980]];
  const MID = (912 + 980 + 50) / 2;
  const dec = enc.slice(0, 4).map(([a, b], L) => [2 * MID - b - WC[L], 2 * MID - a - WC[L]]);
  const bar = (x, L, col) => {
    const h = H[L], w = WC[L], y = Y[L] - h / 2;
    const g = svgEl("g", { opacity: 0 }, svg);
    svgEl("path", { d: `M${x},${y} l7,-7 h${w} l-7,7 z`, fill: col, opacity: 0.55 }, g);
    svgEl("path", { d: `M${x + w},${y} l7,-7 v${h} l-7,7 z`, fill: col, opacity: 0.8 }, g);
    svgEl("rect", { x, y, width: w, height: h, rx: 1.5, fill: col }, g);
    return { g, x, w, y, h, L, cx: x + w / 2, right: x + w, bot: y + h };
  };
  const E = enc.map((xs, L) => xs.map((x) => bar(x, L, L === 4 ? "#e07a1f" : "#195764")));
  const DC = dec.map((xs, L) => xs.map((x) => bar(x, L, "#6fa77a")));
  const defs = svgEl("defs", {}, svg);
  ["334155", "195764", "6fa77a", "94a3b8"].forEach((c) => {
    const m = svgEl("marker", { id: `ah-${ID}-${c}`, viewBox: "0 0 10 10", refX: 8, refY: 5, markerWidth: 6, markerHeight: 6, orient: "auto-start-reverse" }, defs);
    svgEl("path", { d: "M0,0 L10,5 L0,10 z", fill: `#${c}` }, m);
  });
  const arrow = (d, c, dash) => { const p = svgEl("path", { d, stroke: `#${c}`, "stroke-width": 3, "stroke-linecap": "round", "marker-end": `url(#ah-${ID}-${c})`, opacity: 0 }, svg); p.dataset.dash = dash || "none"; return p; };
  const downs = E.slice(0, 4).map((lv, L) => arrow(`M${lv[1].cx},${lv[1].bot + 6} L${E[L + 1][0].x - 8},${E[L + 1][0].y + 12}`, "195764"));
  const ups = DC.map((lv, L) => { const a = L === 3 ? E[4][1] : DC[L + 1][1]; return arrow(`M${a.right + 10},${a.y + 10} L${lv[0].cx},${lv[0].bot + 12}`, "6fa77a"); });
  const skips = E.slice(0, 4).map((lv, L) => arrow(`M${lv[1].right + 12},${Y[L]} H${DC[L][0].x - 8}`, "94a3b8", "6 8"));
  const aIn = arrow(`M452,${Y[0]} H${E[0][0].x - 10}`, "334155");
  const aOut = arrow(`M${DC[0][1].right + 14},${Y[0]} H1488`, "334155");
  const show = (a, t, d = 0.3) => {
    tl.set(a, { opacity: 1 }, t);
    drawPath(a, t, d, { ease: "power2.out" });
    tl.set(a, { strokeDasharray: a.dataset.dash, strokeDashoffset: 0 }, t + d + 0.01);
  };
  const lit = (bs, t, st = 0.04) => tl.fromTo(bs.map((b) => b.g), { opacity: 0, y: 8 }, { opacity: 1, y: 0, duration: 0.35, ease: "expo.out", stagger: st }, t);

  // ---- beat 1 "Isinya U-Net 2.5D, masuk enam slice DWI dan ADC, keluar peta lesi per piksel" ----
  // semua mendarat dalam ~1,3 dtk pertama kalimat, lalu diam selama presenter bicara
  const t1 = w("Isinya") - 0.1;
  tl.to(".ghost", { scale: 1.08, opacity: 0, filter: "blur(6px)", duration: 0.35, ease: "power2.in" }, t1 - 0.2);
  tl.fromTo(".name", { opacity: 0, filter: "blur(10px)" }, { opacity: 1, filter: "blur(0px)", duration: 0.2, ease: "power2.out" }, t1);
  const sl = [...$(".ins .sl")];
  sl.forEach((el, i) => tl.fromTo(el, { x: 0, y: 0, opacity: 0 }, { x: (5 - i) * 20, y: (5 - i) * 20, opacity: 1, duration: 0.5, ease: "expo.out" }, w("masuk") - 0.2 + i * 0.04));
  tl.fromTo(".c-in", { opacity: 0, y: 10 }, { opacity: 1, y: 0, duration: 0.35 }, w("masuk") + 0.1);
  show(aIn, w("masuk") + 0.15, 0.25);
  // seluruh U menyala sebagai satu bentuk (rinciannya dijelaskan di beat 2)
  [0, 1, 2, 3, 4].forEach((L) => lit(E[L], w("masuk") + 0.2 + L * 0.07));
  [3, 2, 1, 0].forEach((L, k) => lit(DC[L], w("masuk") + 0.55 + k * 0.07));
  downs.forEach((a, L) => show(a, w("masuk") + 0.3 + L * 0.07, 0.15));
  ups.forEach((a, L) => show(a, w("masuk") + 0.6 + (3 - L) * 0.07, 0.15));
  show(aOut, w("keluar") - 0.1, 0.25);
  tl.fromTo(".out", { opacity: 0, scale: 0.94 }, { opacity: 1, scale: 1, duration: 0.45 }, w("keluar"));
  tl.fromTo(".out .pr", { opacity: 0 }, { opacity: 0.9, duration: 0.4 }, w("peta"));
  tl.fromTo(".c-out", { opacity: 0, y: 10 }, { opacity: 1, y: 0, duration: 0.35 }, w("peta"));

  // ---- beat 2 "Encoder mengenali lesinya, decoder mengembalikan ke ukuran asli supaya batasnya presisi" ----
  const t2 = w("Encoder") - 0.15;
  tl.to(".name", { opacity: 0.14, duration: 0.3 }, t2);
  tl.fromTo(".a-enc", { opacity: 0, x: -16 }, { opacity: 1, x: 0, duration: 0.4 }, t2);
  tl.to(E.flat().map((b) => b.g), { y: 6, duration: 0.15, stagger: 0.03, yoyo: true, repeat: 1, ease: "power2.out" }, t2 + 0.1);
  tl.fromTo(".a-dec", { opacity: 0, x: 16 }, { opacity: 1, x: 0, duration: 0.4 }, w("decoder") - 0.1);
  tl.to(DC.slice().reverse().flat().map((b) => b.g), { y: -6, duration: 0.15, stagger: 0.03, yoyo: true, repeat: 1, ease: "power2.out" }, w("decoder"));
  skips.forEach((a, L) => show(a, w("supaya") - 0.2 + L * 0.06, 0.4));
  tl.fromTo(".c-skip", { opacity: 0, y: 10 }, { opacity: 1, y: 0, duration: 0.35 }, w("supaya"));

  // ---- beat 3 "Hasilnya jadi pembanding setelah mahasiswa submit, dengan Dice 0,738 pada data uji" ----
  const t4 = w("Hasilnya") - 0.1;
  tl.fromTo(".use .t", { opacity: 0, y: 12 }, { opacity: 1, y: 0, duration: 0.4 }, t4);
  tl.fromTo(".out", { boxShadow: "0 0 0 3px #10313a, 0 18px 40px rgba(16,24,40,.2)" }, { boxShadow: "0 0 0 8px #e07a1f, 0 18px 40px rgba(16,24,40,.2)", duration: 0.3, immediateRender: false }, t4);
  tl.fromTo(".use .d", { opacity: 0, y: 16 }, { opacity: 1, y: 0, duration: 0.45 }, w("Dice") - 0.1);
  leave();
  window.__timelines[ID] = tl;
})();
</script>
</template></body></html>

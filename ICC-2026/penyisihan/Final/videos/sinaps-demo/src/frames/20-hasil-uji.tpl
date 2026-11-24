<!doctype html>
<html><head><meta charset="UTF-8" /></head><body><template>
<style>
<!-- @base -->
#f20 { position: absolute; inset: 0; background: transparent; overflow: hidden; }
#f20 .kick { position: absolute; left: 96px; top: 70px; }
#f20 .title { position: absolute; left: 96px; top: 112px; font-size: 64px; font-weight: 700; }
#f20 .cmp { position: absolute; left: 96px; top: 240px; width: 900px; }
#f20 .cmp .h { font: 700 34px 'Geist', sans-serif; color: var(--ink); }
#f20 .cmp .r { margin-top: 26px; }
#f20 .cmp .r .lb { display: flex; justify-content: space-between; align-items: baseline; font-size: 42px; font-weight: 700; }
#f20 .cmp .r .v { font: 700 150px/1 'Oswald', sans-serif; }
#f20 .cmp .r .tr { margin-top: 14px; height: 34px; border-radius: 17px; background: #f1f5f9; overflow: hidden; }
#f20 .cmp .r .tr i { display: block; height: 100%; border-radius: 20px; }
#f20 .ci { margin-top: 10px; font: 600 26px 'Geist', sans-serif; color: var(--muted); }
#f20 .zero { position: absolute; left: 1080px; top: 240px; width: 744px; height: 560px; border-radius: 28px; padding: 50px 56px; background: #fff; border: 2px solid var(--line); box-shadow: 0 1px 2px rgba(16,24,40,.04), 0 14px 36px rgba(16,24,40,.07); }
#f20 .zero .v { font: 700 230px/1 'Oswald', sans-serif; color: var(--ok); }
#f20 .zero .v small { font-size: 110px; color: var(--muted); }
#f20 .zero .t { margin-top: 18px; font-size: 48px; line-height: 1.15; font-weight: 700; }
#f20 .zero .s { margin-top: 18px; font: 600 28px/1.4 'Geist', sans-serif; color: var(--ink-2); }
#f20 .rule { position: absolute; left: 96px; right: 96px; top: 838px; height: 158px; display: flex; align-items: center; gap: 22px; padding: 0 30px; border-radius: 26px; background: var(--teal-soft); border: 3px solid var(--teal); }
#f20 .rule .rt { font: 700 40px/1.05 'Oswald', sans-serif; color: var(--teal); text-transform: uppercase; letter-spacing: .04em; width: 190px; }
#f20 .rule .st { padding: 14px 22px; border-radius: 18px; background: #fff; border: 2px solid var(--line-2); }
#f20 .rule .st b { display: block; font: 700 34px 'Geist', sans-serif; color: var(--ink); }
#f20 .rule .st span { display: block; margin-top: 4px; font: 600 25px/1.28 'Geist', sans-serif; color: var(--ink-2); }
#f20 .rule .st.out { flex: 1; border-color: var(--nt); }
#f20 .rule .ar { font: 700 44px 'Geist', sans-serif; color: var(--teal); }
#f20 .foot { position: absolute; left: 96px; bottom: 30px; }
</style>
<div id="f20" data-composition-id="f20" data-width="1920" data-height="1080">
  
  <div class="kick eyebrow">Hasil pengujian · Bab IV</div>
  <div class="title">Diuji pada kode yang sudah di-deploy.</div>
  <div class="cmp">
    <div class="h">Mengenali 5 jenis kesalahan anotasi</div>
    <div class="r"><div class="lb"><span>Aturan SINAPS</span><span class="v" style="color: var(--teal)">97,8%</span></div><div class="tr"><i style="width: 97.8%; background: var(--teal)"></i></div><div class="ci">IK 95% 96,0–99,1 · 672 anotasi, 36 subjek</div></div>
    <div class="r"><div class="lb"><span>Hanya skor Dice</span><span class="v" style="color: #64748b">47,3%</span></div><div class="tr"><i style="width: 47.3%; background: #cbd5e1"></i></div><div class="ci">pembanding: pengklasifikasi yang hanya melihat Dice</div></div>
  </div>
  <div class="zero">
    <div class="v"><span class="z" style="display:inline-block">0</span><small>/<span class="n">432</span></small></div>
    <div class="t">jawaban tutor keluar dari fakta</div>
    <div class="s">4 skenario uji, termasuk mahasiswa yang mendesakkan jawaban keliru.</div>
  </div>
  <div class="rule"><div class="rt">Aturan SINAPS</div><div class="st"><b>4 metrik</b><span>Dice · recall per lesi<br />galat volume · HD95</span></div><div class="ar">→</div><div class="st"><b>5 ambang</b><span>aturan keputusan<br />sederhana &amp; transparan</span></div><div class="ar">→</div><div class="st out"><b>5 jenis kesalahan</b><span>hampir benar · terlalu luas · terlalu sempit<br />lesi kecil terlewat · salah lokasi</span></div></div>
  <div class="foot src">Aturan diuji pada anotasi sintetis (batas atas). Efek belajar pada mahasiswa belum diukur, menjadi tahap pilot berikutnya.</div>
</div>
<!-- @sfx woosh_up@0.0:0.5 impact_boom@0.72:0.6 punch_hit@0.72:0.4 whoosh_deep@1.75:0.4 snap@~Modul-0.3:0.4 riser@~akurasi-0.6:0.35 counter_roll@~sembilan-0.2:0.4 punch_hit@~persen+0.3:0.55 ding@~persen+0.35:0.4 swipe_zip@~dibanding-0.2:0.4 counter_roll@~empat-0.2:0.3 thud_soft@~empat+1.0:0.4 swish_fast@~Dan-0.2:0.45 counter_roll@~empat.2-0.2:0.3 reverse_suck@~tidak-1.1:0.4 impact_boom@~tidak:0.6 swipe_zip@~Modul-0.4:0.35 mar1@~penilaian:0.45 mar3@~mengenali:0.45 mar5@~kesalahan:0.5 confetti@~fakta+0.1:0.55 success_arp@~fakta+0.2:0.45 -->
<script>
(() => {
/* @helpers */
enter("bars");
  const tb = bumper("HASIL UJI", 0.5, { sub: "diuji pada kode yang sudah di-deploy", hold: 0.75 });
  rise(".kick", tb - 0.1, { y: 14 });
  words(".title", tb);
  rise(".cmp .h", w("Modul") - 0.3, { y: 14 });
  // penjelasan aturan: metrik -> ambang -> jenis kesalahan, seirama "modul penilaian mengenali jenis kesalahan"
  tl.fromTo(".rule", { y: 60, opacity: 0 }, { y: 0, opacity: 1, duration: 0.5 }, w("Modul") - 0.4);
  const rs = [...$(".rule .st")], ra = [...$(".rule .ar")];
  rise(".rule .rt", w("Modul") - 0.2, { y: 16 });
  pop(rs[0], w("penilaian"), { from: 0.7 });
  pop(ra[0], w("mengenali") - 0.15, { from: 0.3 });
  pop(rs[1], w("mengenali"), { from: 0.7 });
  pop(ra[1], w("kesalahan") - 0.15, { from: 0.3 });
  pop(rs[2], w("kesalahan"), { from: 0.7 });
  tl.to(rs[2], { backgroundColor: "#fdf0e3", duration: 0.3 }, w("kesalahan") + 0.4);
  const rows = [...$(".cmp .r")];
  rise(rows[0], w("akurasi") - 0.3, { y: 20 });
  count(rows[0].querySelector(".v"), 0, 97.8, w("sembilan") - 0.2, w("persen") - w("sembilan") + 0.4, { dec: 1, suf: "%" });
  scaleBar(rows[0].querySelector(".tr i"), w("sembilan") - 0.2, { d: 1.6 });
  rise(rows[0].querySelector(".ci"), w("persen") + 0.3, { y: 8 });
  hit(rows[0].querySelector(".v"), 860, 400, w("persen") + 0.3, { color: "#195764", c2: "#e07a1f", r0: 80, r1: 230, n: 14, shake: 9, origin: "100% 50%" });
  rise(rows[1], w("dibanding") - 0.2, { y: 20 });
  rise(rows[1].querySelector(".ci"), w("Dice") - 0.2, { y: 8 });
  count(rows[1].querySelector(".v"), 0, 47.3, w("empat") - 0.2, 1.0, { dec: 1, suf: "%" });
  scaleBar(rows[1].querySelector(".tr i"), w("empat") - 0.2, { d: 1.0 });
  // 0 dari 432
  tl.fromTo(".zero", { x: 80, opacity: 0 }, { x: 0, opacity: 1, duration: 0.6 }, w("Dan") - 0.2);
  count($1(".zero .n"), 0, 432, w("empat", 2) - 0.2, w("dua") - w("empat", 2) + 0.4);
  rise(".zero .t", w("jawaban") - 0.2, { y: 14 });
  tl.fromTo(".zero .z", { scale: 3, opacity: 0 }, { scale: 1, opacity: 1, duration: 0.45, ease: "back.out(2)", transformOrigin: "50% 80%" }, w("tidak") - 0.1);
  burst(1200, 420, w("tidak") + 0.15, { color: "#16a34a", c2: "#195764", r0: 110, r1: 300, n: 16 });
  shake(w("tidak") + 0.15, 12);
  flash(w("tidak") + 0.15, { color: "#dcfce7", a: 0.6, d: 0.5 });
  confetti(1450, 300, w("fakta") + 0.1, { n: 80 });
  rise(".zero .s", w("fakta") - 0.4, { y: 12 });
  rise(".foot", w("fakta") + 0.6, { y: 8 });
  leave();
  window.__timelines[ID] = tl;
})();
</script>
</template></body></html>

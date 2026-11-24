<!doctype html>
<html><head><meta charset="UTF-8" /></head><body><template>
<style>
<!-- @base -->
#f17 { position: absolute; inset: 0; background: transparent; overflow: hidden; }
#f17 .win { left: 450px; top: 110px; width: 1380px; }
#f17 .big { position: absolute; padding: 22px 32px; border-radius: 24px; background: #fff; border: 2px solid var(--line); box-shadow: 0 1px 2px rgba(16,24,40,.04), 0 14px 36px rgba(16,24,40,.07); }
#f17 .big .k { font: 700 30px 'Geist', sans-serif; color: var(--ink-2); }
#f17 .big .v { font: 700 124px/1 'Oswald', sans-serif; margin-top: 6px; }

#f17 .win .view { height: 862px; }
#f17 .win .view .cam { position: absolute; inset: 0; }
#f17 .win .view video.shot { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }
#f17 .win .view .cam img.hold { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }
</style>
<div id="f17" data-composition-id="f17" data-width="1920" data-height="1080">
  
  <div class="side"><div class="n">DEMO · 04</div><h2>Dinilai dalam hitungan detik</h2><p>Dice · recall per lesi · galat volume · HD95</p></div>
  <div class="win"><div class="bar"><i></i><i></i><i></i><span class="url">mvp-lemon-ten.vercel.app/latihan</span></div>
    <div class="view"><div class="cam"><img class="hold" src="../../assets/rec/skor_akhir.jpg" alt="" /><video id="rec-skor" class="clip shot" src="../../assets/rec/skor.mp4" muted playsinline data-start="0" data-duration="8.9" data-media-start="0" data-playback-rate="1.1" data-track-index="1"></video></div></div>
  </div>
  <div class="big" style="left: 500px; top: 640px"><div class="k">Jenis kesalahan</div><div class="v" style="color: var(--nt-d); font-size: 76px">Terlalu sempit</div></div>
  <div class="big" style="left: 500px; top: 330px"><div class="k">Skor Dice</div><div class="v" style="color: var(--nt-d)">0,48</div></div>
  <div class="callout" style="left: 500px; top: 920px">oranye = jawaban · hijau = <b>kunci ahli</b></div>
</div>
<!-- @sfx reverse_suck@0.0:0.35 ding@~skornya-0.3:0.45 swipe_zip@~skornya:0.35 counter_roll@~Dice-0.1:0.4 punch_hit@~Dice+0.7:0.5 mar3@~recall:0.4 mar4@~galat:0.4 card_flip@~jenis-0.3:0.4 stamp@~jenis+0.1:0.45 -->
<script>
(() => {
/* @helpers */
enter("zoom");

  rise(".side .n", 0.6, { y: 14 });
  rise(".side h2", 0.7, { y: 24 });
  rise(".side p", 0.85, { y: 14 });
  tl.fromTo(".win", { y: 50, scale: 0.97, opacity: 0 }, { y: 0, scale: 1, opacity: 1, duration: 0.7 }, 0.45);

  const big = [...$(".big")];
  tl.fromTo(big[1], { x: 60, opacity: 0, scale: 0.9 }, { x: 0, opacity: 1, scale: 1, duration: 0.55, ease: "back.out(1.7)" }, w("Dice") - 0.2);
  count(big[1].querySelector(".v"), 0, 0.48, w("Dice") - 0.1, 0.8, { dec: 2 });
  tl.fromTo(big[0], { x: 60, opacity: 0, scale: 0.9 }, { x: 0, opacity: 1, scale: 1, duration: 0.55, ease: "back.out(1.7)" }, w("jenis") - 0.2);
  // kamera: panel hasil penilaian diperbesar, lalu mundur memperlihatkan overlay jawaban vs kunci
  camTo(".cam", 1665, 300, 1.7, w("skornya") - 0.3, 1.0);
  camTo(".cam", 960, 600, 1, w("jenis") + 0.6, 0.8);
  hit(big[1].querySelector(".v"), 640, 470, w("Dice") + 0.7, { r0: 70, r1: 190, n: 12, shake: 7, origin: "0% 50%" });
  mark(big[0].querySelector(".v"), w("kesalahannya"), { color: "rgba(224,122,31,.2)" });
  pop(".callout", w("kesalahannya") + 0.3, { from: 0.6, origin: "0% 50%" });
  leave();
  window.__timelines[ID] = tl;
})();
</script>
</template></body></html>

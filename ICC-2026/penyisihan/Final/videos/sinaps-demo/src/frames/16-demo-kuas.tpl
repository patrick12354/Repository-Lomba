<!doctype html>
<html><head><meta charset="UTF-8" /></head><body><template>
<style>
<!-- @base -->
#f16 { position: absolute; inset: 0; background: transparent; overflow: hidden; }
#f16 .win { left: 450px; top: 90px; width: 1380px; overflow: visible; }
#f16 .win > .bar { border-radius: 22px 22px 0 0; }
#f16 .win .view { border-radius: 0 0 22px 22px; }
#f16 .speed { position: absolute; right: 14px; top: 60px; padding: 8px 18px; border-radius: 999px; background: var(--ink); font: 700 26px 'Geist', sans-serif; color: #fff; z-index: 3; }

#f16 .win .view { height: 862px; }
#f16 .win .view .cam { position: absolute; inset: 0; }
#f16 .win .view video.shot { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }
#f16 .win .view .cam img.hold { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }
</style>
<div id="f16" data-composition-id="f16" data-width="1920" data-height="1080">
  
  <div class="side"><div class="n">DEMO · 03</div><h2>Tandai lesi dengan kuas</h2><p>labelmap · hapus · urungkan</p></div>
  <div class="win"><div class="bar"><i></i><i></i><i></i><span class="url">mvp-lemon-ten.vercel.app/latihan</span></div>
    <div class="view"><div class="cam"><img class="hold" src="../../assets/rec/kuas_akhir.jpg" alt="" /><video id="rec-kuas" class="clip shot" src="../../assets/rec/kuas.mp4" muted playsinline data-start="0" data-duration="7.8" data-media-start="0" data-playback-rate="3.3" data-track-index="1"></video></div></div><div class="speed">dipercepat 3,3×</div>
  </div>
  <div class="callout" style="left: 480px; top: 820px">kuas langsung di <b>citra</b></div>
  <div class="callout" style="left: 1060px; top: 620px"><b>kirim</b> jawaban</div>
</div>
<!-- @sfx whip@0.0:0.45 notif_pop@1.0:0.35 swipe_zip@1.25:0.3 pen_scribble@~menandai:0.4 brush@~kuas:0.45 brush@~citra-0.3:0.35 swish_fast@~menekan-0.4:0.35 click@6.0:0.6 success_arp@6.25:0.4 -->
<script>
(() => {
/* @helpers */
enter("whip");

  rise(".side .n", 0.6, { y: 14 });
  rise(".side h2", 0.7, { y: 24 });
  rise(".side p", 0.85, { y: 14 });
  tl.fromTo(".win", { y: 50, scale: 0.97, opacity: 0 }, { y: 0, scale: 1, opacity: 1, duration: 0.7 }, 0.45);

  pop(".speed", 1.0, { from: 0.7 });
  // kamera: dekat ke lesi saat mengecat, lalu ke tombol kirim; klik nyata di rekaman jatuh ~6,0 dtk
  camTo(".cam", 690, 560, 1.75, 1.2, 1.2);
  camTo(".cam", 1667, 1000, 1.5, w("menekan") - 0.5, 0.8);
  camTo(".cam", 960, 600, 1, 6.6, 0.9);
  pop($(".callout")[0], w("kuas") - 0.2, { from: 0.6, origin: "0% 50%" });
  tl.to($(".callout")[0], { opacity: 0, duration: 0.2 }, w("menekan") - 0.5);
  pop($(".callout")[1], w("submit") - 0.5, { from: 0.6, origin: "0% 50%" });
  burst(1557, 790, 6.0, { r0: 60, r1: 160, n: 12, c2: "#16a34a" });
  tl.to($(".callout")[1], { opacity: 0, duration: 0.2 }, 6.6);
  leave();
  window.__timelines[ID] = tl;
})();
</script>
</template></body></html>

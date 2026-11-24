<!doctype html>
<html><head><meta charset="UTF-8" /></head><body><template>
<style>
<!-- @base -->
#f14 { position: absolute; inset: 0; background: transparent; overflow: hidden; }
#f14 .win { left: 450px; top: 110px; width: 1380px; }
#f14 .hl { position: absolute; border: 4px solid var(--nt); border-radius: 20px; }

#f14 .win .view { height: 862px; }
#f14 .win .view .cam { position: absolute; inset: 0; }
#f14 .win .view video.shot { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }
#f14 .win .view .cam img.hold { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }
</style>
<div id="f14" data-composition-id="f14" data-width="1920" data-height="1080">
  
  <div class="side"><div class="n">DEMO · 01</div><h2>Beranda yang tahu langkahmu</h2><p>rekaman MVP asli · data demo</p></div>
  <div class="win"><div class="bar"><i></i><i></i><i></i><span class="url">mvp-lemon-ten.vercel.app/beranda</span></div>
    <div class="view"><div class="cam"><img class="hold" src="../../assets/rec/beranda_akhir.jpg" alt="" /><video id="rec-beranda" class="clip shot" src="../../assets/rec/beranda.mp4" muted playsinline data-start="1.9" data-duration="5.8" data-media-start="0" data-playback-rate="1.45" data-track-index="1"></video><div class="hl" style="left: 28px; top: 124px; width: 690px; height: 172px"></div></div></div>
  </div>
  <div class="callout" style="left: 500px; top: 740px">langkah berikutnya: <b>KC terlemah</b></div>
  <div class="callout" style="left: 1150px; top: 860px">peta penguasaan <b>6 KC</b></div>
</div>
<!-- @sfx woosh_up@0.0:0.5 impact_boom@0.72:0.6 punch_hit@0.72:0.4 whoosh_deep@1.95:0.4 swipe_zip@2.3:0.35 shutter@~menyarankan-0.4:0.4 notif_pop@~menyarankan+0.3:0.45 swish_fast@~berikutnya:0.4 glass_hi@~berikutnya+0.6:0.45 -->
<script>
(() => {
/* @helpers */
enter("bars");
  const tb = bumper("DEMO", 0.5, { sub: "rekaman MVP asli · data demo", hold: 1.15 });

  rise(".side .n", tb - 0.1, { y: 14 });
  words(".side h2", tb, { stagger: 0.06 });
  rise(".side p", tb + 0.3, { y: 14 });
  tl.fromTo(".win", { y: 80, scale: 0.9, opacity: 0, rotationX: 10 }, { y: 0, scale: 1, opacity: 1, rotationX: 0, duration: 0.8, ease: "expo.out" }, tb - 0.25);
  // kamera: dekati kartu langkah berikutnya, lalu geser ke peta penguasaan
  camTo(".cam", 650, 380, 1.45, w("menyarankan") - 0.5, 1.0);
  camTo(".cam", 1570, 470, 1.45, w("berikutnya") - 0.1, 0.9);

  tl.fromTo(".hl", { opacity: 0, scale: 1.04 }, { opacity: 1, scale: 1, duration: 0.4 }, w("langkah") - 0.4);
  tl.to(".hl", { boxShadow: "0 0 0 10px rgba(224,122,31,.2)", duration: 0.4, yoyo: true, repeat: 3 }, w("langkah"));
  pop($(".callout")[0], w("menyarankan") + 0.3, { from: 0.5, origin: "0% 50%" });
  tl.to($(".callout")[0], { opacity: 0, y: 20, duration: 0.25 }, w("berikutnya"));
  pop($(".callout")[1], w("berikutnya") + 0.6, { from: 0.5, origin: "0% 50%" });
  leave();
  window.__timelines[ID] = tl;
})();
</script>
</template></body></html>

<!doctype html>
<html><head><meta charset="UTF-8" /></head><body><template>
<style>
<!-- @base -->
#f15 { position: absolute; inset: 0; background: transparent; overflow: hidden; }
#f15 .win { left: 450px; top: 90px; width: 1380px; }
#f15 .pair { position: absolute; left: 960px; top: 470px; width: 880px; padding: 24px; border-radius: 28px; display: grid; grid-template-columns: 1fr 1fr; gap: 20px; background: #fff; border: 2px solid var(--line); box-shadow: 0 1px 2px rgba(16,24,40,.04), 0 14px 36px rgba(16,24,40,.07); }
#f15 .pair figure { margin: 0; position: relative; }
#f15 .pair img { display: block; width: 100%; border-radius: 14px; }
#f15 .pair figcaption { margin-top: 12px; font: 700 38px 'Geist', sans-serif; color: var(--ink); display: flex; justify-content: space-between; }
#f15 .pair figcaption b { font-family: 'Geist', sans-serif; color: var(--nt-d); font-weight: 800; }
#f15 .ring { position: absolute; width: 130px; height: 130px; border-radius: 50%; border: 7px solid var(--nt); box-shadow: 0 0 18px rgba(224,122,31,.7); }

#f15 .win .view { height: 862px; }
#f15 .win .view .cam { position: absolute; inset: 0; }
#f15 .win .view video.shot { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }
#f15 .win .view .cam img.hold { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }
</style>
<div id="f15" data-composition-id="f15" data-width="1920" data-height="1080">
  
  <div class="side"><div class="n">DEMO · 02</div><h2>Membaca MRI seperti di klinik</h2><p>gulir slice · window/level · DWI ↔ ADC</p></div>
  <div class="win"><div class="bar"><i></i><i></i><i></i><span class="url">mvp-lemon-ten.vercel.app/latihan</span></div>
    <div class="view"><div class="cam"><img class="hold" src="../../assets/rec/viewer_akhir.jpg" alt="" /><video id="rec-viewer" class="clip shot" src="../../assets/rec/viewer.mp4" muted playsinline data-start="0" data-duration="14.0" data-media-start="0" data-playback-rate="1.0" data-track-index="1"></video></div></div>
  </div>
  <div class="callout" style="left: 560px; top: 190px">↕ <b>gulir</b> slice</div>
  <div class="callout" style="left: 560px; top: 320px">◐ <b>W/L</b> atur kontras</div>
  <div class="pair">
    <figure><img src="../../assets/mri/sub-654/dwi_z15.png" alt="" /><div class="ring" style="left: 115px; top: 150px"></div><figcaption>DWI <b>terang</b></figcaption></figure>
    <figure><img src="../../assets/mri/sub-654/adc_z15.png" alt="" /><div class="ring" style="left: 115px; top: 150px"></div><figcaption>ADC <b>gelap</b></figcaption></figure>
  </div>
</div>
<!-- @sfx whoosh@0.0:0.45 blips@~menggulir:0.4 notif_pop@~menggulir+0.1:0.4 dbl_click@~window-0.3:0.35 glass_tap@~window:0.45 swipe_zip@~membandingkan:0.35 woosh_up@~Infark-0.4:0.4 thud_soft@~Infark:0.35 mar6@~terang:0.5 mar1@~gelap:0.5 -->
<script>
(() => {
/* @helpers */
enter("push");

  rise(".side .n", 0.6, { y: 14 });
  rise(".side h2", 0.7, { y: 24 });
  rise(".side p", 0.85, { y: 14 });
  tl.fromTo(".win", { y: 50, scale: 0.97, opacity: 0 }, { y: 0, scale: 1, opacity: 1, duration: 0.7 }, 0.45);

  camTo(".cam", 760, 600, 1.35, w("menggulir") - 0.3, 1.4);
  camTo(".cam", 960, 600, 1, w("Infark") - 0.6, 0.8);
  pop($(".callout")[0], w("menggulir"), { from: 0.7, origin: "0% 50%" });
  pop($(".callout")[1], w("window"), { from: 0.7, origin: "0% 50%" });
  tl.fromTo(".pair", { y: 120, opacity: 0, rotation: 2 }, { y: 0, opacity: 1, rotation: 0, duration: 0.7, ease: "back.out(1.3)" }, w("Infark") - 0.3);
  const rings = [...$(".pair .ring")];
  pop(rings[0], w("terang"), { from: 1.8, ease: "power3.out" });
  pop(rings[1], w("gelap"), { from: 1.8, ease: "power3.out" });
  tl.fromTo($(".pair figcaption b")[0], { color: "#334155" }, { color: "#c2620f", duration: 0.3 }, w("terang"));
  tl.fromTo($(".pair figcaption b")[1], { color: "#334155" }, { color: "#c2620f", duration: 0.3 }, w("gelap"));
  tl.to($(".callout"), { opacity: 0, duration: 0.3 }, w("Infark") - 0.4);
  burst(1164, 709, w("terang"), { r0: 70, r1: 170, n: 10, shake: 0 });
  burst(1590, 709, w("gelap"), { r0: 70, r1: 170, n: 10, c2: "#0f3a43" });
  leave();
  window.__timelines[ID] = tl;
})();
</script>
</template></body></html>

<!doctype html>
<html><head><meta charset="UTF-8" /></head><body><template>
<style>
<!-- @base -->
#f18 { position: absolute; inset: 0; background: transparent; overflow: hidden; }
#f18 .win { left: 450px; top: 110px; width: 1380px; }
#f18 .sina-wrap { position: absolute; left: 160px; top: 760px; }

#f18 .win .view { height: 862px; }
#f18 .win .view .cam { position: absolute; inset: 0; }
#f18 .win .view video.shot { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }
#f18 .win .view .cam img.hold { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }
</style>
<div id="f18" data-composition-id="f18" data-width="1920" data-height="1080">
  
  <div class="side"><div class="n">DEMO · 05</div><h2>Tutor yang membimbing</h2><p>mode Sokratik · fakta terkunci sebelum submit</p></div>
  <div class="win"><div class="bar"><i></i><i></i><i></i><span class="url">mvp-lemon-ten.vercel.app/latihan</span></div>
    <div class="view"><div class="cam"><img class="hold" src="../../assets/rec/tutor_akhir.jpg" alt="" /><video id="rec-tutor" class="clip shot" src="../../assets/rec/tutor.mp4" muted playsinline data-start="0" data-duration="9.7" data-media-start="1.6" data-playback-rate="1" data-track-index="1"></video></div></div>
  </div>
  <div class="callout" style="left: 1020px; top: 38px">tidak memberi <b>jawaban langsung</b></div>
  <div class="callout" style="left: 500px; top: 930px">membimbing dengan <b>pertanyaan</b></div>
  <div class="sina-wrap"><!-- @include sina p=f18s w=210 --></div>
</div>
<!-- @sfx swipe_zip@0.0:0.45 hop@1.2:0.45 keys_clack@~bertanya:0.35 swish_fast@1.0:0.3 data_chirps@~Sokratik:0.3 notif_pop@~langsung-0.2:0.45 bubble_hi@~membimbing:0.4 mar5@~pertanyaan-0.3:0.45 glass_tap@~temuan:0.35 -->
<script>
(() => {
/* @helpers */
enter("slideup");

  rise(".side .n", 0.6, { y: 14 });
  rise(".side h2", 0.7, { y: 24 });
  rise(".side p", 0.85, { y: 14 });
  tl.fromTo(".win", { y: 50, scale: 0.97, opacity: 0 }, { y: 0, scale: 1, opacity: 1, duration: 0.7 }, 0.45);

  // kamera mendekat ke panel tutor
  tl.fromTo(".cam", { scale: 1, transformOrigin: "100% 100%" }, { scale: 1.55, duration: 1.6, ease: "power3.inOut" }, 1.0);
  pop($(".callout")[0], w("langsung") - 0.2, { from: 0.6, origin: "0% 50%" });
  pop($(".callout")[1], w("pertanyaan") - 0.3, { from: 0.6, origin: "0% 50%" });
  tl.fromTo(".sina-wrap", { x: -260, rotation: -30 }, { x: 0, rotation: 12, duration: 0.7, ease: "back.out(1.6)" }, 1.2);
  bob(".sina-rig", 2.0, END, 6, 1.5);
  blink(".sina-lid", [3.0, 6.5, 9.8]);
  tl.fromTo(".sina-arm-r", { rotation: 0, svgOrigin: "62 6" }, { rotation: -50, duration: 0.4, ease: "back.out(2)" }, w("membimbing"));
  leave();
  window.__timelines[ID] = tl;
})();
</script>
</template></body></html>

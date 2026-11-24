<!doctype html>
<html><head><meta charset="UTF-8" /></head><body><template>
<style>
<!-- @base -->
#f19 { position: absolute; inset: 0; background: transparent; overflow: hidden; }
#f19 .stage { position: absolute; inset: 0; perspective: 2200px; }
#f19 .win .view { height: 641px; }
#f19 .win .view .cam { position: absolute; inset: 0; }
#f19 .win .view video.shot { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; object-position: 50% 0%; }
#f19 .win .view img.shot { position: absolute; left: 0; top: 0; width: 100%; }
#f19 .c { left: 600px; top: 200px; width: 1140px; z-index: 3; }
#f19 .l { left: 430px; top: 270px; width: 760px; z-index: 1; filter: brightness(.82); }
#f19 .r { left: 1220px; top: 270px; width: 640px; z-index: 1; filter: brightness(.82); }
#f19 .l .view, #f19 .r .view { height: 470px; }
#f19 .win .view .cam img.hold { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }
</style>
<div id="f19" data-composition-id="f19" data-width="1920" data-height="1080">
  
  <div class="side"><div class="n">DEMO · 06</div><h2>Dasbor dosen</h2><p>peta penguasaan · kesalahan tersering · audit tutor</p></div>
  <div class="stage">
    <div class="win l"><div class="bar"><i></i><i></i><i></i></div><div class="view"><img class="shot" src="../../assets/screens/tinjau.png" alt="" /></div></div>
    <div class="win r"><div class="bar"><i></i><i></i><i></i></div><div class="view"><img class="shot" src="../../assets/screens/audit.png" alt="" /></div></div>
    <div class="win c"><div class="bar"><i></i><i></i><i></i><span class="url">mvp-lemon-ten.vercel.app/dosen</span></div><div class="view"><div class="cam"><img class="hold" src="../../assets/rec/dosen_akhir.jpg" alt="" /><video id="rec-dosen" class="clip shot" src="../../assets/rec/dosen.mp4" muted playsinline data-start="0" data-duration="10.0" data-media-start="0" data-playback-rate="1.26" data-track-index="1"></video></div></div></div>
  </div>
  <div class="callout" style="left: 600px; top: 900px">peta <b>penguasaan</b> kelas</div>
  <div class="callout" style="left: 460px; top: 900px">kesalahan <b>tersering</b></div>
  <div class="callout" style="left: 1120px; top: 900px">setiap jawaban tutor <b>bisa diaudit</b></div>
</div>
<!-- @sfx whoosh@0.0:0.45 card_flip@0.9:0.4 card_flip@1.05:0.35 mar2@~peta:0.45 woosh_down@~kesalahan-0.4:0.35 mar4@~kesalahan:0.45 woosh_up@~audit-0.4:0.4 mar6@~audit:0.5 tech_beep@~jawaban:0.4 -->
<script>
(() => {
/* @helpers */
enter("push");
  rise(".side .n", 0.6, { y: 14 });
  rise(".side h2", 0.7, { y: 24 });
  rise(".side p", 0.85, { y: 14 });
  tl.fromTo(".win.c", { y: 60, opacity: 0, scale: 0.95 }, { y: 0, opacity: 1, scale: 1, duration: 0.7 }, 0.45);
  tl.fromTo(".win.l", { rotationY: 70, opacity: 0, transformOrigin: "100% 50%" }, { rotationY: 28, opacity: 1, duration: 0.9 }, 0.9);
  tl.fromTo(".win.r", { rotationY: -70, opacity: 0, transformOrigin: "0% 50%" }, { rotationY: -28, opacity: 1, duration: 0.9 }, 1.05);
  const co = [...$(".callout")];
  // karosel: jendela kiri (tinjau kesalahan) lalu kanan (audit tutor) maju ke depan
  pop(co[0], w("peta"), { from: 0.6, origin: "0% 50%" });
  tl.to(co[0], { opacity: 0, duration: 0.2 }, w("kesalahan") - 0.3);
  tl.to(".win.l", { rotationY: 0, x: 120, scale: 1.12, filter: "brightness(1)", zIndex: 5, duration: 0.6, ease: "power3.inOut" }, w("kesalahan") - 0.4);
  pop(co[1], w("kesalahan"), { from: 0.6, origin: "0% 50%" });
  tl.to(".win.l", { rotationY: 28, x: 0, scale: 1, filter: "brightness(.82)", zIndex: 1, duration: 0.5, ease: "power3.inOut" }, w("audit") - 0.5);
  tl.to(co[1], { opacity: 0, duration: 0.2 }, w("audit") - 0.4);
  tl.to(".win.r", { rotationY: 0, x: -260, scale: 1.15, filter: "brightness(1)", zIndex: 5, duration: 0.6, ease: "power3.inOut" }, w("audit") - 0.4);
  pop(co[2], w("audit"), { from: 0.6, origin: "0% 50%" });
  leave();
  window.__timelines[ID] = tl;
})();
</script>
</template></body></html>

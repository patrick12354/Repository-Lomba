<!doctype html>
<html><head><meta charset="UTF-8" /></head><body><template>
<style>
<!-- @base -->
#f08 { position: absolute; inset: 0; background: transparent; overflow: hidden; }
/* ruang baca radiologi: gelap, citra yang menyala */
#f08 .room { position: absolute; inset: 0; background: radial-gradient(ellipse 80% 70% at 50% 45%, #13213a, #070d18 75%); }
#f08 .wall { position: absolute; left: 30px; top: 130px; width: 1860px; display: grid; grid-template-columns: repeat(9, 196px); gap: 12px; }
#f08 .wall img { width: 196px; height: 196px; border-radius: 8px; display: block; background: #000; }
#f08 .count { position: absolute; left: 0; right: 0; top: 330px; text-align: center; color: #fff; }
#f08 .count .v { font: 700 300px/1 'Oswald', sans-serif; font-variant-numeric: tabular-nums; letter-spacing: -.01em; text-shadow: 0 10px 60px rgba(0,0,0,.6); }
#f08 .count .s { margin-top: 10px; font: 700 56px 'Arvo', serif; color: #cbd5e1; }
#f08 .cam { position: absolute; inset: 0; transform-origin: 960px 540px; }
#f08 .case { position: absolute; left: 610px; top: 190px; width: 700px; height: 700px; border-radius: 14px; overflow: hidden; background: #000; box-shadow: 0 0 0 3px #1e293b, 0 40px 120px rgba(0,0,0,.7); opacity: 0; }
#f08 .case img { position: absolute; inset: 0; width: 100%; height: 100%; }
#f08 .key { position: absolute; left: 1360px; top: 420px; width: 200px; height: 200px; border-radius: 50%; background: var(--nt); display: grid; place-items: center; box-shadow: 0 20px 50px rgba(224,122,31,.35); opacity: 0; }
</style>
<div id="f08" data-composition-id="f08" data-width="1920" data-height="1080" data-amb="0" data-split="lengkap">
  <div class="room"></div>
  <div class="cam">
    <div class="wall"></div>
    <div class="case"><img src="../../assets/mri/sub-1413/dwi_z14.png" alt="" /><img class="mask" src="../../assets/mri/sub-1413/mask_z14.png" alt="" /></div>
  </div>
  <div class="count"><div class="v">0</div><div class="s">pasien stroke, MRI klinis</div></div>
  <div class="key"><svg width="116" height="116" viewBox="0 0 96 96"><circle cx="34" cy="48" r="20" fill="none" stroke="#fff" stroke-width="10" /><path d="M54,48 H88 M76,48 V64 M88,48 V60" fill="none" stroke="#fff" stroke-width="10" stroke-linecap="round" /></svg></div>
</div>
<script>
(() => {
/* @helpers */
  const wall = $1(".wall");
  for (let i = 0; i < 36; i++) {
    const img = document.createElement("img");
    img.src = `assets/mri/wall/w${String(i).padStart(2, "0")}.png`;
    wall.appendChild(img);
  }
  enter("cut");
  // 1. "ada peluang": dinding MRI pasien nyata menyala, ubin demi ubin dari tengah
  tl.fromTo(wall.children, { opacity: 0, scale: 0.9 }, { opacity: 1, scale: 1, duration: 0.4, stagger: { each: 0.018, grid: [4, 9], from: "center" } }, 0.1);
  // 2a. 1.505 pasien
  const tc = w("Dataset") - 0.1;
  tl.to(wall.children, { opacity: 0.22, duration: 0.4, ease: "power2.out" }, tc);
  tl.fromTo(".count", { opacity: 0, y: 30 }, { opacity: 1, y: 0, duration: 0.5 }, tc);
  count($1(".count .v"), 0, 1505, tc, 0.9, { ease: "power3.out" });
  // 2b. satu kasus maju ke depan, mask ahli terlukis di atasnya
  const tm = w("lengkap");
  tl.to(".count", { opacity: 0, y: -30, duration: 0.3, ease: "power2.in" }, tm - 0.3);
  tl.to(wall.children, { opacity: 0.12, duration: 0.4 }, tm);
  tl.fromTo(".case", { opacity: 0, scale: 0.3, x: -250, y: 120 }, { opacity: 1, scale: 1, x: 0, y: 0, duration: 0.6, ease: "expo.out" }, tm - 0.05);
  tl.fromTo(".case .mask", { clipPath: "circle(0% at 33% 33%)" }, { clipPath: "circle(80% at 33% 33%)", duration: 0.7, ease: "power2.inOut" }, tm + 0.4);
  // 3. "jaringan mana yang infark": kamera masuk ke lesi
  const tz = w("Untuk");
  tl.to(".cam", { scale: 1.45, x: (960 - (610 + 0.33 * 700)) * 1.45 * 0.6, y: (540 - (190 + 0.33 * 700)) * 1.45 * 0.6, duration: 0.8, ease: "power4.inOut" }, tz);
  // 4. itu kunci jawaban
  const tk = w("Itu");
  tl.to(".cam", { scale: 1, x: -230, y: 0, duration: 0.7, ease: "power4.inOut" }, tk - 0.1);
  tl.fromTo(".key", { opacity: 0, x: 120, rotation: -90 }, { opacity: 1, x: 0, rotation: 0, duration: 0.6, ease: "expo.out" }, tk + 0.2);
  leave();
  window.__timelines[ID] = tl;
})();
</script>
</template></body></html>

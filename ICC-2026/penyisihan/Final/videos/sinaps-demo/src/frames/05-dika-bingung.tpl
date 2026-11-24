<!doctype html>
<html><head><meta charset="UTF-8" /></head><body><template>
<style>
<!-- @base -->
#f05 { position: absolute; inset: 0; background: transparent; overflow: hidden; }
#f05 .screen { position: absolute; left: 90px; top: 110px; width: 760px; height: 540px; border-radius: 18px; background: #fff; border: 6px solid #10313a; box-shadow: 0 20px 50px rgba(16,24,40,.16); }
#f05 .screen .hd { position: absolute; left: 34px; right: 34px; top: 24px; display: flex; justify-content: space-between; font: 700 26px 'Geist', sans-serif; color: var(--muted); }
#f05 .screen h3 { position: absolute; left: 0; right: 0; top: 36px; margin: 0; text-align: center; font-size: 50px; font-weight: 700; }
#f05 .screen img { position: absolute; left: 50%; bottom: 34px; width: 390px; height: 390px; margin-left: -195px; border-radius: 12px; }
#f05 .screen .one { position: absolute; left: 400px; top: 200px; width: 320px; font: 700 34px/1.3 'Geist', sans-serif; color: var(--ink-2); }
#f05 .screen .one b { display: block; font: 700 120px/1 'Oswald', sans-serif; color: var(--ink); }
#f05 .k1 { position: absolute; left: 90px; top: 690px; }
#f05 .k1 .tagk { display: inline-block; padding: 12px 24px; border-radius: 14px; background: var(--ink); color: #fff; font: 700 34px 'Oswald', sans-serif; letter-spacing: .08em; text-transform: uppercase; }
#f05 .k1 p { margin: 12px 0 0; font: 700 40px 'Geist', sans-serif; color: var(--ink); }
#f05 .dosen { position: absolute; left: 600px; top: 470px; }
#f05 .desk { position: absolute; left: 960px; top: 900px; width: 1000px; height: 200px; border-radius: 10px 10px 0 0; background: #9a7656; }
#f05 .desk::before { content: ""; position: absolute; left: -10px; right: -10px; top: -20px; height: 24px; border-radius: 8px; background: #b98f68; }
#f05 .fa { position: absolute; left: 990px; top: 560px; }
#f05 .fb { position: absolute; left: 1690px; top: 560px; }
#f05 .dk { position: absolute; left: 1270px; top: 470px; }
#f05 .cloud { position: absolute; left: 1060px; top: 30px; width: 820px; height: 440px; }
#f05 .stack { position: absolute; left: 1150px; top: 70px; width: 640px; height: 330px; perspective: 1400px; }
#f05 .stack .rot { position: absolute; inset: 0; transform-style: preserve-3d; }
#f05 .sl { position: absolute; left: 230px; top: 40px; width: 230px; height: 230px; border-radius: 10px; border: 3px solid #e5e7eb; background: #000; box-shadow: 0 8px 20px rgba(16,24,40,.25); }
#f05 .cnt { position: absolute; left: 1640px; top: 300px; padding: 10px 22px; border-radius: 18px; background: var(--ink); color: #fff; font: 700 28px 'Geist', sans-serif; box-shadow: 0 12px 30px rgba(16,24,40,.25); }
#f05 .cnt b { font: 700 64px/1 'Oswald', sans-serif; color: #fbbf24; margin-right: 8px; vertical-align: -6px; }
#f05 .seq { position: absolute; left: 1130px; top: 400px; display: flex; gap: 12px; }
#f05 .seq span { padding: 8px 18px; border-radius: 12px; background: #fff; border: 3px solid var(--teal); font: 700 28px 'Geist', sans-serif; color: var(--teal); }
#f05 .q { position: absolute; width: 96px; height: 96px; border-radius: 50%; background: #fff; border: 5px solid var(--bad); display: grid; place-items: center; font: 700 70px/1 'Oswald', sans-serif; color: var(--bad); box-shadow: 0 10px 24px rgba(220,38,38,.25); }
</style>
<div id="f05" data-composition-id="f05" data-width="1920" data-height="1080">
  <div class="screen">
    <h3>Infark akut pada MRI</h3>
    <img src="../../assets/mri/sub-654/dwi_z15.png" alt="" />
  </div>
  <div class="dosen"><!-- @include dika p=f05t w=220 hair=#9aa3a8 brow=#6b7280 glasses=1 skin=#e2b08e skin2=#c48d68 scrub=#5c4a7a steth=0 --></div>
  <svg class="cloud" viewBox="0 0 820 440"><path d="M120,330 C40,330 20,240 90,215 C60,140 150,90 215,120 C240,50 360,30 410,90 C460,30 590,40 610,120 C690,90 790,150 750,230 C810,260 790,350 700,340 C660,400 540,400 500,350 C450,400 320,410 280,350 C230,390 140,380 120,330 Z" fill="#ffffff" stroke="#10313a" stroke-width="6" stroke-linejoin="round" /><circle class="cb" cx="300" cy="400" r="20" fill="#fff" stroke="#10313a" stroke-width="5" /><circle class="cb" cx="330" cy="436" r="12" fill="#fff" stroke="#10313a" stroke-width="5" /></svg>
  <div class="stack"><div class="rot"></div></div>
  <div class="seq"><span>DWI</span><span>ADC</span><span>FLAIR</span></div>
  <div class="fa"><!-- @include dika p=f05a w=240 hijab=1 hj=#195764 hair=#195764 skin2=#195764 skin=#d39a76 scrub=#aad39c --></div>
  <div class="fb"><!-- @include dika p=f05c w=240 hair=#5a3a28 skin=#e2b08e skin2=#c48d68 scrub=#e07a1f --></div>
  <div class="dk"><!-- @include dika p=f05d w=330 smile=1 worried=0 brows=1 wbrows=0 sweat=0 --></div>
  <div class="desk"></div>
  <div class="q" style="left: 1170px; top: 520px">?</div>
  <div class="q" style="left: 1640px; top: 500px">?</div>
  <div class="q" style="left: 1110px; top: 700px">?</div>
  <div class="q" style="left: 1700px; top: 690px">?</div>
</div>
<!-- @sfx whip@0.0:0.5 mar2@~layar:0.4 shutter@~potongan:0.4 swish_fast@~Padahal-0.2:0.45 woosh_up@~klinik:0.4 swipe_zip@~puluhan-0.3:0.45 counter_roll@~puluhan:0.3 glass_tap@~beberapa:0.4 glass_hi@~sekuens:0.4 question_pop@~bingung-0.1:0.5 question_pop@~harus:0.45 bubble_hi@~mulai:0.4 question_pop@~dari:0.45 slide_whistle@~mana:0.25 -->
<script>
(() => {
/* @helpers */
  const rot = $1(".stack .rot");
  const zs = [15, 16, 14, 17, 13, 18, 12];
  const slices = zs.map((z, i) => {
    const img = document.createElement("img");
    img.className = "sl";
    img.src = `assets/mri/sub-654/${i % 3 === 1 ? "adc" : i % 3 === 2 ? "flair" : "dwi"}_z${String(z).padStart(2, "0")}.png`;
    rot.appendChild(img);
    return img;
  });
  enter("push");
  // kiri: kuliah, satu gambar statis
  pop(".screen", 0.45, { from: 0.9, ease: "back.out(1.5)" });
  words(".screen h3", w("layar") - 0.2);
  pop(".screen img", w("potongan") - 0.2, { from: 0.5, ease: "back.out(2)" });
  tl.fromTo(".dosen", { x: -200, opacity: 0 }, { x: 0, opacity: 1, duration: 0.6, ease: "power3.out" }, 0.6);
  tl.fromTo(".dosen .dika-arm-l", { rotation: 0, svgOrigin: "108 272" }, { rotation: 120, duration: 0.5, ease: "back.out(1.6)" }, w("menunjukkan"));
  tl.to(".dosen .dika-arm-l", { rotation: 0, duration: 0.5 }, w("Padahal"));
  bob(".dosen .dika-rig", 0.6, END, 3, 2.4);
  blink(".dosen .dika-lid", [2.5, 7.3]);
  // kanan: Dika dan teman-teman
  tl.fromTo(".dk", { y: 300 }, { y: 0, duration: 0.6, ease: "back.out(1.4)" }, 0.5);
  tl.fromTo(".fa, .fb", { y: 300 }, { y: 0, duration: 0.6, ease: "back.out(1.4)", stagger: 0.1 }, 0.6);
  bob(".dk .dika-rig", 1.2, END, 4, 2.2);
  bob(".fa .dika-rig", 1.2, END, 3, 2.5);
  bob(".fb .dika-rig", 1.2, END, 3, 2.0);
  blink(".dk .dika-lid", [1.8, 4.4, 9.6, 12.3]);
  blink(".fa .dika-lid", [3.1, 8.0]);
  blink(".fb .dika-lid", [2.0, 6.7, 11.0]);
  [".dk", ".fa", ".fb"].forEach((k, i) => tl.fromTo(`${k} .dika-head`, { rotation: 0, svgOrigin: "160 240" }, { rotation: -9, duration: 0.4 }, w("dosen") + i * 0.08));
  // "Padahal di klinik": awan pikiran berisi puluhan slice
  const tp = w("Padahal");
  tl.to(".dk .dika-head", { rotation: 4, duration: 0.4 }, tp);
  tl.fromTo(".cloud", { scale: 0, opacity: 0, transformOrigin: "36% 95%" }, { scale: 1, opacity: 1, duration: 0.6, ease: "back.out(1.6)" }, tp);
  slices.forEach((img, i) => {
    const k = i - 3;
    tl.fromTo(img, { x: 0, y: 30, z: 0, rotationY: 0, rotationX: 0, scale: 0.5, opacity: 0, filter: "brightness(1)" },
      { x: k * 56, y: k * -10, z: k * -40, rotationY: -24, rotationX: 6, scale: 0.85, opacity: 1, filter: `brightness(${0.7 + i * 0.045})`, duration: 0.7, ease: "power3.out" }, w("puluhan") - 0.4 + i * 0.06);
  });
  tl.to(rot, { rotationY: 16, duration: 3.2, ease: "sine.inOut", yoyo: true, repeat: 1 }, w("slice"));
  slices.forEach((img, i) => tl.to(img, { y: "-=26", duration: 0.2, yoyo: true, repeat: 1, ease: "power2.out" }, w("slice") + i * 0.1));
  pop(".seq span", w("beberapa"), { from: 0.4, stagger: 0.18, ease: "back.out(2.4)" });
  // "Dika bingung": tanda tanya, wajah cemas, garuk kepala, teman saling pandang
  const tb = w("bingung");
  tl.to(".dk .dika-m-smile", { opacity: 0, duration: 0.12 }, tb - 0.2);
  tl.to(".dk .dika-m-worried", { opacity: 1, duration: 0.12 }, tb - 0.2);
  tl.to(".dk .dika-brows > g:nth-child(1)", { opacity: 0, duration: 0.12 }, tb - 0.2);
  tl.to(".dk .dika-brows > g:nth-child(2)", { opacity: 1, duration: 0.12 }, tb - 0.2);
  tl.fromTo(".dk .dika-sweat", { opacity: 0, y: -10 }, { opacity: 1, y: 14, duration: 0.8, ease: "power1.in" }, tb);
  tl.fromTo(".dk .dika-arm-r", { rotation: 0, svgOrigin: "212 272" }, { rotation: -165, duration: 0.45, ease: "back.out(1.6)" }, tb - 0.1);
  tl.to(".dk .dika-arm-r", { rotation: -150, duration: 0.12, yoyo: true, repeat: 7, ease: "sine.inOut" }, tb + 0.35);
  tl.fromTo(".dk .dika-head", { rotation: 4 }, { rotation: -6, duration: 0.25, yoyo: true, repeat: 5, ease: "sine.inOut", immediateRender: false }, tb + 0.2);
  [...$(".q")].forEach((q, i) => {
    const t = tb - 0.1 + i * 0.32;
    tl.fromTo(q, { scale: 0, rotation: -40, opacity: 0 }, { scale: 1, rotation: 0, opacity: 1, duration: 0.4, ease: "back.out(3)" }, t);
    tl.to(q, { y: -16, rotation: i % 2 ? 10 : -10, duration: 0.6, yoyo: true, repeat: 2, ease: "sine.inOut" }, t + 0.4);
  });
  tl.to(".fa .dika-head", { rotation: 12, duration: 0.35, ease: "back.out(2)" }, w("harus"));
  tl.to(".fb .dika-head", { rotation: -12, duration: 0.35, ease: "back.out(2)" }, w("harus") + 0.1);
  tl.to(".fa .dika-arm-l", { rotation: 40, svgOrigin: "108 272", duration: 0.4 }, w("mulai"));
  tl.to(".fb .dika-arm-r", { rotation: -40, svgOrigin: "212 272", duration: 0.4 }, w("mulai"));
  leave();
  window.__timelines[ID] = tl;
})();
</script>
</template></body></html>

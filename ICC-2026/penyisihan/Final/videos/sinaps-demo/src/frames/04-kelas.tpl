<!doctype html>
<html><head><meta charset="UTF-8" /></head><body><template>
<style>
<!-- @base -->
#f04 { position: absolute; inset: 0; background: transparent; overflow: hidden; }
#f04 .world { position: absolute; left: 0; top: 0; width: 1920px; height: 1080px; }
#f04 .wall { position: absolute; left: 0; top: 0; width: 1920px; height: 780px; background: linear-gradient(#f3f8f7, #e9f1ef); }
#f04 .floor { position: absolute; left: 0; top: 780px; width: 1920px; height: 300px; background: linear-gradient(#dfe6e3, #cfd9d5); }
#f04 .skirt { position: absolute; left: 0; top: 770px; width: 1920px; height: 14px; background: #c3cfcb; }
#f04 .screen { position: absolute; left: 110px; top: 90px; width: 790px; height: 470px; border-radius: 18px; background: #fff; border: 6px solid #10313a; box-shadow: 0 20px 50px rgba(16,24,40,.18); overflow: hidden; }
#f04 .screen .glow { position: absolute; inset: 0; background: radial-gradient(ellipse at 50% 40%, rgba(255,255,255,0), rgba(25,87,100,.10)); }
#f04 .screen .hd { position: absolute; left: 36px; top: 26px; right: 36px; display: flex; justify-content: space-between; font: 700 26px 'Geist', sans-serif; color: var(--muted); }
#f04 .screen h3 { position: absolute; left: 36px; top: 70px; margin: 0; font-size: 58px; line-height: 1.05; font-weight: 700; color: var(--ink); }
#f04 .screen h3 b { color: var(--teal); }
#f04 .screen img { position: absolute; right: 40px; bottom: 34px; width: 230px; height: 230px; border-radius: 12px; }
#f04 .screen .bul { position: absolute; left: 40px; bottom: 44px; font: 700 32px/1.6 'Geist', sans-serif; color: var(--ink-2); }
#f04 .screen .bul i { font-style: normal; color: var(--nt-d); }
#f04 .stand { position: absolute; left: 495px; top: 560px; width: 14px; height: 220px; background: #9fb1ad; }
#f04 .clock { position: absolute; left: 1700px; top: 80px; width: 120px; height: 120px; }
#f04 .tdesk { position: absolute; left: 640px; top: 640px; width: 420px; height: 160px; border-radius: 10px 10px 0 0; background: #8a6a4d; }
#f04 .tdesk::before { content: ""; position: absolute; left: -14px; right: -14px; top: -18px; height: 22px; border-radius: 8px; background: #a8835f; }
#f04 .dosen { position: absolute; left: 820px; top: 300px; }
#f04 .row2 { position: absolute; top: 400px; }
#f04 .row1 { position: absolute; top: 470px; }
#f04 .desk { position: absolute; border-radius: 10px 10px 0 0; background: #9a7656; }
#f04 .desk::before { content: ""; position: absolute; left: -10px; right: -10px; top: -20px; height: 24px; border-radius: 8px; background: #b98f68; }
#f04 .book { position: absolute; width: 90px; height: 16px; border-radius: 4px; }
#f04 .lap { position: absolute; left: 1525px; top: 742px; width: 150px; height: 50px; }
#f04 .tag { position: absolute; left: 1395px; top: 452px; padding: 12px 24px; border-radius: 16px; background: var(--ink); color: #fff; font: 700 34px 'Geist', sans-serif; white-space: nowrap; box-shadow: 0 10px 26px rgba(16,24,40,.25); }
#f04 .tag small { display: block; font: 600 22px 'Geist', sans-serif; color: #aad39c; letter-spacing: .06em; text-transform: uppercase; }
#f04 .tag::after { content: ""; position: absolute; left: 60px; bottom: -16px; border: 10px solid transparent; border-top: 10px solid var(--ink); border-bottom: 0; }
#f04 .cap { position: absolute; left: 110px; top: 600px; }
#f04 .chat { position: absolute; padding: 8px 16px; border-radius: 16px; background: #fff; border: 3px solid var(--line-2); font: 700 28px 'Geist', sans-serif; color: var(--ink-2); }
</style>
<div id="f04" data-composition-id="f04" data-width="1920" data-height="1080" data-amb="0" data-drift="0.015">
  <div class="world">
    <div class="wall"></div><div class="floor"></div><div class="skirt"></div>
    <svg class="clock" viewBox="-60 -60 120 120"><circle r="54" fill="#fff" stroke="#10313a" stroke-width="7" /><line class="ch-h" x1="0" y1="0" x2="0" y2="-26" stroke="#10313a" stroke-width="7" stroke-linecap="round" /><line class="ch-m" x1="0" y1="0" x2="0" y2="-40" stroke="#e07a1f" stroke-width="5" stroke-linecap="round" /><circle r="6" fill="#10313a" /></svg>
    <div class="stand"></div>
    <div class="screen">
      <div class="glow"></div>
      <h3>Membaca<br /><b>MRI stroke</b></h3>
      <div class="bul"><i>●</i> DWI · ADC<br /><i>●</i> lesi infark</div>
      <img src="../../assets/mri/sub-654/dwi_z15.png" alt="" />
    </div>
    <div class="dosen"><!-- @include dika p=f04t w=230 hair=#9aa3a8 brow=#6b7280 glasses=1 skin=#e2b08e skin2=#c48d68 scrub=#5c4a7a steth=0 --></div>
    <div class="tdesk"></div>
    <!-- baris belakang -->
    <div class="row2" style="left: 1235px"><!-- @include dika p=f04b1 w=170 hair=#3b2a20 skin=#c48d68 skin2=#a96f4c scrub=#2563eb --></div>
    <div class="row2" style="left: 1480px"><!-- @include dika p=f04b2 w=170 hijab=1 hj=#c2620f hair=#c2620f skin2=#c2620f skin=#e2b08e scrub=#6fa77a --></div>
    <div class="row2" style="left: 1725px"><!-- @include dika p=f04b3 w=170 hair=#2a2220 skin=#a96f4c skin2=#8a5a3c scrub=#195764 --></div>
    <div class="desk" style="left: 1200px; top: 650px; width: 720px; height: 130px"></div>
    <!-- baris depan: teman berhijab, Dika, teman -->
    <div class="row1 fa" style="left: 1140px"><!-- @include dika p=f04a w=230 hijab=1 hj=#195764 hair=#195764 skin2=#195764 skin=#d39a76 scrub=#aad39c --></div>
    <div class="row1 dk" style="left: 1400px"><!-- @include dika p=f04d w=230 --></div>
    <div class="row1 fb" style="left: 1660px"><!-- @include dika p=f04c w=230 hair=#5a3a28 skin=#e2b08e skin2=#c48d68 scrub=#e07a1f --></div>
    <div class="desk" style="left: 1090px; top: 800px; width: 860px; height: 280px"></div>
    <div class="book" style="left: 1190px; top: 770px; background: #e07a1f"></div>
    <div class="book" style="left: 1205px; top: 756px; background: #195764"></div>
    <svg class="lap" viewBox="0 0 150 50"><path d="M20,0 H130 L140,40 H10 Z" fill="#334155" /><rect x="0" y="40" width="150" height="10" rx="4" fill="#64748b" /><circle cx="75" cy="20" r="6" fill="#aad39c" /></svg>
    <div class="book" style="left: 1760px; top: 770px; background: #6fa77a"></div>
    <div class="chat" style="left: 1150px; top: 400px">MRI?</div>
    <div class="chat" style="left: 1760px; top: 420px">kuis?</div>
    <div class="tag">Dika</div>
  </div>
</div>
<!-- @sfx class_chatter@0.0:0.35 school_bell@0.2:0.45 hop@~Dika-0.1:0.45 notif_pop@~Dika+0.1:0.5 whoosh_deep@~kelas-0.4:0.45 projector_on@~neuroradiologi-0.2:0.45 snap@~belajar:0.4 shutter@~MRI:0.4 mar5@~stroke:0.45 -->
<script>
(() => {
/* @helpers */
  const W = $1(".world");
  enter("cut");
  // kamera: mulai dekat di Dika, mundur memperlihatkan seluruh kelas saat "kelas neuroradiologi"
  tl.set(W, { transformOrigin: "0px 0px" }, 0);
  tl.set(W, { scale: 2.0, x: -2000, y: -520 }, 0);
  tl.to(W, { scale: 1, x: 0, y: 0, duration: 1.3, ease: "power4.inOut" }, w("kelas") - 0.3);
  // jam dinding
  tl.fromTo(".ch-m", { rotation: 0, svgOrigin: "0 0" }, { rotation: 360, duration: END, ease: "none" }, 0);
  tl.fromTo(".ch-h", { rotation: 40, svgOrigin: "0 0" }, { rotation: 70, duration: END, ease: "none" }, 0);
  // semua tokoh bernapas & berkedip
  bob(".row2 .dika-rig", 0.2, END, 3, 2.4);
  bob(".fa .dika-rig", 0.3, END, 4, 2.1);
  bob(".fb .dika-rig", 0.5, END, 4, 2.3);
  bob(".dosen .dika-rig", 0.4, END, 3, 2.6);
  blink(".dk .dika-lid", [1.9, 4.8, 7.6]);
  blink(".fa .dika-lid", [1.2, 5.6]);
  blink(".fb .dika-lid", [2.6, 6.4]);
  blink(".row2 .dika-lid", [3.1, 6.9]);
  blink(".dosen .dika-lid", [2.2, 6.1]);
  // obrolan sebelum kelas
  pop($(".chat")[0], 0.3, { from: 0.4, ease: "back.out(3)" });
  pop($(".chat")[1], 0.7, { from: 0.4, ease: "back.out(3)" });
  tl.to(".chat", { opacity: 0, scale: 0.6, duration: 0.25 }, w("kelas") - 0.6);
  tl.fromTo(".fa .dika-head", { rotation: 0, svgOrigin: "160 240" }, { rotation: 10, duration: 0.4, yoyo: true, repeat: 1, ease: "sine.inOut" }, 0.4);
  tl.fromTo(".fb .dika-head", { rotation: 0, svgOrigin: "160 240" }, { rotation: -10, duration: 0.4, yoyo: true, repeat: 1, ease: "sine.inOut" }, 0.8);
  // Dika menyapa, label nama
  tl.fromTo(".dk .dika-rig", { y: 0 }, { y: -18, duration: 0.18, yoyo: true, repeat: 1, ease: "power2.out", immediateRender: false }, w("Dika") - 0.1);
  tl.fromTo(".dk .dika-arm-r", { rotation: 0, svgOrigin: "212 272" }, { rotation: -150, duration: 0.4, ease: "back.out(1.8)" }, w("Dika"));
  tl.to(".dk .dika-arm-r", { rotation: -130, duration: 0.2, yoyo: true, repeat: 5, ease: "sine.inOut" }, w("Dika") + 0.4);
  tl.to(".dk .dika-arm-r", { rotation: 0, duration: 0.4 }, w("kelas") - 0.2);
  tl.fromTo(".tag", { y: 30, scale: 0.5, opacity: 0, transformOrigin: "60px 100%" }, { y: 0, scale: 1, opacity: 1, duration: 0.45, ease: "back.out(2.4)" }, w("Dika") + 0.1);
  // proyektor menyala, dosen menunjuk layar
  tl.fromTo(".screen", { filter: "brightness(.35)" }, { filter: "brightness(1)", duration: 0.5, ease: "steps(3)" }, w("neuroradiologi") - 0.2);
  tl.set(".screen", { filter: "none" }, w("neuroradiologi") + 0.35);
  words(".screen h3", w("neuroradiologi"), { stagger: 0.08 });
  rise(".screen .bul", w("belajar"), { y: 20 });
  pop(".screen img", w("MRI") - 0.1, { from: 0.4, ease: "back.out(2)" });
  tl.fromTo(".dosen .dika-arm-l", { rotation: 0, svgOrigin: "108 272" }, { rotation: 118, duration: 0.5, ease: "back.out(1.6)" }, w("neuroradiologi"));
  tl.fromTo(".dosen .dika-head", { rotation: 0, svgOrigin: "160 240" }, { rotation: -10, duration: 0.4 }, w("neuroradiologi"));
  // semua menoleh ke layar
  [".dk", ".fa", ".fb"].forEach((k, i) => tl.to(`${k} .dika-head`, { rotation: -8, duration: 0.4, ease: "power2.out" }, w("membaca") + i * 0.08));
  leave();
  window.__timelines[ID] = tl;
})();
</script>
</template></body></html>

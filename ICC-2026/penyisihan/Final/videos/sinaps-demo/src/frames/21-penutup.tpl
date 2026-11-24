<!doctype html>
<html><head><meta charset="UTF-8" /></head><body><template>
<style>
<!-- @base -->
#f21 { position: absolute; inset: 0; background: transparent; overflow: hidden; }
#f21 .halo { display: none; }
#f21 .dika-wrap { position: absolute; left: 230px; top: 380px; }
#f21 .sina-wrap { position: absolute; left: 560px; top: 640px; }
#f21 .spark { position: absolute; left: 520px; top: 560px; }
#f21 .lock { position: absolute; left: 1040px; top: 200px; display: flex; align-items: center; gap: 36px; }
#f21 .word { font-family: 'Oswald', sans-serif; font-weight: 600; font-size: 170px; line-height: 1; letter-spacing: .14em; text-transform: uppercase; font-size: 150px; }
#f21 .line { position: absolute; left: 1046px; top: 420px; width: 800px; font-size: 54px; line-height: 1.2; font-weight: 700; }
#f21 .line b { color: var(--teal); }
#f21 .team { position: absolute; left: 1046px; top: 720px; font: 700 34px 'Geist', sans-serif; color: var(--ink); line-height: 1.45; }
#f21 .team span { display: block; font: 600 28px 'Geist', sans-serif; color: var(--muted); }
#f21 .url { position: absolute; left: 1046px; top: 860px; padding: 20px 36px; border-radius: 999px; background: var(--teal); color: #fff; font: 700 38px 'Geist', sans-serif; box-shadow: 0 10px 0 #0f3a43; }
#f21 .disc { position: absolute; left: 1046px; right: 40px; bottom: 34px; font: 600 24px 'Geist', sans-serif; color: var(--muted); }
</style>
<div id="f21" data-composition-id="f21" data-width="1920" data-height="1080">
  
  <div class="halo"></div>
  <div class="dika-wrap"><!-- @include dika p=f21d w=330 --></div>
  <div class="sina-wrap"><!-- @include sina p=f21s w=260 smile=0 open=1 --></div>
  <svg class="spark" width="120" height="120" viewBox="-60 -60 120 120"><g stroke="#f09a6c" stroke-width="6" stroke-linecap="round"><path d="M0,-50 V-26" /><path d="M0,26 V50" /><path d="M-50,0 H-26" /><path d="M26,0 H50" /><path d="M-35,-35 L-19,-19" /><path d="M35,-35 L19,-19" /></g></svg>
  <div class="lock"><!-- @include logo p=f21l w=170 --><span class="word">Sinaps</span></div>
  <div class="line">Latihan membaca MRI stroke, <b>kapan saja</b>, dengan umpan balik yang bisa dipercaya.</div>
  <div class="team">Tim Rizzz · Sains Data, Universitas Airlangga<span>ICC 2026 · Campus Data Week</span></div>
  <div class="url">mvp-lemon-ten.vercel.app</div>
  <div class="disc">Alat bantu belajar, bukan alat diagnosis · data SOOP (OpenNeuro ds004889, CC0)</div>
</div>
<!-- @sfx shimmer_sweep@0.0:0.4 swish_fast@0.4:0.4 hop@0.65:0.45 punch_hit@~SINAPS-0.2:0.45 success_arp@~SINAPS:0.4 clap@2.25:0.65 confetti@2.25:0.5 sparkle@2.3:0.4 snap@~Latihan-0.1:0.35 mar3@~umpan:0.4 notif_pop@~dipercaya:0.5 glass_hi@~dipercaya+0.5:0.4 ui_swell@~dipercaya+0.7:0.35 -->
<script>
(() => {
/* @helpers */
enter("fade");
  const word = $1(".word");
  word.innerHTML = [...word.textContent].map((c) => `<span class="ch" style="display:inline-block">${c}</span>`).join("");
  // Dika dan Sina masuk, lalu tos
  tl.fromTo(".dika-wrap", { x: -500 }, { x: 0, duration: 0.8, ease: "power3.out" }, 0.4);
  tl.fromTo(".sina-wrap", { y: 400, scale: 0.4 }, { y: 0, scale: 1, duration: 0.7, ease: "back.out(1.8)" }, 0.6);
  bob(".dika-rig", 1.3, END - 1, 4, 2.2);
  bob(".sina-rig", 1.4, END - 1, 9, 1.3);
  blink(".dika-lid", [1.8, 4.6, 7.4]);
  blink(".sina-lid", [3.2, 6.0, 8.6]);
  tl.fromTo(".dika-arm-r", { rotation: 0, svgOrigin: "212 272" }, { rotation: -150, duration: 0.5, ease: "back.out(1.6)" }, 1.7);
  tl.fromTo(".sina-arm-l", { rotation: 0, svgOrigin: "-62 6" }, { rotation: 95, duration: 0.45, ease: "back.out(1.6)" }, 1.75);
  tl.fromTo(".sina-rig", { rotation: 0, svgOrigin: "0 110" }, { rotation: -12, duration: 0.4, immediateRender: false }, 1.75);
  tl.fromTo(".spark", { scale: 0, rotation: -30, opacity: 0, transformOrigin: "50% 50%" }, { scale: 1.2, rotation: 0, opacity: 1, duration: 0.35, ease: "back.out(3)" }, 2.2);
  tl.to(".spark", { scale: 1.5, opacity: 0, duration: 0.6 }, 2.6);
  confetti(580, 600, 2.25, { n: 70, d: 2.6 });
  burst(580, 600, 2.22, { r0: 50, r1: 200, n: 14, shake: 0 });
  tl.fromTo(".dika-head", { rotation: 0, svgOrigin: "160 240" }, { rotation: 6, duration: 0.4 }, 2.0);
  // lockup
  pop(".lock .logo", w("SINAPS") - 0.2, { from: 0.3, ease: "back.out(2)" });
  tl.fromTo(".word .ch", { y: 90, opacity: 0 }, { y: 0, opacity: 1, duration: 0.5, ease: "back.out(1.7)", stagger: 0.05 }, w("SINAPS"));
  burst(1130, 290, w("SINAPS") + 0.1, { r0: 80, r1: 230, n: 14, ring: "#195764" });
  words(".line", w("Latihan") - 0.1, { stagger: 0.05 });
  mark(".line b", w("kapan"), { color: "rgba(25,87,100,.18)" });
  tl.fromTo(".line b", { color: "#334155" }, { color: "#195764", duration: 0.3 }, w("kapan"));
  rise(".team", w("umpan"), { y: 14 });
  pop(".url", w("dipercaya"), { from: 0.6, ease: "back.out(2.6)" });
  tl.to(".url", { scale: 1.06, duration: 0.35, yoyo: true, repeat: 3, ease: "sine.inOut" }, w("dipercaya") + 0.6);
  rise(".disc", w("dipercaya") + 0.6, { y: 8 });
  // penutup film: pudar ke putih
  tl.to(S, { opacity: 0, duration: 0.9, ease: "power1.in" }, END - 0.9);
  window.__timelines[ID] = tl;
})();
</script>
</template></body></html>

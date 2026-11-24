<!doctype html>
<html><head><meta charset="UTF-8" /></head><body><template>
<style>
<!-- @base -->
#f09 { position: absolute; inset: 0; background: transparent; overflow: hidden; }
#f09 .mark { position: absolute; left: 280px; top: 260px; }
#f09 .word { position: absolute; left: 860px; top: 330px; font-family: 'Oswald', sans-serif; font-weight: 600; font-size: 220px; line-height: 1; letter-spacing: .16em; text-transform: uppercase; color: var(--ink); }
#f09 .tag { position: absolute; left: 868px; top: 575px; width: 700px; font-size: 40px; line-height: 1.28; font-weight: 700; color: var(--ink-2); }
#f09 .tag b { color: var(--teal); font-size: 1.12em; }
#f09 .pills .chip i { font-style: normal; display: grid; place-items: center; width: 40px; height: 40px; border-radius: 50%; background: var(--teal); color: #fff; font-size: 24px; }
#f09 .sina-wrap { position: absolute; left: 1560px; top: 640px; }
</style>
<div id="f09" data-composition-id="f09" data-width="1920" data-height="1080">
  
  <div class="mark"><!-- @include logo p=f09l w=460 --></div>
  <div class="word">Sinaps</div>
  <div class="tag"><b>S</b>istem <b>I</b>nteraktif <b>N</b>euroradiologi <b>A</b>daptif untuk <b>P</b>embelajaran <b>S</b>troke</div>
  <div class="sina-wrap"><!-- @include sina p=f09s w=300 smile=0 open=1 --></div>
</div>
<!-- @sfx reverse_suck@0.0:0.45 logo_sting@0.45:0.75 sparkle@1.35:0.45 impact_boom@~SINAPS-0.1:0.6 punch_hit@~SINAPS-0.1:0.4 snap@~tutor-0.2:0.4 slide_whistle@~berlatih-0.15:0.3 hop@~berlatih+0.6:0.5 mar2@~berlatih:0.45 mar4@~dinilai:0.45 mar6@~tidak-0.2:0.5 bubble_hi@~dibimbing+0.3:0.35 -->
<script>
(() => {
/* @helpers */
// huruf SINAPS dipecah supaya bisa muncul satu per satu
  const word = $1(".word");
  word.innerHTML = [...word.textContent].map((c) => `<span class="ch" style="display:inline-block">${c}</span>`).join("");
  enter("zoom");
  // logo terbentuk: ubin, dua ujung neuron bertemu, neurotransmiter meletup
  tl.fromTo(".mark", { scale: 2.8, opacity: 0, transformOrigin: "50% 50%" }, { scale: 1, opacity: 1, duration: 0.6, ease: "expo.out" }, 0.05);
  drawPath($1(".logo-pre"), 0.3, 0.45);
  drawPath($1(".logo-post"), 0.42, 0.45);
  tl.fromTo(".logo-k1, .logo-k2", { opacity: 0 }, { opacity: 1, duration: 0.15 }, 0.8);
  tl.fromTo(".logo-nt", { opacity: 0, scale: 0.4, transformOrigin: "50% 50%" }, { opacity: 1, scale: 1, duration: 0.35, stagger: 0.08 }, 0.9);
  // wordmark mendarat tepat saat "SINAPS" diucapkan
  const tw = w("SINAPS");
  tl.fromTo(".word .ch", { y: 70, opacity: 0 }, { y: 0, opacity: 1, duration: 0.5, ease: "expo.out", stagger: 0.035 }, tw - 0.35);
  rise(".tag", w("tutor") - 0.25, { y: 30 });
  tl.fromTo(".tag b", { color: "#334155" }, { color: "#195764", duration: 0.25, stagger: 0.12 }, w("tutor") + 0.2);
  // Sina melompat keluar dari logo
  const tj = w("berlatih") - 0.1;
  tl.fromTo(".sina-wrap", { x: -1150, y: -220, scale: 0.3, opacity: 0, rotation: -40 }, { x: 0, y: 0, scale: 1, opacity: 1, rotation: 0, duration: 0.9, ease: "back.out(1.4)" }, tj);
  bob(".sina-rig", tj + 1.0, END, 5, 2.0);
  blink(".sina-lid", [tj + 1.6, tj + 4.1, tj + 6.2]);
  tl.fromTo(".sina-arm-l", { rotation: 0, svgOrigin: "-62 6" }, { rotation: 70, duration: 0.3, ease: "back.out(2)" }, w("dibimbing"));
  tl.to(".sina-arm-l", { rotation: 40, duration: 0.25, yoyo: true, repeat: 3, ease: "sine.inOut" }, w("dibimbing") + 0.3);
  leave();
  window.__timelines[ID] = tl;
})();
</script>
</template></body></html>

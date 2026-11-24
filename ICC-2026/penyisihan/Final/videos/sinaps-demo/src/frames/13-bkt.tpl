<!doctype html>
<html><head><meta charset="UTF-8" /></head><body><template>
<style>
<!-- @base -->
#f13 { position: absolute; inset: 0; background: transparent; overflow: hidden; }
#f13 .bars { position: absolute; left: 110px; top: 250px; width: 960px; padding: 44px 50px; border-radius: 28px; background: #fff; border: 2px solid var(--line); box-shadow: 0 1px 2px rgba(16,24,40,.04), 0 14px 36px rgba(16,24,40,.07); }
#f13 .bar { display: grid; grid-template-columns: 1fr; align-items: center; gap: 22px; margin: 0 0 30px; }
#f13 .bar:last-child { margin: 0; }
#f13 .bar .nm { font-size: 40px; font-weight: 700; margin-bottom: 14px; }
#f13 .bar .tr { height: 34px; border-radius: 17px; background: #f1f5f9; overflow: hidden; position: relative; }
#f13 .bar .tr i { position: absolute; left: 0; top: 0; bottom: 0; border-radius: 11px; background: var(--ok); }
#f13 .bar .tr u { position: absolute; left: 95%; top: -4px; bottom: -4px; width: 3px; background: var(--ink); }
#f13 .bar.low .tr i { background: var(--bad); }
#f13 .dial { position: absolute; left: 1180px; top: 270px; width: 640px; height: 420px; }
#f13 .dial .lbl { position: absolute; left: 0; right: 0; top: 360px; text-align: center; font: 700 76px 'Arvo', serif; color: var(--warn); }
#f13 .sina-wrap { position: absolute; left: 1640px; top: 760px; }
</style>
<div id="f13" data-composition-id="f13" data-width="1920" data-height="1080">
  
  <div class="bars">
    <div class="bar"><div><div class="nm">Mengenali sekuens</div><div class="tr"><i style="width: 96%"></i><u></u></div></div></div>
    <div class="bar"><div><div class="nm">Hiperintensitas DWI</div><div class="tr"><i style="width: 81%"></i><u></u></div></div></div>
    <div class="bar"><div><div class="nm">Restriksi vs T2 shine-through</div><div class="tr"><i style="width: 64%"></i><u></u></div></div></div>
    <div class="bar low"><div><div class="nm">Delineasi seluruh lesi</div><div class="tr"><i style="width: 33%"></i><u></u></div></div></div>
  </div>
  <svg class="dial" viewBox="0 0 640 420">
    <path d="M70,320 A250,250 0 0 1 195,103" fill="none" stroke="#86efac" stroke-width="50" />
    <path d="M205,98 A250,250 0 0 1 435,98" fill="none" stroke="#fbbf24" stroke-width="50" />
    <path d="M445,103 A250,250 0 0 1 570,320" fill="none" stroke="#f87171" stroke-width="50" />
    <text x="40" y="160" font-family="Geist" font-size="34" font-weight="600" fill="#334155" transform="rotate(-58 40 160)">mudah</text>
    <text x="320" y="30" font-family="Geist" font-size="34" font-weight="600" fill="#334155" text-anchor="middle">sedang</text>
    <text x="576" y="130" font-family="Geist" font-size="34" font-weight="600" fill="#334155" transform="rotate(58 576 130)">sulit</text>
    <g class="needle"><path d="M320,320 L334,320 L322,100 L318,100 L306,320 Z" fill="#10313a" /><circle cx="320" cy="320" r="26" fill="#10313a" /><circle cx="320" cy="320" r="10" fill="#fff" /></g>
  </svg>
  <div class="dial" style="pointer-events:none"><div class="lbl">sedang</div></div>
  <div class="sina-wrap"><!-- @include sina p=f13s w=180 --></div>
</div>
<!-- @sfx swish_fast@0.0:0.45 mar5@~memperbarui:0.45 mar4@~memperbarui+0.18:0.45 mar3@~memperbarui+0.36:0.45 mar1@~memperbarui+0.54:0.45 error_buzz@~lemah:0.3 notif_pop@~lemah-0.2:0.45 swipe_zip@~tingkat-0.6:0.4 hop@~tingkat:0.4 slide_whistle@~kesulitan:0.3 ding@~pas-0.2:0.5 -->
<script>
(() => {
/* @helpers */
enter("push");
  tl.fromTo(".bars", { y: 40, opacity: 0 }, { y: 0, opacity: 1, duration: 0.6 }, 0.8);
  const bars = [...$(".bar")];
  const vals = [96, 81, 64, 33];
  bars.forEach((b, i) => {
    const t = w("memperbarui") + i * 0.18;
    tl.fromTo(b.querySelector(".tr i"), { scaleX: 0, transformOrigin: "0% 50%" }, { scaleX: 1, duration: 1.0, ease: "power3.out" }, t);
  });
  // KC terlemah disorot
  const tk = w("lemah");
  tl.to(bars[3], { backgroundColor: "#fef2f2", duration: 0.3 }, w("Kasus"));
  tl.fromTo(bars[3], { x: 0 }, { x: 10, duration: 0.08, yoyo: true, repeat: 1, immediateRender: false }, tk);
  // dial tingkat kesulitan
  const arcs = [...$(".dial path")];
  arcs.forEach((p, i) => drawPath(p, w("tingkat") - 0.6 + i * 0.15, 0.6));
  rise(".dial text", w("tingkat") - 0.2, { y: 8, stagger: 0.1 });
  tl.fromTo(".needle", { rotation: -82, svgOrigin: "320 320", opacity: 0 }, { rotation: -8, opacity: 1, duration: 1.4, ease: "elastic.out(1, 0.45)" }, w("kesulitan"));
  pop(".dial .lbl", w("pas") - 0.2, { from: 0.6 });
  tl.fromTo(".sina-wrap", { y: 200, opacity: 0 }, { y: 0, opacity: 1, duration: 0.6, ease: "back.out(1.8)" }, w("tingkat"));
  tl.fromTo(".sina-arm-l", { rotation: 0, svgOrigin: "-62 6" }, { rotation: 80, duration: 0.4, ease: "back.out(2)" }, w("kesulitan"));
  bob(".sina-rig", w("tingkat") + 0.7, END, 6, 1.4);
  // frame terakhir: tidak ada adegan sesudahnya, jadi tidak keluar (berakhir diam di frame ini)
  window.__timelines[ID] = tl;
})();
</script>
</template></body></html>

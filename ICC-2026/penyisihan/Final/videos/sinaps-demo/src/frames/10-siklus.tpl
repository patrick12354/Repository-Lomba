<!doctype html>
<html><head><meta charset="UTF-8" /></head><body><template>
<style>
<!-- @base -->
#f10 { position: absolute; inset: 0; background: transparent; overflow: hidden; }
#f10 .ringsvg { position: absolute; left: 0; top: 0; width: 1920px; height: 1080px; }
#f10 .center { position: absolute; left: 730px; top: 600px; width: 460px; text-align: center; }
#f10 .center .t { font: 700 60px/1 'Arvo', serif; }
#f10 .st { position: absolute; width: 300px; margin-left: -150px; text-align: center; }
#f10 .st .disc { width: 150px; height: 150px; margin: 0 auto; border-radius: 50%; background: #fff; border: 2px solid var(--line); box-shadow: 0 10px 26px rgba(16,24,40,.08); display: grid; place-items: center; position: relative; }
#f10 .st.on .disc { background: var(--teal-soft); border-color: var(--teal); }
#f10 .st .lb { display: inline-block; margin-top: 12px; padding: 4px 14px; border-radius: 14px; background: rgba(255,255,255,.95); font-size: 40px; line-height: 1.15; font-weight: 700; }
#f10 .st.r .lb { position: absolute; left: 236px; top: 30px; width: max-content; margin: 0; text-align: left; }
#f10 .st.l .lb { position: absolute; right: 236px; top: 30px; width: max-content; margin: 0; text-align: right; }
#f10 .sina-wrap { position: absolute; left: 870px; top: 385px; }
</style>
<div id="f10" data-composition-id="f10" data-width="1920" data-height="1080">
  
  <svg class="ringsvg" viewBox="0 0 1920 1080">
    <circle cx="960" cy="560" r="340" fill="none" stroke="#eef2f5" stroke-width="16" />
    <circle class="ring-prog" cx="960" cy="560" r="340" fill="none" stroke="#195764" stroke-width="16" stroke-linecap="round" stroke-dasharray="2136" stroke-dashoffset="1580" transform="rotate(-90 960 560)" />
  </svg>
  <div class="center"><div class="t">Satu siklus</div></div>
  <!-- stasiun pada sudut -90, -18, 54, 126, 198 derajat, r = 340 -->
  <div class="st" style="left: 960px; top: 145px"><div class="disc"><svg width="76" height="76" viewBox="0 0 76 76"><circle cx="38" cy="38" r="30" fill="none" stroke="#10313a" stroke-width="6" /><circle cx="38" cy="38" r="16" fill="none" stroke="#10313a" stroke-width="6" /><circle cx="38" cy="38" r="5" fill="#10313a" /></svg></div><div class="lb">Pilih kasus</div></div>
  <div class="st r" style="left: 1283px; top: 380px"><div class="disc"><svg width="76" height="76" viewBox="0 0 76 76"><path d="M14,62 C10,50 22,44 30,50 C36,56 30,66 14,62 Z" fill="#10313a" /><path d="M32,46 L62,12" stroke="#10313a" stroke-width="8" stroke-linecap="round" /></svg></div><div class="lb">Baca &amp; tandai</div></div>
  <div class="st" style="left: 1160px; top: 755px"><div class="disc"><svg width="76" height="76" viewBox="0 0 76 76"><path d="M10,50 A28,28 0 0 1 66,50" fill="none" stroke="#10313a" stroke-width="7" stroke-linecap="round" /><path d="M38,50 L56,30" stroke="#f09a6c" stroke-width="7" stroke-linecap="round" /><circle cx="38" cy="50" r="6" fill="#10313a" /></svg></div><div class="lb">Dinilai otomatis</div></div>
  <div class="st" style="left: 760px; top: 755px"><div class="disc"><svg width="76" height="76" viewBox="0 0 76 76"><path d="M10,14 h56 a6,6 0 0 1 6,6 v30 a6,6 0 0 1 -6,6 h-30 l-14,12 v-12 h-12 a6,6 0 0 1 -6,-6 v-30 a6,6 0 0 1 6,-6 z" fill="none" stroke="#10313a" stroke-width="6" stroke-linejoin="round" /><circle cx="26" cy="35" r="4" fill="#10313a" /><circle cx="38" cy="35" r="4" fill="#10313a" /><circle cx="50" cy="35" r="4" fill="#10313a" /></svg></div><div class="lb">Tutor menjelaskan</div></div>
  <div class="st l" style="left: 637px; top: 380px"><div class="disc"><svg width="76" height="76" viewBox="0 0 76 76"><rect x="10" y="40" width="12" height="24" rx="3" fill="#10313a" /><rect x="32" y="26" width="12" height="38" rx="3" fill="#10313a" /><rect x="54" y="12" width="12" height="52" rx="3" fill="#f09a6c" /></svg></div><div class="lb">Penguasaan naik</div></div>
  <div class="sina-wrap"><!-- @include sina p=f10s w=180 --></div>
</div>
<!-- @sfx ui_swell@0.0:0.45 hop@~Sina-0.3:0.5 bubble_hi@~Sina+0.3:0.35 woosh_up@~siklus-0.4:0.35 mar1@~Sistem:0.5 mar2@~Kamu:0.5 mar3@~Jawabanmu:0.5 mar4@~tutor:0.5 mar5@~penguasaanmu:0.5 success_arp@~diperbarui+0.2:0.5 -->
<script>
(() => {
/* @helpers */
enter("push");
  const C = [960, 560], RAD = 340;
  const ang = [-90, -18, 54, 126, 198];
  const sts = [...$(".st")];
  // 2. siklus: cincin dan lima stasiun muncul bersama, Sina mengecil ke pusatnya
  const tc = w("SINAPS") - 0.2;
  tl.fromTo(".ringsvg circle:first-child", { scale: 0.85, opacity: 0, svgOrigin: "960 560" }, { scale: 1, opacity: 1, duration: 0.6 }, tc);
  sts.forEach((el, i) => pop(el.querySelector(".disc"), tc + 0.1 + i * 0.05));
  rise(".st .lb", tc + 0.2, { y: 12, stagger: 0.04 });
  rise(".center", tc + 0.3, { y: 16 });
  // Sina menyapa
  // 1. kenalan dengan Sina: sendirian, besar, di tengah
  tl.fromTo(".sina-wrap", { y: 160, scale: 1.2, opacity: 0 }, { y: 60, scale: 2, opacity: 1, duration: 0.6 }, 0.55);
  tl.to(".sina-wrap", { y: 0, scale: 1, duration: 0.6, ease: "power4.inOut" }, tc - 0.1);
  tl.fromTo(".sina-arm-l", { rotation: 0, svgOrigin: "-62 6" }, { rotation: 70, duration: 0.3 }, w("Sina"));
  tl.to(".sina-arm-l", { rotation: 40, duration: 0.25, yoyo: true, repeat: 3, ease: "sine.inOut" }, w("Sina") + 0.3);
  tl.to(".sina-arm-l", { rotation: 0, duration: 0.3 }, w("Sina") + 1.2);
  bob(".sina-rig", w("Sina") + 0.6, END, 4, 2.2);
  blink(".sina-lid", [3.4, 7.8, 11.6, 15.9]);
  // sinyal (butir neurotransmiter) berjalan di cincin, tiap stasiun menyala saat dilewati
  const ns = "http://www.w3.org/2000/svg";
  const sig = document.createElementNS(ns, "circle");
  sig.setAttribute("r", "17"); sig.setAttribute("fill", "#e07a1f"); sig.setAttribute("stroke", "#fff"); sig.setAttribute("stroke-width", "5");
  $1(".ringsvg").appendChild(sig);
  const times = [w("Sistem"), w("Kamu"), w("Jawabanmu"), w("tutor"), w("penguasaanmu")];
  const a = { v: -90 };
  const put = () => {
    const r = (a.v * Math.PI) / 180;
    sig.setAttribute("cx", (C[0] + RAD * Math.cos(r)).toFixed(1));
    sig.setAttribute("cy", (C[1] + RAD * Math.sin(r)).toFixed(1));
    $1(".ring-prog").setAttribute("stroke-dashoffset", (2136 * (1 - (a.v + 90) / 360)).toFixed(1));
    // Sina menoleh ke arah sinyal
    gsap.set(R.querySelector(".sina-face"), { x: 6 * Math.cos(r), y: 4 * Math.sin(r) });
  };
  // ekor komet mengikuti sinyal
  const trail = [1, 2, 3, 4, 5, 6].map((k) => svgEl("circle", { r: (15 - k * 2).toFixed(0), fill: "#e07a1f", opacity: (0.5 - k * 0.07).toFixed(2), cx: 960, cy: 220 }, $1(".ringsvg")));
  $1(".ringsvg").appendChild(sig);
  const put0 = put;
  const putT = () => { put0(); trail.forEach((c, k) => { const r = ((a.v - (k + 1) * 5) * Math.PI) / 180; c.setAttribute("cx", (C[0] + RAD * Math.cos(r)).toFixed(1)); c.setAttribute("cy", (C[1] + RAD * Math.sin(r)).toFixed(1)); }); };
  tl.fromTo(trail, { opacity: 0 }, { opacity: (i) => 0.5 - (i + 1) * 0.07, duration: 0.3 }, times[0] - 0.4);
  tl.fromTo(sig, { opacity: 0 }, { opacity: 1, duration: 0.3 }, times[0] - 0.4);
  tl.fromTo(a, { v: -90 }, { v: -90, duration: 0.01, onUpdate: put, onStart: put }, 0);
  times.forEach((t, i) => {
    if (i > 0) { const d = Math.min(0.9, t - times[i - 1] - 0.05); tl.to(a, { v: ang[i], duration: d, ease: "power2.inOut", onUpdate: putT }, t - d); }
    const ra = (ang[i] * Math.PI) / 180;
    burst(C[0] + RAD * Math.cos(ra), C[1] + RAD * Math.sin(ra), t, { r0: 80, r1: 170, n: 10 });
    const d = sts[i].querySelector(".disc");
    tl.to(d, { backgroundColor: "#e8f1f2", borderColor: "#195764", duration: 0.25 }, t);
    tl.fromTo(d, { scale: 1 }, { scale: 1.08, duration: 0.15, yoyo: true, repeat: 1, ease: "power2.out", immediateRender: false }, t);
    tl.to(sts[i].querySelector(".lb"), { color: "#195764", duration: 0.25 }, t);
  });
  tl.to(a, { v: 270, duration: 0.9, ease: "power2.inOut", onUpdate: putT }, times[4] + 0.3);
  tl.to(".center .t", { color: "#195764", duration: 0.3 }, times[4] + 1.1);
  tl.fromTo(".ring-prog", { attr: { "stroke-width": 16 } }, { attr: { "stroke-width": 28 }, duration: 0.2, yoyo: true, repeat: 1, immediateRender: false }, times[4] + 1.2);
  leave();
  window.__timelines[ID] = tl;
})();
</script>
</template></body></html>

<!doctype html>
<html><head><meta charset="UTF-8" /></head><body><template>
<style>
<!-- @base -->
#f02 { position: absolute; inset: 0; background: transparent; overflow: hidden; }
#f02 .ecg { position: absolute; left: 0; top: 0; width: 1920px; height: 1080px; }
#f02 .cd { position: absolute; top: 230px; width: 780px; height: 720px; border-radius: 32px; border: 4px solid transparent; }
#f02 .cA { left: 120px; } #f02 .cB { left: 1020px; }
#f02 .cB .hd { text-align: right; }
#f02 .cd .hd { position: absolute; left: 44px; right: 44px; top: 30px; font: 700 60px 'Arvo', serif; color: var(--ink); }
#f02 .cd .brain { position: absolute; left: 50px; top: 100px; width: 680px; height: 541px; }
#f02 .cd .sy { position: absolute; left: 40px; right: 40px; bottom: 34px; display: flex; gap: 14px; justify-content: center; }
#f02 .cd .sy span { font: 600 34px 'Geist', sans-serif; color: var(--ink-2); }
#f02 .cd .sy span + span::before { content: "·"; margin-right: 14px; color: var(--muted); }
#f02 .cd .res { position: absolute; left: 50%; bottom: 24px; display: flex; align-items: center; gap: 14px; padding: 16px 30px 16px 18px; border-radius: 999px; color: #fff; font: 700 44px 'Geist', sans-serif; box-shadow: 0 14px 30px rgba(16,24,40,.22); white-space: nowrap; }
#f02 .cA .res { background: var(--ok); } #f02 .cB .res { background: var(--bad); }
#f02 .cd .res i { width: 62px; height: 62px; border-radius: 50%; background: #fff; display: grid; place-items: center; font-style: normal; }
#f02 .eq { position: absolute; left: 900px; top: 530px; width: 120px; height: 120px; border-radius: 50%; background: var(--ink); color: #fff; display: grid; place-items: center; font: 700 86px/1 'Oswald', sans-serif; box-shadow: 0 10px 30px rgba(16,24,40,.25); }
#f02 .drug { position: absolute; left: 560px; top: 92px; width: 800px; display: flex; align-items: center; justify-content: center; gap: 22px; font: 700 50px 'Arvo', serif; color: var(--ink); }
#f02 .arrows { position: absolute; left: 0; top: 0; width: 1920px; height: 1080px; pointer-events: none; }
/* ruang baca */
#f02 .read { position: absolute; inset: 0; background: #0b1220; opacity: 0; }
#f02 .read .img { position: absolute; left: 230px; top: 150px; width: 700px; height: 700px; border-radius: 26px; overflow: hidden; border: 3px solid #1e293b; background: #000; }
#f02 .read .img img { width: 100%; height: 100%; display: block; }
#f02 .read .beam { position: absolute; left: 0; right: 0; top: 0; height: 10px; background: #f09a6c; box-shadow: 0 0 40px 14px rgba(240,154,108,.55); }
#f02 .read .cover { position: absolute; inset: 0; background: #000; }
#f02 .read .step { position: absolute; left: 1040px; width: 800px; display: flex; align-items: center; gap: 26px; color: #fff; font: 700 76px/1.1 'Arvo', serif; }
#f02 .read .step em { font-style: normal; }
#f02 .read .step .ok { display: inline-grid; place-items: center; width: 64px; height: 64px; border-radius: 50%; background: var(--ok); margin-left: 6px; }
#f02 .read .step .qm { display: inline-grid; place-items: center; width: 70px; height: 70px; border-radius: 50%; background: #fbbf24; color: #0b1220; font: 700 52px/1 'Oswald', sans-serif; margin-left: 6px; }
</style>
<div id="f02" data-composition-id="f02" data-width="1920" data-height="1080">
  <svg class="ecg" viewBox="0 0 1920 1080"><path class="ecg-l" d="M-20,540 H690 L730,540 L752,488 L780,612 L818,330 L858,700 L884,520 L906,540 H1180 L1206,540 L1222,508 L1244,580 L1266,540 H1940" fill="none" stroke="#dc2626" stroke-width="9" stroke-linecap="round" stroke-linejoin="round" /></svg>
  <div class="drug"><svg width="70" height="70" viewBox="0 0 70 70"><g transform="rotate(-40 35 35)"><rect x="8" y="27" width="40" height="16" rx="4" fill="#fff" stroke="#10313a" stroke-width="4" /><rect x="12" y="30" width="20" height="10" fill="#e07a1f" /><rect x="48" y="31" width="10" height="8" fill="#10313a" /><line x1="58" y1="35" x2="68" y2="35" stroke="#10313a" stroke-width="3" /><rect x="2" y="25" width="6" height="20" rx="2" fill="#10313a" /></g></svg>Obat penghancur bekuan</div>
  <div class="cd cA">
    <div class="hd">Tersumbat</div>
    <svg class="brain" viewBox="0 0 1080 860">
      <path class="ol" d="M180,430 C150,300 230,170 380,130 C470,80 600,80 700,120 C820,150 920,240 940,360 C960,470 900,560 800,590 C760,600 720,600 690,610 C660,650 640,700 610,760 C590,800 560,800 560,760 C560,720 570,680 560,650 C500,640 420,640 330,620 C230,600 190,520 180,430 Z" fill="#f8ece9" stroke="#cbd5e1" stroke-width="6" />
      <g fill="none" stroke="#e9d3cf" stroke-width="6" stroke-linecap="round"><path d="M290,260 C340,220 400,250 450,215" /><path d="M560,170 C600,210 660,190 700,220" /><path d="M260,420 C320,380 360,430 420,400" /><path d="M760,300 C800,340 850,320 880,360" /><path d="M330,540 C380,500 440,540 500,510" /></g>
      <path class="isc" d="M620,330 C720,300 860,360 860,460 C860,540 760,570 680,540 C610,515 560,420 620,330 Z" fill="#2563eb" opacity="0" />
      <path class="vs" d="M280,330 C400,350 470,380 560,420 C650,460 760,470 880,440" fill="none" stroke="#d9534f" stroke-width="16" stroke-linecap="round" />
      <path class="vs2" d="M560,420 C590,340 660,280 770,250" fill="none" stroke="#d9534f" stroke-width="11" stroke-linecap="round" />
      <path class="vs3" d="M640,455 C660,520 700,560 760,580" fill="none" stroke="#d9534f" stroke-width="9" stroke-linecap="round" />
      <circle class="clot" cx="505" cy="396" r="30" fill="#5b1414" stroke="#fff" stroke-width="5" />
    </svg>
    <div class="sy"><span>bicara pelo</span><span>wajah turun</span><span>tubuh lemah</span></div>
    <div class="res"><i><svg width="40" height="40" viewBox="0 0 40 40"><path d="M8,21 l8,8 l16,-18" fill="none" stroke="#16a34a" stroke-width="6" stroke-linecap="round" stroke-linejoin="round" /></svg></i>menyelamatkan</div>
  </div>
  <div class="cd cB">
    <div class="hd">Pecah</div>
    <svg class="brain" viewBox="0 0 1080 860">
      <defs><radialGradient id="f02-bl"><stop offset="0" stop-color="#b91c1c" /><stop offset=".7" stop-color="#dc2626" stop-opacity=".85" /><stop offset="1" stop-color="#dc2626" stop-opacity="0" /></radialGradient></defs>
      <path class="ol" d="M180,430 C150,300 230,170 380,130 C470,80 600,80 700,120 C820,150 920,240 940,360 C960,470 900,560 800,590 C760,600 720,600 690,610 C660,650 640,700 610,760 C590,800 560,800 560,760 C560,720 570,680 560,650 C500,640 420,640 330,620 C230,600 190,520 180,430 Z" fill="#f8ece9" stroke="#cbd5e1" stroke-width="6" />
      <g fill="none" stroke="#e9d3cf" stroke-width="6" stroke-linecap="round"><path d="M290,260 C340,220 400,250 450,215" /><path d="M560,170 C600,210 660,190 700,220" /><path d="M260,420 C320,380 360,430 420,400" /><path d="M760,300 C800,340 850,320 880,360" /><path d="M330,540 C380,500 440,540 500,510" /></g>
      <path class="vs" d="M280,330 C400,350 470,380 560,420 C650,460 760,470 880,440" fill="none" stroke="#d9534f" stroke-width="16" stroke-linecap="round" />
      <path class="vs2" d="M560,420 C590,340 660,280 770,250" fill="none" stroke="#d9534f" stroke-width="11" stroke-linecap="round" />
      <path class="vs3" d="M640,455 C660,520 700,560 760,580" fill="none" stroke="#d9534f" stroke-width="9" stroke-linecap="round" />
      <circle class="bleed" cx="610" cy="370" r="120" fill="url(#f02-bl)" />
      <path class="rip" d="M590,392 l14,-18 l10,14 l14,-20" fill="none" stroke="#fff" stroke-width="6" stroke-linecap="round" stroke-linejoin="round" />
    </svg>
    <div class="sy"><span>bicara pelo</span><span>wajah turun</span><span>tubuh lemah</span></div>
    <div class="res"><i><svg width="40" height="40" viewBox="0 0 40 40"><path d="M11,11 l18,18 M29,11 l-18,18" fill="none" stroke="#dc2626" stroke-width="6" stroke-linecap="round" /></svg></i>memperparah</div>
  </div>
  <div class="eq">=</div>
  <svg class="arrows" viewBox="0 0 1920 1080">
    <defs><marker id="f02-ah" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#10313a" /></marker></defs>
    <path class="arA" d="M820,190 C700,230 620,280 560,380" fill="none" stroke="#10313a" stroke-width="8" stroke-linecap="round" marker-end="url(#f02-ah)" />
    <path class="arB" d="M1100,190 C1220,230 1300,280 1400,380" fill="none" stroke="#10313a" stroke-width="8" stroke-linecap="round" marker-end="url(#f02-ah)" />
  </svg>
  <div class="read" data-layout-allow-overlap>
    <div class="img"><img src="../../assets/mri/sub-654/dwi_z15.png" alt="" /><div class="cover"></div><div class="beam"></div></div>
    <div class="step s1" style="top: 340px"><span>Otaknya <em>dipindai</em><span class="ok"><svg width="36" height="36" viewBox="0 0 40 40"><path d="M8,21 l8,8 l16,-18" fill="none" stroke="#fff" stroke-width="6" stroke-linecap="round" stroke-linejoin="round" /></svg></span></span></div>
    <div class="step s2" style="top: 560px"><span>Lalu <em>dibaca</em> dengan benar<span class="qm">?</span></span></div>
  </div>
</div>
<!-- @sfx whoosh@0.0:0.45 pop@~tersumbat-0.1:0.4 glass_tap@~pecah-0.1:0.45 crowd_murmur@~gejalanya:0.2 ding@~sama:0.4 tension_hit@~berlawanan-0.1:0.45 liquid_drip@~penghancur:0.5 swish_fast@~menyelamatkan-0.3:0.4 success_arp@~menyelamatkan+0.1:0.4 swish_fast@~memperparah-0.3:0.4 error_buzz@~memperparah+0.1:0.4 impact_boom@~berdarah:0.45 heartbeat@~berdarah+0.2:0.4 whoosh_deep@~Karena.2-0.3:0.45 scan_beam@~otaknya:0.45 ding@~dipindai+0.2:0.4 question_pop@~membacanya+0.2:0.45 riser@~dengan-0.6:0.35 -->
<script>
(() => {
/* @helpers */
  enter("push");
  // "menyangkut nyawa": satu detak jantung digambar melintang layar
  drawPath($1(".ecg-l"), 0.5, 0.9, { ease: "power2.out" });
  tl.to(".ecg", { opacity: 0, y: -60, duration: 0.35, ease: "power2.in" }, w("Stroke") - 0.45);
  const cA = $1(".cA"), cB = $1(".cB");
  // dua otak, satu per penyebab
  tl.fromTo(cA, { y: 160, opacity: 0 }, { y: 0, opacity: 1, duration: 0.6, ease: "back.out(1.4)" }, w("tersumbat") - 0.5);
  tl.fromTo(cB, { y: 160, opacity: 0 }, { y: 0, opacity: 1, duration: 0.6, ease: "back.out(1.4)" }, w("pecah") - 0.5);
  [cA, cB].forEach((c, i) => {
    const t = i ? w("pecah") - 0.3 : w("tersumbat") - 0.3;
    rise(c.querySelector(".hd"), t, { y: 18 });
    drawPath(c.querySelector(".vs"), t, 0.7);
    drawPath(c.querySelector(".vs2"), t + 0.3, 0.5);
    drawPath(c.querySelector(".vs3"), t + 0.4, 0.5);
  });
  // tersumbat: bekuan menutup aliran, jaringan di hilirnya kekurangan darah
  pop(".cA .clot", w("tersumbat") + 0.1, { from: 0, ease: "back.out(3)" });
  tl.fromTo(".cA .isc", { opacity: 0 }, { opacity: 0.24, duration: 0.8 }, w("tersumbat") + 0.4);
  tl.to(".cA .vs3, .cA .vs", { stroke: "#94a3b8", duration: 0.6 }, w("tersumbat") + 0.4);
  // pecah: darah merembes keluar
  tl.fromTo(".cB .bleed", { scale: 0, transformOrigin: "610px 370px" }, { scale: 0.75, duration: 0.7, ease: "power2.out" }, w("pecah"));
  pop(".cB .rip", w("pecah"), { from: 0 });
  // dari luar: gejalanya sama
  const tg = w("gejalanya");
  [cA, cB].forEach((c) => pop(c.querySelectorAll(".sy span"), tg - 0.1, { stagger: 0.08 }));
  pop(".eq", w("sama") - 0.1, { from: 0, ease: "back.out(3)" });
  tl.fromTo(".eq", { rotation: -90 }, { rotation: 0, duration: 0.5, ease: "back.out(2)" }, w("sama") - 0.1);
  // obatnya berlawanan
  const to = w("berlawanan");
  tl.to(".eq", { scale: 0, duration: 0.3, ease: "back.in(2)" }, to);
  tl.fromTo(".drug", { y: -120, opacity: 0 }, { y: 0, opacity: 1, duration: 0.5, ease: "back.out(1.8)" }, w("penghancur") - 0.5);
  // kiri: menyelamatkan
  const ts = w("menyelamatkan");
  tl.fromTo(".arA", { opacity: 0 }, { opacity: 1, duration: 0.01 }, ts - 0.4);
  drawPath($1(".arA"), ts - 0.4, 0.45);
  tl.to(".cA .clot", { scale: 0, duration: 0.6, ease: "back.in(2)", transformOrigin: "505px 396px" }, ts);
  tl.to(".cA .isc", { opacity: 0, duration: 0.8 }, ts + 0.2);
  tl.to(".cA .vs3, .cA .vs", { stroke: "#d9534f", duration: 0.6 }, ts + 0.2);
  tl.to(cA, { borderColor: "#16a34a", backgroundColor: "rgba(22,163,74,.05)", duration: 0.4 }, ts + 0.2);
  tl.to(".cA .sy", { opacity: 0, y: 20, duration: 0.2 }, ts);
  tl.fromTo(".cA .res", { xPercent: -50, scale: 0, rotation: -12, transformOrigin: "50% 50%" }, { xPercent: -50, scale: 1, rotation: 0, duration: 0.45, ease: "back.out(2.4)" }, ts + 0.2);
  // kanan: memperparah
  const tm = w("memperparah");
  tl.fromTo(".arB", { opacity: 0 }, { opacity: 1, duration: 0.01 }, tm - 0.4);
  drawPath($1(".arB"), tm - 0.4, 0.45);
  tl.to(".cB .bleed", { scale: 1.55, duration: 1.2, ease: "power2.out" }, tm);
  tl.to(cB, { borderColor: "#dc2626", backgroundColor: "rgba(220,38,38,.05)", duration: 0.4 }, tm + 0.2);
  tl.to(".cB .sy", { opacity: 0, y: 20, duration: 0.2 }, tm);
  tl.fromTo(".cB .res", { xPercent: -50, scale: 0, rotation: 12, transformOrigin: "50% 50%" }, { xPercent: -50, scale: 1, rotation: 0, duration: 0.45, ease: "back.out(2.4)" }, tm + 0.2);
  // karena itu: harus dipindai, lalu dibaca
  const tr = w("Karena", 2) - 0.2;
  tl.to([cA, cB, ".drug", ".arrows"], { scale: 0.9, opacity: 0, duration: 0.45, ease: "power2.in", stagger: 0.05 }, tr);
  tl.fromTo(".read", { opacity: 0 }, { opacity: 1, duration: 0.5 }, tr + 0.3);
  tl.fromTo(".read .img", { scale: 0.85, opacity: 0 }, { scale: 1, opacity: 1, duration: 0.6, ease: "back.out(1.5)" }, tr + 0.5);
  const tsc = w("otaknya") - 0.2;
  tl.fromTo(".read .cover", { scaleY: 1, transformOrigin: "50% 100%" }, { scaleY: 0, duration: 1.4, ease: "power1.inOut" }, tsc);
  tl.fromTo(".read .beam", { y: 0 }, { y: 690, duration: 1.4, ease: "power1.inOut" }, tsc);
  tl.to(".read .beam", { opacity: 0, duration: 0.2 }, tsc + 1.4);
  slideIn(".read .s1", w("otaknya") - 0.1, { x: 80 });
  pop(".read .s1 .ok", w("dipindai") + 0.2, { from: 0, ease: "back.out(3)" });
  slideIn(".read .s2", w("seseorang") - 0.2, { x: 80 });
  pop(".read .s2 .qm", w("membacanya") + 0.2, { from: 0, ease: "back.out(3)" });
  leave();
  window.__timelines[ID] = tl;
})();
</script>
</template></body></html>

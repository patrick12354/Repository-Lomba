<!doctype html>
<html><head><meta charset="UTF-8" /></head><body><template>
<style>
<!-- @base -->
#f01 { position: absolute; inset: 0; background: transparent; overflow: hidden; }
#f01 .world { position: absolute; left: 0; top: 0; width: 1920px; height: 1080px; }
#f01 .wall { position: absolute; inset: 0; background: linear-gradient(#1a2b35, #24404c 70%, #2b4a57); }
#f01 .floor { position: absolute; left: 0; top: 860px; width: 1920px; height: 220px; background: #182630; }
#f01 .win { position: absolute; left: 110px; top: 90px; width: 380px; height: 300px; border-radius: 12px; border: 12px solid #34525e; background: linear-gradient(#0b1726, #16304a); overflow: hidden; }
#f01 .win::after { content: ""; position: absolute; left: 50%; top: 0; bottom: 0; width: 10px; margin-left: -5px; background: #34525e; }
#f01 .moon { position: absolute; left: 230px; top: 50px; width: 80px; height: 80px; border-radius: 50%; background: #f8f1d8; box-shadow: 0 0 40px 10px rgba(248,241,216,.35); }
#f01 .star { position: absolute; width: 5px; height: 5px; border-radius: 50%; background: #e2e8f0; }
#f01 .glow { position: absolute; left: 40px; top: 360px; width: 900px; height: 700px; background: radial-gradient(ellipse at 40% 45%, rgba(253,224,150,.55), rgba(253,224,150,0) 65%); }
#f01 .dk { position: absolute; left: 380px; top: 300px; }
#f01 .dk .dika-badge, #f01 .dk .dika-torso rect { display: none; }
#f01 .desk { position: absolute; left: 150px; top: 760px; width: 900px; height: 320px; background: #6b4f3a; border-radius: 10px 10px 0 0; }
#f01 .desk::before { content: ""; position: absolute; left: -16px; right: -16px; top: -22px; height: 26px; border-radius: 8px; background: #8a6a4d; }
#f01 .lamp { position: absolute; left: 190px; top: 520px; width: 200px; height: 240px; }
#f01 .lap { position: absolute; left: 640px; top: 600px; width: 300px; height: 170px; }
#f01 .books { position: absolute; left: 960px; top: 650px; width: 70px; height: 110px; }
#f01 .books i { position: absolute; left: 0; width: 70px; height: 22px; border-radius: 4px; }
#f01 .dark { position: absolute; inset: 0; background: #050b10; opacity: 0; pointer-events: none; }
#f01 .vig { position: absolute; inset: 0; background: radial-gradient(ellipse at 30% 50%, rgba(220,38,38,0) 40%, rgba(220,38,38,.38)); opacity: 0; pointer-events: none; }
#f01 .cd { position: absolute; left: 1080px; top: 170px; width: 760px; height: 720px; border-radius: 32px; background: #fff; box-shadow: 0 30px 80px rgba(0,0,0,.45); overflow: hidden; opacity: 0; }
#f01 .c1 .bind { position: absolute; left: 0; right: 0; top: 0; height: 120px; background: var(--bad); }
#f01 .c1 .ring { position: absolute; top: 18px; width: 30px; height: 64px; border-radius: 15px; background: #2b3640; border: 5px solid #5b6b78; }
#f01 .c1 .big { position: absolute; left: 0; right: 0; top: 150px; text-align: center; font: 700 380px/1 'Oswald', sans-serif; color: var(--ink); }
#f01 .c1 .sub { position: absolute; left: 0; right: 0; top: 540px; text-align: center; font: 700 64px 'Arvo', serif; color: var(--ink-2); }
#f01 .note { position: absolute; left: 960px; top: 560px; width: 330px; height: 300px; padding: 26px 28px; background: #fde68a; box-shadow: 0 18px 30px rgba(0,0,0,.35); transform: rotate(-5deg); opacity: 0; }
#f01 .note img { display: block; width: 150px; height: 150px; border-radius: 8px; }
#f01 .note p { margin: 16px 0 0; font: 700 44px/1.05 'Arvo', serif; color: #3b2f12; }
#f01 .c2 svg { position: absolute; left: 30px; top: 170px; width: 700px; height: 380px; }
#f01 .c3 .grid { position: absolute; left: 70px; top: 203px; width: 620px; height: 314px; display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; filter: blur(7px) grayscale(1); opacity: .8; }
#f01 .c3 .grid img { width: 100%; height: 150px; object-fit: cover; border-radius: 10px; background: #000; }
#f01 .c3 .lock { position: absolute; left: 300px; top: 260px; width: 160px; height: 200px; }
#f01 .c3 .stamp { position: absolute; left: 170px; top: 330px; padding: 12px 34px; border: 8px solid var(--bad); border-radius: 16px; color: var(--bad); background: rgba(255,255,255,.9); font: 700 80px/1 'Oswald', sans-serif; letter-spacing: .1em; transform: rotate(-10deg); opacity: 0; }
#f01 .c4 .book { position: absolute; left: 60px; top: 180px; width: 640px; height: 360px; }
#f01 .c4 .pic { position: absolute; left: 140px; top: 250px; width: 170px; height: 170px; border-radius: 8px; filter: grayscale(1); }
</style>
<div id="f01" data-composition-id="f01" data-width="1920" data-height="1080" data-amb="0" data-drift="0">
  <div class="world">
    <div class="wall"></div><div class="floor"></div>
    <div class="win"><div class="moon"></div><i class="star" style="left: 40px; top: 60px"></i><i class="star" style="left: 120px; top: 150px"></i><i class="star" style="left: 300px; top: 200px"></i><i class="star" style="left: 90px; top: 230px"></i><i class="star" style="left: 330px; top: 30px"></i></div>
    <div class="glow"></div>
    <div class="dk"><!-- @include dika p=f01d w=360 coat=#4a7c86 scrub=#f1efe6 steth=0 smile=0 --></div>
    <svg class="lamp" viewBox="0 0 200 240"><path d="M40,236 h90" stroke="#2b2b2b" stroke-width="12" stroke-linecap="round" /><path d="M85,236 L60,120 L130,40" fill="none" stroke="#3a3a3a" stroke-width="10" stroke-linecap="round" stroke-linejoin="round" /><path class="shade" d="M110,20 L190,60 L150,110 Z" fill="#e07a1f" /><circle class="bulb" cx="160" cy="92" r="16" fill="#fde68a" /></svg>
    <div class="desk"></div>
    <svg class="lap" viewBox="0 0 300 170"><path d="M30,10 h240 a8,8 0 0 1 8,8 v130 h-256 v-130 a8,8 0 0 1 8,-8 z" fill="#9aa4ad" stroke="#6b7680" stroke-width="4" /><circle cx="150" cy="80" r="16" fill="#c9d1d8" /><rect x="0" y="148" width="300" height="20" rx="6" fill="#7b8590" /></svg>
    <div class="books"><i style="top: 88px; background: #195764"></i><i style="top: 64px; background: #a2462a; left: 4px"></i><i style="top: 40px; background: #aad39c; left: -3px"></i></div>
    <div class="dark"></div>
  </div>
  <div class="vig"></div>
  <div class="cd c1"><div class="bind"></div><i class="ring" style="left: 200px"></i><i class="ring" style="left: 530px"></i><div class="big">7</div><div class="sub">hari lagi</div></div>
  <div class="note"><img src="../../assets/mri/sub-654/dwi_z15.png" alt="" /><p>MRI stroke</p></div>
  <div class="cd c2">
    <svg viewBox="0 0 700 380">
      <g transform="translate(40 60)"><rect x="0" y="80" width="220" height="190" rx="8" fill="#e8f1f2" stroke="#195764" stroke-width="5" /><path d="M-10,84 L110,10 L230,84 Z" fill="#195764" /><g fill="#195764"><rect x="30" y="120" width="26" height="110" /><rect x="96" y="120" width="26" height="110" /><rect x="162" y="120" width="26" height="110" /></g><text x="110" y="320" text-anchor="middle" font-family="Geist" font-weight="700" font-size="34" fill="#10313a">Kampus</text></g>
      <g transform="translate(440 60)"><rect x="0" y="40" width="220" height="230" rx="8" fill="#fff" stroke="#94a3b8" stroke-width="5" /><circle cx="110" cy="130" r="46" fill="#fff" stroke="#dc2626" stroke-width="6" /><rect x="98" y="100" width="24" height="60" rx="4" fill="#dc2626" /><rect x="80" y="118" width="60" height="24" rx="4" fill="#dc2626" /><text x="110" y="320" text-anchor="middle" font-family="Geist" font-weight="700" font-size="34" fill="#10313a">Rumah sakit</text></g>
      <path class="link" d="M270,200 H430" stroke="#94a3b8" stroke-width="8" stroke-dasharray="14 12" />
      <g class="x"><circle cx="350" cy="200" r="46" fill="#dc2626" /><path d="M330,180 l40,40 M370,180 l-40,40" stroke="#fff" stroke-width="10" stroke-linecap="round" /></g>
    </svg></div>
  <div class="cd c3">
    <div class="grid"><img src="../../assets/mri/sub-1413/dwi_z08.png" alt="" /><img src="../../assets/mri/sub-1413/dwi_z12.png" alt="" /><img src="../../assets/mri/sub-1413/dwi_z16.png" alt="" /><img src="../../assets/mri/sub-654/dwi_z10.png" alt="" /><img src="../../assets/mri/sub-654/dwi_z15.png" alt="" /><img src="../../assets/mri/sub-654/dwi_z20.png" alt="" /></div>
    <svg class="lock" viewBox="0 0 160 200"><path class="sh" d="M40,96 V62 a40,40 0 0 1 80,0 V96" fill="none" stroke="#10313a" stroke-width="18" stroke-linecap="round" /><rect x="14" y="90" width="132" height="104" rx="18" fill="#10313a" /><circle cx="80" cy="134" r="14" fill="#fbbf24" /><rect x="74" y="140" width="12" height="30" rx="4" fill="#fbbf24" /></svg>
    <div class="stamp">RAHASIA</div></div>
  <div class="cd c4">
    <svg class="book" viewBox="0 0 640 360"><path d="M320,40 C250,10 120,10 30,30 V330 C120,310 250,310 320,340 Z" fill="#fdfaf2" stroke="#cbd5e1" stroke-width="5" /><path d="M320,40 C390,10 520,10 610,30 V330 C520,310 390,310 320,340 Z" fill="#fdfaf2" stroke="#cbd5e1" stroke-width="5" /><g stroke="#cbd5e1" stroke-width="8" stroke-linecap="round"><path d="M370,80 H560" /><path d="M370,120 H570" /><path d="M370,160 H540" /><path d="M370,200 H565" /><path d="M370,240 H520" /><path d="M370,280 H550" /></g><path d="M80,250 H270" stroke="#cbd5e1" stroke-width="8" stroke-linecap="round" /><path d="M80,285 H230" stroke="#cbd5e1" stroke-width="8" stroke-linecap="round" /></svg>
    <img class="pic" src="../../assets/mri/sub-654/dwi_z15.png" alt="" /></div>
</div>
<!-- @sfx night_room@0.0:0.4 tick@0.6:0.3 tock@1.6:0.3 pop@~Dika:0.4 notif_pop@~Minggu-0.1:0.45 clock_fast@~ujian:0.35 tension_hit@~Masalahnya-0.05:0.55 heartbeat@~Masalahnya+0.2:0.5 whoosh@~kampusnya+0.1:0.4 error_buzz@~sendiri-0.2:0.35 slide@~Data-0.2:0.4 lock_heavy@~rahasia-0.25:0.55 stamp@~rahasia:0.6 heartbeat_fast@~rahasia+0.3:0.4 book_open@~Yang-0.1:0.45 tense_drone@~beberapa:0.45 -->
<script>
(() => {
/* @helpers */
  const W = $1(".world");
  tl.set(W, { transformOrigin: "560px 500px" }, 0);
  // kamera diam; satu dorongan ke Dika saat "Masalahnya", lalu diam lagi
  const tm = w("Masalahnya") - 0.05;
  tl.to(W, { scale: 1.16, duration: 0.6, ease: "expo.out" }, tm);
  // pembuka: kamar gelap, lampu belajar menyala, Dika di mejanya
  tl.fromTo(".dark", { opacity: 0.78 }, { opacity: 0, duration: 0.5, ease: "power2.out" }, 0.25);
  tl.fromTo(".glow", { opacity: 0 }, { opacity: 1, duration: 0.5, ease: "power2.out" }, 0.25);
  tl.fromTo(".lamp .bulb", { opacity: 0.3 }, { opacity: 1, duration: 0.08, ease: "steps(2)" }, 0.22);
  bob(".dk .dika-rig", 0.4, tm, 2.5, 2.6);
  // kartu: satu demi satu di slot yang sama
  const cards = [...$(".cd")];
  const cardIn = (i, t) => tl.fromTo(cards[i], { x: 120, opacity: 0, rotation: 2 }, { x: 0, opacity: 1, rotation: 0, duration: 0.5, ease: "back.out(1.6)" }, t);
  const cardOut = (i, t) => tl.to(cards[i], { x: -60, opacity: 0, duration: 0.3, ease: "power2.in" }, t);
  cardIn(0, w("Minggu") - 0.2);
  tl.fromTo(".c1 .big", { scale: 1.5, opacity: 0 }, { scale: 1, opacity: 1, duration: 0.5, ease: "expo.out" }, w("Minggu") - 0.05);
  rise(".c1 .sub", w("Minggu") + 0.1, { y: 20 });
  // "membaca MRI stroke": catatan tempel ditepuk ke sudut kalender
  tl.fromTo(".note", { opacity: 0, y: -40, rotation: -14, scale: 1.12 }, { opacity: 1, y: 0, rotation: -5, scale: 1, duration: 0.42, ease: "expo.out" }, w("membaca") - 0.1);
  // hentakan "Masalahnya"
  cardOut(0, tm - 0.2);
  tl.to(".note", { x: -60, opacity: 0, duration: 0.3, ease: "power2.in" }, tm - 0.2);
  tl.to(".dk .dika-m-oh", { opacity: 1, duration: 0.05 }, tm);
  tl.to(".dk .dika-brows > g:nth-child(1)", { opacity: 0, duration: 0.05 }, tm);
  tl.to(".dk .dika-brows > g:nth-child(2)", { opacity: 1, duration: 0.05 }, tm);
  tl.fromTo(".dk .dika-sweat", { opacity: 0, y: -8 }, { opacity: 1, y: 0, duration: 0.5 }, tm + 0.2);
  tl.fromTo(".vig", { opacity: 0 }, { opacity: 0.3, duration: 0.4 }, tm);
  flash(tm, { color: "#ffffff", a: 0.35, d: 0.3 });
  shake(tm + 0.05, 14, 0.5);
  // kampus tanpa rumah sakit
  cardIn(1, w("kampusnya") + 0.1);
  drawPath($1(".c2 .link"), w("kampusnya") + 0.4, 0.5);
  tl.fromTo(".c2 .x", { scale: 0, transformOrigin: "350px 200px" }, { scale: 1, duration: 0.4, ease: "back.out(3)" }, w("tidak"));
  // data pasien: rahasia
  cardOut(1, w("Data") - 0.4);
  cardIn(2, w("Data") - 0.2);
  tl.fromTo(".c3 .lock", { y: -160, opacity: 0 }, { y: 0, opacity: 1, duration: 0.45, ease: "bounce.out" }, w("sifatnya") - 0.3);
  tl.fromTo(".c3 .lock .sh", { y: -18 }, { y: 0, duration: 0.15, ease: "power4.in" }, w("rahasia") - 0.25);
  tl.fromTo(".c3 .stamp", { scale: 2.4, opacity: 0, rotation: -26 }, { scale: 1, opacity: 1, rotation: -10, duration: 0.28, ease: "power4.in" }, w("rahasia") - 0.2);
  burst(1460, 520, w("rahasia") + 0.08, { color: "#dc2626", c2: "#10313a", r0: 120, r1: 300, n: 14 });
  shake(w("rahasia") + 0.08, 12);
  tl.to(".dk .dika-head", { rotation: -6, svgOrigin: "160 240", duration: 0.35, ease: "power2.inOut" }, w("rahasia") + 0.2);
  // yang ia punya: gambar seadanya; lampu meredup
  cardOut(2, w("Yang") - 0.4);
  cardIn(3, w("Yang") - 0.2);
  tl.fromTo(".c4 .pic", { scale: 0.4, opacity: 0 }, { scale: 1, opacity: 1, duration: 0.4, ease: "back.out(2)" }, w("beberapa"));
  tl.to(".dk .dika-m-oh", { opacity: 0, duration: 0.1 }, w("Yang"));
  tl.to(".dk .dika-m-worried", { opacity: 1, duration: 0.1 }, w("Yang"));
  tl.to(".dk .dika-head", { rotation: 7, svgOrigin: "160 240", duration: 0.6, ease: "power2.inOut" }, w("hanya"));
  tl.to(".glow", { opacity: 0.55, duration: 0.8 }, w("hanya"));
  tl.to(".dark", { opacity: 0.3, duration: 0.8 }, w("hanya"));
  leave();
  window.__timelines[ID] = tl;
})();
</script>
</template></body></html>

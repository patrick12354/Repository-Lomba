<!doctype html>
<html><head><meta charset="UTF-8" /></head><body><template>
<style>
<!-- @base -->
#f07 { position: absolute; inset: 0; background: transparent; overflow: hidden; }
#f07 .dika-wrap { position: absolute; left: 150px; top: 380px; }
#f07 .phone { position: absolute; left: 640px; top: 120px; width: 1180px; height: 850px; border-radius: 36px; background: #f7f7f8; border: 4px solid #d9d9de; overflow: hidden; box-shadow: 0 30px 70px rgba(16,24,40,.14); }
#f07 .phone .top { height: 92px; background: #ffffff; border-bottom: 2px solid #e6e6ea; display: flex; align-items: center; gap: 16px; padding: 0 34px; font: 700 34px 'Geist', sans-serif; color: #2a2a31; }
#f07 .phone .top .av { width: 46px; height: 46px; border-radius: 50%; background: #c9c9d1; }
#f07 .msg { position: absolute; font: 600 38px/1.38 'Geist', sans-serif; border-radius: 28px; padding: 26px 32px; }
#f07 .me { right: 40px; top: 112px; width: 560px; background: #dfe3ea; color: #2a2e36; }
#f07 .me .pic { position: relative; width: 260px; height: 260px; margin-bottom: 16px; }
#f07 .me .pic img { display: block; width: 260px; height: 260px; border-radius: 14px; }
#f07 .me .pic svg { position: absolute; left: 0; top: 0; width: 260px; height: 260px; overflow: visible; }
#f07 .bot { left: 40px; top: 600px; width: 760px; min-height: 190px; background: #ffffff; color: #22252b; border: 3px solid #e6e6ea; }
#f07 .stamp { position: absolute; left: 1230px; top: 698px; padding: 22px 38px; border: 7px solid var(--bad); border-radius: 18px; color: var(--bad); transform: rotate(-7deg); background: rgba(255,255,255,.96); text-align: center; box-shadow: 0 16px 34px rgba(220,38,38,.18); }
#f07 .stamp .a { font-family: 'Oswald', sans-serif; font-weight: 700; font-size: 52px; letter-spacing: .14em; }
#f07 .stamp .b { font-family: 'Oswald', sans-serif; font-weight: 700; font-size: 150px; line-height: .95; }
/* lembar bacaan Dika: tandanya sendiri, kotak nilai yang masih kosong */
#f07 .sheet { position: absolute; left: 820px; top: 130px; width: 900px; height: 820px; border-radius: 10px; background: #fffefb; box-shadow: 0 2px 0 #e7e2d6, 0 30px 70px rgba(16,24,40,.16); opacity: 0; }
#f07 .sheet .img { position: absolute; left: 70px; top: 80px; width: 520px; height: 520px; border-radius: 8px; overflow: hidden; background: #000; }
#f07 .sheet .img img { width: 100%; height: 100%; display: block; }
#f07 .sheet .img svg { position: absolute; inset: 0; width: 100%; height: 100%; }
#f07 .sheet .lines { position: absolute; left: 70px; top: 650px; width: 520px; }
#f07 .sheet .lines i { display: block; height: 10px; border-radius: 5px; background: #e7e2d6; margin-bottom: 26px; }
#f07 .sheet .grade { position: absolute; left: 640px; top: 90px; width: 200px; height: 200px; border-radius: 50%; border: 7px dashed #c9c2b2; display: grid; place-items: center; font: 700 130px/1 'Arvo', serif; color: #c9c2b2; }
#f07 .dim { position: absolute; inset: 0; background: #10313a; opacity: 0; }
#f07 .ask { position: absolute; left: 0; right: 0; top: 470px; text-align: center; color: #fff; font: 700 104px/1.1 'Arvo', serif; }
</style>
<div id="f07" data-composition-id="f07" data-width="1920" data-height="1080">
  <div class="dika-wrap"><!-- @include dika p=f07d w=300 smile=0 oh=1 --></div>
  <div class="phone">
    <div class="top"><span class="av"></span>Asisten AI</div>
    <div class="msg me"><div class="pic"><img src="../../assets/mri/sub-654/dwi_z15.png" alt="" /><svg viewBox="0 0 260 260"><ellipse class="truth" cx="112" cy="140" rx="40" ry="56" fill="none" stroke="#dc2626" stroke-width="7" /></svg></div>Ini MRI-nya. Ada stroke? Lesinya di mana?</div>
    <div class="msg bot" data-layout-allow-overlap>Otak tampak normal. Tidak terlihat tanda infark maupun perdarahan pada gambar ini.</div>
  </div>
  <div class="stamp" data-layout-allow-overlap><div class="a">HALUSINASI</div><div class="b">74,4%</div></div>
  <div class="sheet">
    <div class="img"><img src="../../assets/mri/sub-654/dwi_z15.png" alt="" /><svg viewBox="0 0 520 520"><path class="mine" d="M190,196 C238,176 282,214 276,282 C270,350 236,392 196,372 C160,354 150,300 160,250 C166,222 176,204 196,194" fill="none" stroke="#e07a1f" stroke-width="12" stroke-linecap="round" /></svg></div>
    <div class="lines"><i style="width: 92%"></i><i style="width: 70%"></i><i style="width: 82%"></i></div>
    <div class="grade">?</div>
  </div>
  <div class="dim"></div>
  <div class="ask">Lalu, apa jalan keluarnya?</div>
</div>
<script>
(() => {
/* @helpers */
  enter("push");
  // 1. Dika lari ke chatbot: jendela obrolan, pesannya dengan potongan MRI
  tl.fromTo(".dika-wrap", { y: 420 }, { y: 0, duration: 0.6 }, 0.55);
  bob(".dika-wrap .dika-rig", 1.2, END, 3, 2.4);
  tl.fromTo(".dika-wrap .dika-arm-r", { rotation: 0, svgOrigin: "212 272" }, { rotation: -60, duration: 0.45 }, w("lari"));
  tl.fromTo(".phone", { y: 60, opacity: 0 }, { y: 0, opacity: 1, duration: 0.6 }, 0.7);
  pop(".msg.me", w("lari") + 0.1, { origin: "100% 0%" });
  // 2. jawabannya mengalir yakin... padahal lesinya jelas terlihat
  const bot = $1(".msg.bot");
  const full = bot.textContent;
  pop(".msg.bot", w("Masalahnya") - 0.2, { origin: "0% 0%" });
  const tp = { n: 0 };
  tl.fromTo(tp, { n: 0 }, { n: full.length, duration: 1.1, ease: "none", onUpdate: () => { bot.textContent = full.slice(0, Math.round(tp.n)); } }, w("Masalahnya"));
  const tg = w("salah") + 0.25;
  drawPath($1(".truth"), tg, 0.5, { ease: "power2.out" });
  tl.to(".msg.bot", { borderColor: "#dc2626", backgroundColor: "#fff5f5", duration: 0.3 }, tg + 0.2);
  tl.to(".dika-wrap .dika-m-oh", { opacity: 0, duration: 0.1 }, tg);
  tl.to(".dika-wrap .dika-m-worried", { opacity: 1, duration: 0.1 }, tg);
  tl.to(".dika-wrap .dika-brows > g:nth-child(1)", { opacity: 0, duration: 0.1 }, tg);
  tl.to(".dika-wrap .dika-brows > g:nth-child(2)", { opacity: 1, duration: 0.1 }, tg);
  tl.fromTo(".dika-wrap .dika-sweat", { opacity: 0 }, { opacity: 1, duration: 0.3 }, tg + 0.3);
  // 3. stempel: tingkat halusinasi dari evaluasi
  const ts = w("halusinasi");
  tl.fromTo(".stamp", { scale: 1.9, opacity: 0, rotation: -16 }, { scale: 1, opacity: 1, rotation: -7, duration: 0.26, ease: "power4.in" }, ts - 0.3);
  thud(ts - 0.04);
  // 4. yang Dika butuhkan: bacaannya sendiri, dan nilai yang belum pernah ia dapat
  const tb = w("Dika");
  tl.to([".phone", ".stamp"], { x: 900, opacity: 0, duration: 0.45, ease: "power3.in", stagger: 0.04 }, tb - 0.45);
  tl.fromTo(".sheet", { x: 160, opacity: 0, rotation: 3 }, { x: 0, opacity: 1, rotation: -1.5, duration: 0.55 }, tb - 0.05);
  drawPath($1(".mine"), tb + 0.3, 0.6, { ease: "power1.inOut" });
  tl.fromTo(".sheet .grade", { scale: 1.2, opacity: 0 }, { scale: 1, opacity: 1, duration: 0.45 }, w("menilai") + 0.1);
  tl.to(".dika-wrap .dika-arm-r", { rotation: -85, duration: 0.45, ease: "power3.out" }, tb + 0.2);
  // 5. pertanyaan yang menutup babak masalah
  const tq = w("Lalu");
  tl.fromTo(".dim", { opacity: 0 }, { opacity: 0.94, duration: 0.35, ease: "power2.out" }, tq - 0.2);
  words(".ask", tq);
  leave();
  window.__timelines[ID] = tl;
})();
</script>
</template></body></html>

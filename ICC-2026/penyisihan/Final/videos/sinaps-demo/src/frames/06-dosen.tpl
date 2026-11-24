<!doctype html>
<html><head><meta charset="UTF-8" /></head><body><template>
<style>
<!-- @base -->
#f06 { position: absolute; inset: 0; background: transparent; overflow: hidden; }
#f06 .title { position: absolute; left: 96px; top: 80px; font-size: 72px; line-height: 1.05; font-weight: 700; }
#f06 .title b { font-family: 'Oswald', sans-serif; font-size: 96px; color: var(--teal); }
#f06 .title i { font-style: normal; color: var(--bad); }
#f06 .dosen { position: absolute; left: 300px; top: 300px; }
#f06 .tdesk { position: absolute; left: 110px; top: 790px; width: 700px; height: 300px; border-radius: 10px 10px 0 0; background: #8a6a4d; }
#f06 .tdesk::before { content: ""; position: absolute; left: -14px; right: -14px; top: -20px; height: 24px; border-radius: 8px; background: #a8835f; }
#f06 .pile { position: absolute; left: 140px; top: 400px; width: 260px; height: 372px; }
#f06 .pile i { position: absolute; left: 0; width: 240px; height: 22px; border-radius: 4px; background: #fff; border: 2px solid #cbd5e1; box-shadow: 0 2px 0 #e2e8f0; }
#f06 .pile i::before { content: ""; position: absolute; left: 16px; top: 8px; width: 120px; height: 3px; background: #cbd5e1; }
#f06 .stampx { position: absolute; left: 110px; top: 560px; padding: 14px 24px; border: 6px solid var(--bad); border-radius: 14px; background: #fff; color: var(--bad); font: 700 46px/1 'Oswald', sans-serif; letter-spacing: .06em; transform: rotate(-9deg); white-space: nowrap; }
#f06 .clock { position: absolute; left: 870px; top: 250px; width: 140px; height: 140px; }
#f06 .crowd .m { position: absolute; }
#f06 .lbl { position: absolute; left: 1100px; top: 960px; font: 700 36px 'Geist', sans-serif; color: var(--ink-2); }
</style>
<div id="f06" data-composition-id="f06" data-width="1920" data-height="1080">
  <svg class="clock" viewBox="-60 -60 120 120"><circle r="54" fill="#fff" stroke="#10313a" stroke-width="7" /><line class="ch-h" x1="0" y1="0" x2="0" y2="-26" stroke="#10313a" stroke-width="7" stroke-linecap="round" /><line class="ch-m" x1="0" y1="0" x2="0" y2="-40" stroke="#dc2626" stroke-width="5" stroke-linecap="round" /><circle r="6" fill="#10313a" /></svg>
  <div class="dosen"><!-- @include dika p=f06t w=300 hair=#9aa3a8 brow=#6b7280 glasses=1 skin=#e2b08e skin2=#c48d68 scrub=#5c4a7a steth=0 smile=1 worried=0 brows=1 wbrows=0 sweat=0 --></div>
  <div class="tdesk"></div>
  <div class="pile"></div>
  <div class="stampx">BELUM DIPERIKSA</div>
  <div class="crowd">
    <div class="m" style="left: 1080px; top: 300px"><!-- @include mhs w=100 q=1 --></div>
    <div class="m" style="left: 1240px; top: 330px"><!-- @include mhs w=100 hair=#3b2a20 skin=#e2b08e q=1 --></div>
    <div class="m" style="left: 1400px; top: 290px"><!-- @include mhs w=100 skin=#a96f4c q=1 --></div>
    <div class="m" style="left: 1560px; top: 320px"><!-- @include mhs w=100 hair=#5a3a28 q=1 --></div>
    <div class="m" style="left: 1720px; top: 300px"><!-- @include mhs w=100 skin=#e2b08e hair=#2a2220 q=1 --></div>
    <div class="m" style="left: 1010px; top: 520px"><!-- @include mhs w=100 skin=#c48d68 q=1 --></div>
    <div class="m" style="left: 1170px; top: 550px"><!-- @include mhs w=100 hair=#3b2a20 q=1 --></div>
    <div class="m" style="left: 1330px; top: 510px"><!-- @include mhs w=100 skin=#a96f4c q=1 --></div>
    <div class="m" style="left: 1490px; top: 545px"><!-- @include mhs w=100 skin=#e2b08e q=1 --></div>
    <div class="m" style="left: 1650px; top: 515px"><!-- @include mhs w=100 hair=#5a3a28 skin=#d39a76 q=1 --></div>
    <div class="m" style="left: 1800px; top: 545px"><!-- @include mhs w=100 hair=#2a2220 q=1 --></div>
    <div class="m" style="left: 1090px; top: 740px"><!-- @include mhs w=100 skin=#c48d68 hair=#5a3a28 q=1 --></div>
    <div class="m" style="left: 1260px; top: 770px"><!-- @include mhs w=100 skin=#e2b08e q=1 --></div>
    <div class="m" style="left: 1430px; top: 735px"><!-- @include mhs w=100 hair=#3b2a20 skin=#a96f4c q=1 --></div>
    <div class="m" style="left: 1600px; top: 765px"><!-- @include mhs w=100 q=1 --></div>
    <div class="m" style="left: 1770px; top: 740px"><!-- @include mhs w=100 skin=#d39a76 hair=#2a2220 q=1 --></div>
  </div>
</div>
<!-- @sfx whoosh@0.0:0.45 thud_soft@0.7:0.4 tension_hit@~kewalahan:0.35 snap@~Satu-0.2:0.4 crowd_murmur@~satu.2-0.3:0.4 bubble@~satu.2:0.35 bubble_hi@~kelas:0.35 pop_lo@~penuh:0.35 paper_drop@~kelas+0.2:0.45 paper_drop@~Tidak:0.45 clock_fast@~Tidak-0.2:0.4 paper_rustle@~bacaan:0.4 stamp@~satu.3+0.1:0.65 impact_boom@~satu.3+0.12:0.35 -->
<script>
(() => {
/* @helpers */
  // tumpukan lembar bacaan
  const pile = $1(".pile");
  const sheets = [];
  for (let i = 0; i < 16; i++) {
    const s = document.createElement("i");
    s.style.top = `${350 - i * 22}px`;
    s.style.left = `${((i * 37) % 23) - 10}px`;
    s.style.transform = `rotate(${(((i * 53) % 9) - 4) * 0.8}deg)`;
    pile.appendChild(s);
    sheets.push(s);
  }
  enter("push");
  // dosen dan mejanya
  tl.fromTo(".dosen", { y: 400 }, { y: 0, duration: 0.6, ease: "back.out(1.4)" }, 0.55);
  rise(".tdesk", 0.5, { y: 120 });
  bob(".dosen .dika-rig", 1.2, END, 4, 2.0);
  blink(".dosen .dika-lid", [1.6, 4.2, 7.9]);
  const tk = w("kewalahan");
  tl.to(".dosen .dika-m-smile", { opacity: 0, duration: 0.12 }, tk);
  tl.to(".dosen .dika-m-worried", { opacity: 1, duration: 0.12 }, tk);
  tl.to(".dosen .dika-brows > g:nth-child(1)", { opacity: 0, duration: 0.12 }, tk);
  tl.to(".dosen .dika-brows > g:nth-child(2)", { opacity: 1, duration: 0.12 }, tk);
  tl.fromTo(".dosen .dika-sweat", { opacity: 0, y: -10 }, { opacity: 1, y: 14, duration: 0.8 }, tk + 0.3);
  tl.fromTo(".dosen .dika-arm-l", { rotation: 0, svgOrigin: "108 272" }, { rotation: 38, duration: 0.45, ease: "back.out(2)" }, tk);
  tl.fromTo(".dosen .dika-arm-r", { rotation: 0, svgOrigin: "212 272" }, { rotation: -38, duration: 0.45, ease: "back.out(2)" }, tk);
  tl.fromTo(".dosen .dika-head", { rotation: 0, svgOrigin: "160 240" }, { rotation: 8, duration: 0.3, yoyo: true, repeat: 3, ease: "sine.inOut" }, w("Tidak"));
  // kelas penuh: mahasiswa bermunculan dengan tanda tanya
  const ms = [...$(".crowd .m")];
  ms.forEach((m, i) => {
    const t = w("satu", 2) - 0.3 + i * 0.09;
    tl.fromTo(m, { y: 80, scale: 0.4, opacity: 0, transformOrigin: "50% 100%" }, { y: 0, scale: 1, opacity: 1, duration: 0.4, ease: "back.out(2)" }, t);
    tl.fromTo(m.querySelector(".mhs-rig"), { y: 0 }, { y: -8, duration: 0.2, yoyo: true, repeat: 5, ease: "sine.inOut" }, t + 0.5 + (i % 4) * 0.1);
  });
  tl.fromTo($(".crowd .mhs-q"), { scale: 0, transformOrigin: "30% 100%" }, { scale: 1, duration: 0.3, ease: "back.out(3)", stagger: 0.06 }, w("penuh"));
  tl.to($(".crowd .mhs-q"), { rotation: 9, duration: 0.16, yoyo: true, repeat: 3, ease: "sine.inOut", stagger: 0.04, transformOrigin: "30% 100%" }, w("Tidak"));
  // tumpukan lembar terus meninggi
  sheets.forEach((s, i) => tl.fromTo(s, { y: -260, opacity: 0 }, { y: 0, opacity: 1, duration: 0.3, ease: "bounce.out" }, w("kelas") + i * 0.07));
  // jam berputar cepat
  pop(".clock", w("Tidak") - 0.3, { from: 0.4, ease: "back.out(2.4)" });
  tl.fromTo(".clock .ch-m", { rotation: 0, svgOrigin: "0 0" }, { rotation: 720, duration: END - w("Tidak"), ease: "none" }, w("Tidak") - 0.2);
  tl.fromTo(".clock .ch-h", { rotation: 0, svgOrigin: "0 0" }, { rotation: 60, duration: END - w("Tidak"), ease: "none" }, w("Tidak") - 0.2);
  // stempel
  const ts = w("satu", 3) + 0.1;
  tl.fromTo(".stampx", { scale: 2.6, opacity: 0, rotation: -24 }, { scale: 1, opacity: 1, rotation: -9, duration: 0.3, ease: "power4.in" }, ts - 0.25);
  thud(ts + 0.05);
  leave();
  window.__timelines[ID] = tl;
})();
</script>
</template></body></html>

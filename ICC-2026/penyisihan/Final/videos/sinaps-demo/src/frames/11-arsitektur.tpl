<!doctype html>
<html><head><meta charset="UTF-8" /></head><body><template>
<style>
<!-- @base -->
#f11 { position: absolute; inset: 0; background: transparent; overflow: hidden; }
#f11 .wires { position: absolute; left: 0; top: 0; width: 1920px; height: 1080px; }
#f11 .node { position: absolute; border-radius: 22px; padding: 22px 26px; background: #fff; border: 2px solid var(--line); box-shadow: 0 1px 2px rgba(16,24,40,.04), 0 10px 26px rgba(16,24,40,.06); }
#f11 .node .t { font: 700 38px 'Geist', sans-serif; color: var(--ink); display: flex; align-items: center; gap: 12px; }
#f11 .node .s { white-space: nowrap; margin-top: 6px; font: 600 27px 'Geist', sans-serif; color: var(--muted); }
#f11 .node .ic { position: absolute; right: 22px; top: 22px; }
#f11 .llm { border-color: #f3c49a; background: var(--nt-soft); }
#f11 .llm .t { color: var(--nt-d); }
#f11 .orch { border-color: var(--teal); }
#f11 .pk { position: absolute; width: 18px; height: 18px; margin: -9px 0 0 -9px; border-radius: 50%; background: var(--nt); border: 3px solid #fff; }
</style>
<div id="f11" data-composition-id="f11" data-width="1920" data-height="1080">
  <svg class="wires" viewBox="0 0 1920 1080" fill="none" stroke-width="4" stroke-linecap="round">
    <path class="w" d="M460,560 H580" stroke="#cbd5e1" />
    <path class="w" d="M860,560 C920,560 920,300 990,300" stroke="#cbd5e1" />
    <path class="w" d="M860,560 C930,560 930,470 990,470" stroke="#cbd5e1" />
    <path class="w" d="M860,560 C930,560 930,640 990,640" stroke="#cbd5e1" />
    <path class="w" d="M860,560 C920,560 920,810 990,810" stroke="#cbd5e1" />
    <path class="w" d="M720,630 V830" stroke="#cbd5e1" />
    <path class="w" d="M1390,470 C1440,470 1440,540 1500,540" stroke="#e07a1f" stroke-dasharray="3 12" />
    <path class="w" d="M1390,640 C1440,640 1440,580 1500,580" stroke="#e07a1f" stroke-dasharray="3 12" />
    <path class="w" d="M1390,300 C1450,300 1450,520 1500,520" stroke="#e07a1f" stroke-dasharray="3 12" />
  </svg>
  <div class="node" style="left: 110px; top: 480px; width: 350px; height: 160px">
    <div class="t">Viewer web</div><div class="s">Cornerstone3D</div>
    <svg class="ic" width="40" height="40" viewBox="0 0 44 44"><rect x="3" y="7" width="38" height="30" rx="6" fill="none" stroke="#195764" stroke-width="4" /><path d="M3,16 H41" stroke="#195764" stroke-width="4" /></svg>
  </div>
  <div class="node orch" style="left: 580px; top: 490px; width: 280px; height: 140px"><div class="t">Orkestrator</div><div class="s">FastAPI</div></div>
  <div class="node det" style="left: 990px; top: 235px; width: 400px; height: 130px"><div class="t">Bank kasus</div><div class="s">SOOP</div></div>
  <div class="node det" style="left: 990px; top: 405px; width: 400px; height: 130px"><div class="t">Modul visi</div><div class="s">U-Net 2.5D</div></div>
  <div class="node det" style="left: 990px; top: 575px; width: 400px; height: 130px"><div class="t">Penilaian</div><div class="s">otomatis</div></div>
  <div class="node det" style="left: 990px; top: 745px; width: 400px; height: 130px"><div class="t">Adaptasi</div><div class="s">Knowledge Tracing (BKT)</div></div>
  <div class="node llm" style="left: 1500px; top: 480px; width: 340px; height: 160px"><div class="t">Tutor LLM</div></div>
  <div class="node" style="left: 545px; top: 830px; width: 350px; height: 130px"><div class="t">Dasbor dosen</div></div>
  <div class="pk" style="left: 520px; top: 560px"></div>
  <div class="pk" style="left: 925px; top: 380px"></div>
  <div class="pk" style="left: 1445px; top: 540px"></div>
</div>
<!-- @sfx swipe_zip@0.0:0.5 snap@~enam:0.4 mar1@~Viewer-0.3:0.45 tech_beep@~permintaan:0.35 whoosh_deep@~orkestrator-0.8:0.35 mar2@~orkestrator-0.2:0.45 swish_fast@~belakangnya:0.35 mar3@~bank-0.2:0.45 mar4@~visi-0.3:0.45 mar5@~penilaian-0.3:0.45 mar6@~adaptasi-0.3:0.45 data_chirps@~Tracing:0.35 glass_hi@~Tracing+0.3:0.45 thud_soft@~Dosen:0.45 -->
<script>
(() => {
/* @helpers */
enter("push");
  const nodes = [...$(".node")]; // 0 viewer, 1 orkestrator, 2 bank, 3 visi, 4 penilaian, 5 adaptasi, 6 tutor, 7 dasbor
  const wires = [...$(".wires .w")]; // 0 v-o, 1-4 o-modul, 5 o-dasbor, 6-8 modul-tutor
  // 1. "enam modul": seluruh kerangka muncul redup sekaligus, lalu tiap modul menyala pada gilirannya
  tl.fromTo(nodes, { y: 24, opacity: 0 }, { y: 0, opacity: 0.3, duration: 0.5, stagger: 0.04 }, 0.6);
  const show = (i, t) => {
    tl.to(nodes[i], { opacity: 1, duration: 0.35, ease: "power2.out" }, t);
    tl.fromTo(nodes[i], { boxShadow: "0 0 0 0px rgba(224,122,31,.35)" }, { boxShadow: "0 0 0 18px rgba(224,122,31,0)", duration: 0.7, ease: "power2.out", immediateRender: false }, t + 0.3);
  };
  show(0, w("Viewer") - 0.3);
  drawPath(wires[0], w("permintaan"), 0.6);
  show(1, w("orkestrator") - 0.2);
  [1, 2, 3, 4].forEach((k, i) => drawPath(wires[k], w("belakangnya") + i * 0.12, 0.7));
  show(2, w("bank") - 0.2);
  show(3, w("visi") - 0.3);
  show(4, w("penilaian") - 0.3);
  show(5, w("adaptasi") - 0.3);
  // kabel ke tutor (putus-putus): sembunyikan sampai digambar, lalu kembalikan pola putus-putusnya
  [6, 7, 8].forEach((k, i) => {
    const t = w("Tracing") + 0.2 + i * 0.1;
    tl.fromTo(wires[k], { opacity: 0 }, { opacity: 1, duration: 0.01 }, t);
    drawPath(wires[k], t, 0.6);
    tl.set(wires[k], { strokeDasharray: "3 12", strokeDashoffset: 0 }, t + 0.62);
  });
  show(6, w("Tracing") + 0.3);
  drawPath(wires[5], w("Dosen") - 0.4, 0.5);
  show(7, w("Dosen"));
  // paket data mengalir di kabel (posisi dihitung dari geometri path, bukan layout)
  const pk = [...$(".pk")];
  const route = (el, path, t0, d, reps) => {
    const len = path.getTotalLength();
    const p = { v: 0 };
    const put = () => { const pt = path.getPointAtLength(len * p.v); gsap.set(el, { left: pt.x, top: pt.y }); };
    tl.fromTo(el, { opacity: 0 }, { opacity: 1, duration: 0.2 }, t0);
    tl.fromTo(p, { v: 0 }, { v: 1, duration: d, ease: "power1.inOut", repeat: reps, repeatDelay: 0.3, onUpdate: put, onStart: put }, t0);
    tl.to(el, { opacity: 0, duration: 0.2 }, t0 + d);
  };
  route(pk[0], wires[0], w("permintaan") + 0.6, 0.9, 0);
  route(pk[1], wires[3], w("penilaian") + 0.2, 0.8, 0);
  route(pk[2], wires[7], w("Tracing") + 0.9, 0.8, 0);
  // keluar: tidak didorong. Selain "Modul visi" semuanya meredup; frame 11a membuka dari kartu itu
  tl.to(nodes.filter((_, i) => i !== 3), { opacity: 0.2, duration: 0.5, ease: "power2.inOut" }, END - 1.2);
  tl.to(wires, { opacity: 0.2, duration: 0.5, ease: "power2.inOut" }, END - 1.2);
  tl.to(nodes[3], { borderColor: "#195764", duration: 0.4 }, END - 1.2);
  window.__timelines[ID] = tl;
})();
</script>
</template></body></html>

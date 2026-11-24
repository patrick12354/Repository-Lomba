<!doctype html>
<html><head><meta charset="UTF-8" /></head><body><template>
<style>
<!-- @base -->
#f12 { position: absolute; inset: 0; background: transparent; overflow: hidden; }
#f12 .mods { position: absolute; left: 96px; top: 230px; display: flex; flex-direction: column; gap: 22px; }
#f12 .mods div { width: 310px; padding: 20px 24px; border-radius: 18px; border: 3px solid var(--line-2); background: #fff; font: 700 34px 'Geist', sans-serif; display: flex; align-items: center; gap: 12px; box-shadow: 0 6px 18px rgba(16,24,40,.05); }
#f12 .json { left: 500px; top: 230px; width: 730px; padding: 28px 36px; background: #0f2a31; border-color: #0f2a31; font: 600 28px/1.6 'Geist Mono', monospace; color: #e2e8f0; }
#f12 .json .code { white-space: pre; }
#f12 .json .k { color: #7dd3fc; } #f12 .json .n { color: #fdba74; } #f12 .json .s { color: #86efac; }
#f12 .tutor { left: 1330px; top: 230px; width: 500px; height: 330px; border-color: #f3c49a; background: var(--nt-soft); padding: 34px; }
#f12 .tutor .t { font: 700 48px 'Geist', sans-serif; color: var(--nt-d); }
#f12 .tutor .s { margin-top: 12px; font-size: 34px; line-height: 1.3; font-weight: 700; color: var(--ink-2); width: 300px; }
#f12 .sina-wrap { position: absolute; left: 1640px; top: 400px; }
#f12 .arr { position: absolute; width: 60px; height: 4px; background: var(--line-2); }
#f12 .arr::after { content: ""; position: absolute; right: -4px; top: -8px; border: 10px solid transparent; border-left: 14px solid var(--line-2); border-right: 0; }
#f12 .lane { position: absolute; left: 96px; right: 96px; top: 730px; height: 170px; border-radius: 26px; border: 2px dashed var(--line-2); display: flex; align-items: center; padding: 0 44px; gap: 40px; }
#f12 .lane .key { font: 700 40px 'Geist', sans-serif; }
#f12 .lane .line { flex: 1; height: 5px; background: repeating-linear-gradient(90deg, var(--bad) 0 22px, transparent 22px 36px); position: relative; }
#f12 .lane .lock { width: 110px; height: 110px; border-radius: 50%; background: var(--bad); display: grid; place-items: center; }
#f12 .lane .br { font: 700 40px 'Geist', sans-serif; display: flex; align-items: center; gap: 16px; }
</style>
<div id="f12" data-composition-id="f12" data-width="1920" data-height="1080" data-split="dan">
  <div class="mods"><div>Penilaian</div><div>Modul visi</div><div>Bank kasus</div></div>
  <div class="arr" style="left: 422px; top: 370px"></div>
  <div class="card json">
<div class="code">{
  <span class="k">"volume_ml"</span>: <span class="n">27.07</span>,
  <span class="k">"hemisfer"</span>: <span class="s">"kanan"</span>,
  <span class="k">"jumlah_fokus"</span>: <span class="n">1</span>,
  <span class="k">"dice"</span>: <span class="n">0.71</span>,
  <span class="k">"jenis_kesalahan"</span>: <span class="s">"terlalu_sempit"</span>
}</div>
  </div>
  <div class="arr" style="left: 1248px; top: 370px"></div>
  <div class="card tutor"><div class="t">Tutor LLM</div></div>
  <div class="sina-wrap"><!-- @include sina p=f12s w=190 --></div>
  <div class="lane">
    <div class="key">kunci jawaban</div>
    <div class="line"></div>
    <div class="lock"><svg width="50" height="58" viewBox="0 0 56 64"><path d="M14,28 V18 a14,14 0 0 1 28,0 V28" fill="none" stroke="#fff" stroke-width="7" /><rect x="5" y="28" width="46" height="32" rx="8" fill="#fff" /></svg></div>
    <div class="line"></div>
    <div class="br"><svg width="44" height="44" viewBox="0 0 44 44"><rect x="3" y="7" width="38" height="30" rx="6" fill="none" stroke="#195764" stroke-width="4" /><path d="M3,16 H41" stroke="#195764" stroke-width="4" /></svg>browser</div>
  </div>
</div>
<!-- @sfx whoosh_deep@0.0:0.45 snap@~Kuncinya:0.4 swish_fast@~Tutor-0.1:0.4 bubble@~ujung:0.45 swipe_zip@~menerima-0.3:0.4 keys_clack@~terstruktur:0.35 data_chirps@~modul+0.2:0.3 glass_tap@~lain:0.45 woosh_up@~kunci-0.4:0.35 lock_heavy@~pernah:0.65 punch_hit@~pernah:0.45 notif_pop@~dikirim:0.4 mar5@~peramban:0.4 tech_beep@~submit:0.45 -->
<script>
(() => {
/* @helpers */
enter("push");
  // tutor di ujung rantai
  tl.fromTo(".tutor", { x: 120, opacity: 0 }, { x: 0, opacity: 1, duration: 0.6 }, w("Tutor") - 0.1);
  tl.fromTo(".sina-wrap", { scale: 0.6, y: 40, opacity: 0, transformOrigin: "50% 100%" }, { scale: 1, y: 0, opacity: 1, duration: 0.55 }, w("ujung"));
  bob(".sina-rig", w("ujung") + 0.6, END, 6, 1.6);
  blink(".sina-lid", [5.2, 8.8, 12.2]);
  // fakta terstruktur dari modul deterministik
  // 1. tiga modul deterministik (sumber fakta)
  slideIn(".mods div", 0.6, { x: -80, stagger: 0.08 });
  tl.fromTo($(".arr")[0], { scaleX: 0, transformOrigin: "0% 50%" }, { scaleX: 1, duration: 0.4 }, w("fakta"));
  tl.fromTo(".json", { y: 40, opacity: 0 }, { y: 0, opacity: 1, duration: 0.6 }, w("fakta") - 0.1);
  tl.fromTo(".json .code", { clipPath: "inset(0 0 100% 0)" }, { clipPath: "inset(0 0 0% 0)", duration: 1.3, ease: "steps(7)" }, w("terstruktur"));
  tl.fromTo($(".arr")[1], { scaleX: 0, transformOrigin: "0% 50%" }, { scaleX: 1, duration: 0.4 }, w("modul") + 0.2);
  tl.to(".tutor", { borderColor: "#e07a1f", boxShadow: "0 0 0 10px rgba(224,122,31,.18)", duration: 0.3, yoyo: true, repeat: 1 }, w("lain"));
  tl.fromTo(".sina-rig", { rotation: 0, svgOrigin: "0 110" }, { rotation: -14, duration: 0.25, yoyo: true, repeat: 3, ease: "sine.inOut", immediateRender: false }, w("lain"));
  // kunci jawaban terkunci sebelum submit
  rise(".lane", w("kunci", 2) - 0.4, { y: 30 });
  tl.fromTo($(".lane .line")[0], { scaleX: 0, transformOrigin: "0% 50%" }, { scaleX: 1, duration: 0.6 }, w("jawaban"));
  pop(".lane .lock", w("tidak") - 0.1, { from: 0, ease: "back.out(2.4)" });
  tl.fromTo(".lane .lock svg path", { y: -12 }, { y: 0, duration: 0.25, ease: "power4.in" }, w("pernah"));
  tl.fromTo(".lane .lock", { rotation: 0 }, { rotation: 6, duration: 0.08, yoyo: true, repeat: 1, immediateRender: false }, w("pernah") + 0.25);
  tl.fromTo($(".lane .line")[1], { scaleX: 0, transformOrigin: "0% 50%" }, { scaleX: 1, duration: 0.6 }, w("peramban") - 0.2);
  slideIn(".lane .br", w("peramban"), { x: 40 });
  leave();
  window.__timelines[ID] = tl;
})();
</script>
</template></body></html>

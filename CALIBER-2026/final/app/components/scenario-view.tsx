"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { Area, CartesianGrid, ComposedChart, Line, ReferenceDot, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Loader2, Mail } from "lucide-react";
import { Lightbulb, Receipt } from "@/components/icons";
import type { FrontierPoint } from "@/lib/data";
import { cn, num, pct, rp } from "@/lib/format";
import { Em, PageHead, Panel, PanelHead } from "./ui";
import { AiBrief } from "./ai-brief";
import { Hint } from "./hint";
import { Compose } from "./compose";
import { isId, t } from "@/lib/i18n";

type Data = {
  curve: FrontierPoint[];
  current: FrontierPoint;
  optimized: FrontierPoint;
  pick: FrontierPoint;
  holding: number;
};
export type Replay = { fillToday: number; fill: number; stockToday: number; stock: number; daysToday: number; days: number } | null;

/** Rupiah per A-part shortage day. Spaced for a slider; none of these comes from the data. */
const RATES = [5e5, 1e6, 2e6, 5e6, 1e7, 2e7, 5e7];
const DEFAULT_RATE_IDX = 3;
const X_MAX = 1000;
const X_TICKS = [30, 60, 100, 200, 400, 700, 1000];

type Mode = "optimized" | "cheapest" | "today" | "custom";
/** The English name is the key the memo API reads; the label is what the page shows. */
const POLICY_KEY: Record<Mode, string> = { optimized: "Recommended", cheapest: "Lowest total cost", today: "Stay as we are", custom: "Pick a budget" };
const policies = (): [Mode, string, string][] => [
  ["optimized", t("Recommended", "Disarankan"), t("Target service level: 95% for A parts, 90% B, 85% C, 80% S", "Target tingkat layanan: 95% untuk suku cadang A, 90% B, 85% C, 80% S")],
  ["cheapest", t("Lowest total cost", "Total biaya terendah"), t("Moves as you change the two sliders below", "Bergeser saat Anda mengubah dua penggeser di bawah")],
  ["today", t("Stay as we are", "Tetap seperti sekarang"), t("Keep today's Min and Max in SAP", "Pertahankan Min dan Max di SAP saat ini")],
  ["custom", t("Pick a budget", "Pilih anggaran"), t("Slide to any amount of stock", "Geser ke jumlah stok berapa pun")],
];

const bn = (v: number) => {
  const s = v >= 100 ? Math.round(v).toString() : v.toFixed(v >= 10 ? 0 : 1);
  return isId() ? s.replace(".", ",") : s;
};
const billion = () => t("billion", "miliar");

export function ScenarioView({ initial, replay }: { initial: Data; replay: Replay }) {
  const data = initial;
  const curve = useMemo(() => data.curve.filter((p) => p.budget_idr / 1e9 <= X_MAX), [data.curve]);
  const [idx, setIdx] = useState(() => nearest(curve, initial.optimized.budget_idr));
  const [mode, setMode] = useState<Mode>("optimized");
  const [rateIdx, setRateIdx] = useState(DEFAULT_RATE_IDX);
  /* A plan the person left by moving an assumption: Pick a budget stays on it exactly until the stock slider moves. */
  const [held, setHeld] = useState<FrontierPoint | null>(null);
  const [holding, setHolding] = useState(initial.holding);
  const rate = RATES[rateIdx];
  const [memo, setMemo] = useState<{ text: string; source: string } | null>(null);
  const [writing, setWriting] = useState(false);
  const [emailing, setEmailing] = useState(false);

  const cur = data.current;
  const exposure = (p: FrontierPoint) => (p.exp_risk_cost / 100) * rate;
  const hold = (p: FrontierPoint) => p.budget_idr * holding;
  const total = (p: FrontierPoint) => hold(p) + exposure(p);
  const cheapest = curve.reduce((b, p) => (total(p) < total(b) ? p : b), curve[0]);
  const pick: FrontierPoint = mode === "optimized" ? data.optimized : mode === "cheapest" ? cheapest : mode === "today" ? cur : (held ?? curve[idx]);
  const sliderIdx = mode === "custom" && !held ? idx : nearest(curve, pick.budget_idr);

  /* A preset brings back its own settings. Pick a budget starts from whatever is on screen. */
  const choosePlan = (next: Mode) => {
    if (next === "custom") {
      setHeld(pick);
      setIdx(sliderIdx);
    } else {
      setHeld(null);
      setHolding(initial.holding);
      setRateIdx(DEFAULT_RATE_IDX);
    }
    setMode(next);
  };
  const moveStock = (i: number) => {
    setHeld(null);
    setIdx(i);
    setMode("custom");
  };
  /* Lowest total cost is defined by these two sliders, so it stays selected. The fixed plans become a custom one. */
  const moveAssumption = (apply: () => void) => {
    if (mode === "optimized" || mode === "today") {
      setHeld(pick);
      setIdx(sliderIdx);
      setMode("custom");
    }
    apply();
  };
  const POLICIES = policies();
  const policyName = POLICIES.find((p) => p[0] === mode)![1];

  const writeMemo = () => {
    setWriting(true);
    fetch("/api/ai/memo", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ policy: POLICY_KEY[mode], budget: pick.budget_idr, holding, rate }) })
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(String(r.status)))))
      .then(setMemo)
      .catch(() => setMemo({ text: t("Could not write the memo. Try again.", "Memo gagal dibuat. Coba lagi."), source: "template" }))
      .finally(() => setWriting(false));
  };

  const chart = curve.map((p) => {
    const x = p.budget_idr / 1e9;
    return { x, holding: hold(p) / 1e9, exposure: exposure(p) / 1e9, total: total(p) / 1e9 };
  });
  const yMax = Math.max(total(cur), hold(curve[curve.length - 1])) / 1e9;
  const yTop = niceTop(yMax * 1.08);
  const saving = total(cur) - total(pick);
  const cheapestSaving = total(cur) - total(cheapest);

  return (
    <div className="space-y-5">
      <PageHead
        title={t("What if we keep more or less stock?", "Bagaimana jika stok kita tambah atau kurangi?")}
        actions={<AiBrief page="whatif" />}
        answer={t(
          <>
            The recommended plan holds <Em tone="ready">{rp(data.optimized.budget_idr)}</Em> of stock on average instead of {rp(cur.budget_idr)}, and cuts the risk of running out by <Em tone="ready">{pct(1 - data.optimized.exp_risk_cost / cur.exp_risk_cost)}</Em>.
{" "}
            <Hint>A model of each plan once it has settled. Risk of running out is the expected number of shortage days, with B, C and S days weighted as set at left. Stock is valued over all parts, using the median price of the same part type where a part has no purchase order. &quot;Today&quot; is today&apos;s Min in SAP with the same order sizes, so only the reorder levels differ.</Hint>
          </>,
          <>
            Rencana yang disarankan menyimpan rata-rata <Em tone="ready">{rp(data.optimized.budget_idr)}</Em> stok, bukan {rp(cur.budget_idr)}, dan menurunkan risiko kehabisan stok sebesar <Em tone="ready">{pct(1 - data.optimized.exp_risk_cost / cur.exp_risk_cost)}</Em>.
{" "}
            <Hint>Model setiap rencana setelah kondisinya stabil. Risiko kehabisan stok adalah perkiraan jumlah hari kekurangan, dengan bobot hari B, C, dan S sesuai pengaturan di sebelah kiri. Nilai stok dihitung untuk semua suku cadang, memakai harga median jenis suku cadang yang sama jika belum pernah dipesan. &quot;Saat ini&quot; adalah Min di SAP saat ini dengan ukuran pesanan yang sama, jadi yang berbeda hanya titik pemesanan ulangnya.</Hint>
          </>,
        )}
      />

      <div className="grid grid-cols-1 items-stretch gap-5 lg:grid-cols-[320px_minmax(0,1fr)]">
        <Panel tour="w-policy" className="flex flex-col gap-5 p-5">
          <div>
            <h2 className="m-0 mb-2 text-[14px] font-semibold">{t("Pick a stocking plan", "Pilih rencana stok")}</h2>
            <div role="radiogroup" aria-label={t("Stocking plan", "Rencana stok")} className="space-y-1.5">
              {POLICIES.map(([k, label, sub]) => (
                <button key={k} type="button" role="radio" aria-checked={mode === k} onClick={() => choosePlan(k)} className={cn("flex w-full flex-col rounded-[12px] border px-3 py-2 text-left transition-colors duration-150", mode === k ? "border-ink bg-panel-2" : "border-line hover:border-line-2")}>
                  <span className="text-[13.5px] font-medium">{label}</span>
                  <span className="text-[12px] text-ink-3">{sub}</span>
                </button>
              ))}
            </div>
          </div>
          <label className="block">
            <span className="flex items-baseline justify-between text-[13px]">
              <span className="font-medium">{t("Average value of stock held", "Rata-rata nilai stok yang disimpan")}</span>
              <b className="font-semibold tabular-nums">{rp(pick.budget_idr)}</b>
            </span>
            <input type="range" min={0} max={curve.length - 1} step={1} value={sliderIdx} onChange={(e) => moveStock(Number(e.target.value))} className="mt-2 h-2 w-full cursor-pointer" aria-valuetext={rp(pick.budget_idr)} />
          </label>
          <div data-tour="w-sliders" className="space-y-5">
          <label className="block">
            <span className="flex items-baseline justify-between text-[13px]">
              <span className="font-medium">{t("Yearly cost of holding stock, as % of its value", "Biaya penyimpanan stok per tahun, dalam % dari nilainya")}</span>
              <b className="font-semibold tabular-nums">{Math.round(holding * 100)}%</b>
            </span>
            <input type="range" min={0.05} max={0.5} step={0.01} value={holding} onChange={(e) => { const v = Number(e.target.value); moveAssumption(() => setHolding(v)); }} className="mt-2 h-2 w-full cursor-pointer" />
            <span className="mt-1 block text-[12px] leading-snug text-ink-3">{t("Storage, capital and ageing. Higher makes the blue area grow, so holding less becomes best.", "Gudang, modal, dan penuaan barang. Makin tinggi, area biru makin besar, sehingga menyimpan lebih sedikit menjadi pilihan terbaik.")}</span>
          </label>
          <label className="block">
            <span className="flex items-baseline justify-between text-[13px]">
              <span className="font-medium">{t("Cost of one day without an A part", "Biaya satu hari tanpa suku cadang A")} <span className="font-normal text-ink-3">{t("(assumed)", "(asumsi)")}</span></span>
              <b className="shrink-0 font-semibold tabular-nums">{rp(rate, { compact: true })}</b>
            </span>
            <input type="range" min={0} max={RATES.length - 1} step={1} value={rateIdx} onChange={(e) => { const v = Number(e.target.value); moveAssumption(() => setRateIdx(v)); }} className="mt-2 h-2 w-full cursor-pointer" aria-valuetext={rp(rate, { compact: true })} />
            <span className="mt-1 block text-[12px] leading-snug text-ink-3">{t("Higher makes the orange area grow, so holding more becomes best. A B part counts 30% of this, C 5%, S 1%.", "Makin tinggi, area oranye makin besar, sehingga menyimpan lebih banyak menjadi pilihan terbaik. Suku cadang B dihitung 30% dari angka ini, C 5%, S 1%.")}</span>
          </label>
          </div>
        </Panel>

        <Panel className="flex min-w-0 flex-col">
          <PanelHead title={t("What each stock level costs a year", "Biaya tahunan setiap tingkat stok")} aside={<Legend />} />
          <p className="m-0 px-5 pt-1 text-[13px] leading-[1.5] text-ink-2">
            {t(
              <>
                {data.optimized.budget_idr <= cur.budget_idr && data.optimized.exp_risk_cost <= cur.exp_risk_cost && <>The Recommended plan holds less stock <i>and</i> runs out less than today, so it is cheaper at any setting of the two sliders. They only move the cheapest point. </>}
                With these two assumptions, the cheapest amount of stock to hold is <b className="font-semibold text-ink">{rp(cheapest.budget_idr)}</b>, which costs <b className="font-semibold text-ready-ink">{rp(cheapestSaving)}</b> a year less than today.
              </>,
              <>
                {data.optimized.budget_idr <= cur.budget_idr && data.optimized.exp_risk_cost <= cur.exp_risk_cost && <>Rencana yang Disarankan menyimpan stok lebih sedikit <i>dan</i> lebih jarang kehabisan stok daripada saat ini, sehingga lebih murah pada pengaturan berapa pun dari kedua penggeser. Penggeser hanya memindahkan titik termurahnya. </>}
                Dengan dua asumsi ini, jumlah stok termurah untuk disimpan adalah <b className="font-semibold text-ink">{rp(cheapest.budget_idr)}</b>, dengan biaya <b className="font-semibold text-ready-ink">{rp(cheapestSaving)}</b> per tahun lebih rendah daripada saat ini.
              </>,
            )}
          </p>
          <div data-tour="w-chart" className="h-[340px] px-3 pb-2 pt-2">
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={chart} margin={{ top: 22, right: 22, bottom: 18, left: 4 }}>
                <CartesianGrid stroke="rgb(30 26 20 / 0.06)" vertical={false} />
                <XAxis type="number" dataKey="x" scale="log" domain={[X_TICKS[0], X_MAX]} ticks={X_TICKS} allowDataOverflow tickFormatter={(v) => `${v}`} tick={{ fontSize: 11, fill: "#6f6f73" }} tickLine={false} axisLine={false} label={{ value: t("Average stock value, Rp billion (each step on this axis is a bigger jump)", "Rata-rata nilai stok, miliar rupiah (setiap langkah pada sumbu ini makin besar)"), position: "insideBottom", offset: -10, fontSize: 12, fill: "#6f6f73" }} />
                <YAxis type="number" domain={[0, yTop]} ticks={[0, 0.25, 0.5, 0.75, 1].map((f) => f * yTop)} allowDataOverflow tickFormatter={(v) => bn(v)} tick={{ fontSize: 11, fill: "#6f6f73" }} tickLine={false} axisLine={false} width={44} label={{ value: t("Rp billion a year", "Miliar rupiah per tahun"), angle: -90, position: "insideLeft", offset: 8, fontSize: 12, fill: "#6f6f73" }} />
                <Tooltip
                  cursor={{ stroke: "rgb(30 26 20 / 0.2)" }}
                  content={({ active, payload }) => {
                    const row = payload?.[0]?.payload as (typeof chart)[number] | undefined;
                    return active && row ? (
                      <div className="rounded-[10px] bg-ink px-3 py-2 text-[12px] text-white">
                        <div className="font-medium">{t(`Rp ${bn(row.x)} billion of stock`, `Stok Rp${bn(row.x)} miliar`)}</div>
                        <div className="text-white/70">{t("Cost to hold it", "Biaya penyimpanan")}: {t("Rp ", "Rp")}{bn(row.holding)} {billion()}</div>
                        <div className="text-white/70">{t("Cost of shortages", "Biaya kekurangan stok")}: {t("Rp ", "Rp")}{bn(row.exposure)} {billion()}</div>
                        <div>{t(`Total: Rp ${bn(row.total)} billion a year`, `Total: Rp${bn(row.total)} miliar per tahun`)}</div>
                      </div>
                    ) : null;
                  }}
                />
                <Area dataKey="holding" stackId="cost" type="monotone" stroke="none" fill="#2f6fb5" fillOpacity={0.3} isAnimationActive={false} />
                <Area dataKey="exposure" stackId="cost" type="monotone" stroke="none" fill="#d9480f" fillOpacity={0.26} isAnimationActive={false} />
                <Line dataKey="total" type="monotone" stroke="#16171a" strokeWidth={2} dot={false} isAnimationActive={false} />
                <ReferenceLine x={pick.budget_idr / 1e9} stroke="#16171a" strokeDasharray="3 3" strokeOpacity={0.4} />
                <ReferenceDot x={cheapest.budget_idr / 1e9} y={total(cheapest) / 1e9} r={5} fill="#1e8a5a" stroke="white" strokeWidth={2} />
                <ReferenceDot x={cur.budget_idr / 1e9} y={Math.min(total(cur) / 1e9, yTop)} r={7} fill="#d8402a" stroke="white" strokeWidth={2} label={{ value: t("Today", "Saat ini"), position: "top", fontSize: 12, fontWeight: 600, fill: "#a52c1b" }} />
                {mode !== "today" && <ReferenceDot x={pick.budget_idr / 1e9} y={total(pick) / 1e9} r={8} fill="#16171a" stroke="white" strokeWidth={2.5} label={{ value: mode === "custom" ? t("Your pick", "Pilihan Anda") : policyName, position: "top", fontSize: 12, fontWeight: 600, fill: "#16171a" }} />}
              </ComposedChart>
            </ResponsiveContainer>
          </div>

          <div data-tour="w-bill" className="grid grid-cols-1 gap-x-8 gap-y-4 border-t border-line px-5 py-4 md:grid-cols-2">
            <CostBars today={{ hold: hold(cur), risk: exposure(cur) }} next={{ hold: hold(pick), risk: exposure(pick) }} name={policyName} saving={saving} />
            <div className="space-y-2.5">
              <Move label={t("Average stock, once settled", "Rata-rata stok setelah stabil")} today={rp(cur.budget_idr)} next={rp(pick.budget_idr)} share={pick.budget_idr / cur.budget_idr} goodWhenDown />
              <Move label={t("Shortage days a year, in A-part days", "Hari kekurangan per tahun, setara hari suku cadang A")} today={num(cur.exp_risk_cost / 100)} next={num(pick.exp_risk_cost / 100)} share={pick.exp_risk_cost / cur.exp_risk_cost} goodWhenDown />
              {replay && (
                <p className="m-0 border-t border-line pt-2.5 text-[12.5px] leading-[1.5] text-ink-2">
                  {t(
                    <><Link href="/replay" className="font-semibold text-ink underline underline-offset-2">Tested on real use, Mar–Sep 2026</Link> (Recommended against today&apos;s Min and Max): critical stocked parts on the shelf for <b className="font-semibold text-ready-ink">{pct(replay.fill)}</b> of requests, up from {pct(replay.fillToday)}, with {pct(1 - replay.stock / replay.stockToday)} less stock on average across all stocked parts.</>,
                    <><Link href="/replay" className="font-semibold text-ink underline underline-offset-2">Diuji dengan pemakaian riil, Mar–Sep 2026</Link> (Disarankan dibandingkan Min dan Max saat ini): suku cadang kritis yang distok tersedia di rak untuk <b className="font-semibold text-ready-ink">{pct(replay.fill)}</b> permintaan, naik dari {pct(replay.fillToday)}, dengan rata-rata stok seluruh suku cadang distok {pct(1 - replay.stock / replay.stockToday)} lebih sedikit.</>,
                  )}
                </p>
              )}
            </div>
          </div>
          <p className="m-0 border-t border-line px-5 py-3 text-[12.5px] leading-[1.5] text-ink-3">
            {t(
              <>Today sits above the curve because money is in the wrong parts: the same money, placed where shortages hurt most, leaves far less risk. The cost of a shortage day is not in the data, so every shortage rupiah rests on the assumption at left. This chart shows a plan once it has settled, across all parts, and it also counts Non Stock parts, which have no Min today, so today&apos;s shortage days read high. The replay measures availability on critical stocked parts on real use and values stock across all stocked parts{replay && <> ({pct(1 - replay.stock / replay.stockToday)} less stock there, {pct(1 - data.optimized.budget_idr / cur.budget_idr)} less here)</>}. Quote the replay when you need one number.</>,
              <>Posisi saat ini berada di atas kurva karena uangnya tertanam di suku cadang yang keliru: dengan uang yang sama, jika ditempatkan di suku cadang yang kekurangannya paling merugikan, risikonya jauh lebih kecil. Biaya satu hari kekurangan tidak ada dalam data, jadi setiap rupiah biaya kekurangan bertumpu pada asumsi di sebelah kiri. Grafik ini menunjukkan rencana setelah stabil, untuk semua suku cadang, dan juga menghitung suku cadang Non Stock yang saat ini tidak memiliki Min, sehingga hari kekurangan saat ini tampak tinggi. Simulasi ulang mengukur ketersediaan pada suku cadang kritis yang distok dengan pemakaian riil, dan menilai stok seluruh suku cadang yang distok{replay && <> (stok {pct(1 - replay.stock / replay.stockToday)} lebih sedikit di sana, {pct(1 - data.optimized.budget_idr / cur.budget_idr)} lebih sedikit di sini)</>}. Kutip angka simulasi ulang jika Anda membutuhkan satu angka saja.</>,
            )}
          </p>
          <div data-tour="w-memo" className="border-t border-line px-5 py-3">
            {!memo ? (
              <button type="button" onClick={writeMemo} disabled={writing} className="inline-flex h-9 items-center gap-2 rounded-[10px] border border-line-2 px-3 text-[13px] font-medium transition-colors hover:bg-ink/[0.04] disabled:opacity-60">
                {writing ? <Loader2 aria-hidden className="h-4 w-4 animate-spin" /> : <Lightbulb aria-hidden className="h-4 w-4" />}
                {t("Write a memo for finance on this plan", "Tulis memo untuk keuangan tentang rencana ini")}
              </button>
            ) : (
              <div>
                <div className="flex items-center justify-between gap-3">
                  <h3 className="m-0 inline-flex items-center gap-1.5 text-[13px] font-semibold"><Receipt aria-hidden className="h-4 w-4" />{t("Memo", "Memo")}: {policyName}</h3>
                  <span className="flex items-center gap-1">
                    <button type="button" onClick={writeMemo} disabled={writing} className="inline-flex h-7 items-center gap-1.5 rounded-[8px] px-2 text-[12.5px] font-medium text-ink-2 transition-colors hover:bg-ink/[0.05]">{writing && <Loader2 aria-hidden className="h-3.5 w-3.5 animate-spin" />}{t("Rewrite", "Tulis ulang")}</button>
                    <button type="button" onClick={() => setEmailing(true)} className="inline-flex h-7 items-center gap-1.5 rounded-[8px] bg-ink px-2.5 text-[12.5px] font-medium text-white transition-colors hover:bg-ink-2"><Mail aria-hidden className="h-3.5 w-3.5" />{t("Email to finance", "Kirim surel ke keuangan")}</button>
                  </span>
                </div>
                <p className="m-0 mt-1.5 whitespace-pre-wrap text-[13px] leading-[1.55]">{memo.text}</p>
                <span className="mt-1 block text-[11.5px] text-ink-4">{memo.source === "openai" ? t("Written by AI · numbers from the engine", "Ditulis oleh AI · angka dari mesin hitung") : t("Template text · AI is off", "Teks templat · AI tidak aktif")}</span>
              </div>
            )}
          </div>
        </Panel>
      </div>
      {emailing && memo && <Compose request={{ kind: "note", to: "finance", subject: t(`Stock plan memo: ${policyName}`, `Memo rencana stok: ${policyName}`), body: memo.text, heading: t("Email to finance", "Kirim surel ke keuangan"), source: memo.source }} onClose={() => setEmailing(false)} />}
    </div>
  );
}

function nearest(curve: FrontierPoint[], budget: number) {
  let best = 0;
  curve.forEach((p, i) => {
    if (Math.abs(p.budget_idr - budget) < Math.abs(curve[best].budget_idr - budget)) best = i;
  });
  return best;
}

/** A round axis top that divides into four round steps. */
function niceTop(v: number) {
  const base = 10 ** Math.floor(Math.log10(v / 4));
  const step = [1, 2, 2.5, 5, 10].map((m) => m * base).find((s) => s * 4 >= v) ?? 10 * base;
  return step * 4;
}

function Legend() {
  const item = "inline-flex items-center gap-1.5";
  return (
    <span className="hidden flex-wrap items-center justify-end gap-x-3 text-[12px] text-ink-3 md:flex">
      <span className={item}><i className="h-2.5 w-2.5 rounded-[3px] bg-[#2f6fb5]/50" />{t("Cost to hold stock", "Biaya penyimpanan stok")}</span>
      <span className={item}><i className="h-2.5 w-2.5 rounded-[3px] bg-[#d9480f]/50" />{t("Cost of shortages", "Biaya kekurangan stok")}</span>
      <span className={item}><i className="h-0.5 w-3 bg-ink" />Total</span>
      <span className={item}><i className="h-2.5 w-2.5 rounded-full bg-[#1e8a5a]" />{t("Cheapest point", "Titik termurah")}</span>
    </span>
  );
}

/** Two bars on one scale: the yearly bill today and under the policy. */
function CostBars({ today, next, name, saving }: { today: { hold: number; risk: number }; next: { hold: number; risk: number }; name: string; saving: number }) {
  const top = Math.max(today.hold + today.risk, next.hold + next.risk, 1);
  const bar = (label: string, v: { hold: number; risk: number }) => (
    <div>
      <div className="flex items-baseline justify-between text-[12.5px]"><span className="text-ink-2">{label}</span><b className="font-semibold tabular-nums">{rp(v.hold + v.risk)}</b></div>
      <div className="mt-1 flex h-3.5 overflow-hidden rounded-[5px] bg-ink/[0.05]">
        <div className="h-full bg-[#2f6fb5]/55" style={{ width: `${(v.hold / top) * 100}%` }} title={`${t("Cost to hold stock", "Biaya penyimpanan stok")}: ${rp(v.hold)}`} />
        <div className="h-full bg-[#d9480f]/55" style={{ width: `${(v.risk / top) * 100}%` }} title={`${t("Cost of shortages", "Biaya kekurangan stok")}: ${rp(v.risk)}`} />
      </div>
    </div>
  );
  return (
    <div className="space-y-2.5">
      <h3 className="m-0 text-[13px] font-semibold">{t("The yearly bill: holding stock plus shortages", "Tagihan tahunan: penyimpanan stok ditambah kekurangan stok")}</h3>
      {bar(t("Today", "Saat ini"), today)}
      {bar(name, next)}
      {Math.abs(saving) >= 1e6 && <p className={cn("m-0 text-[13px] font-medium", saving > 0 ? "text-ready-ink" : "text-act-ink")}>{saving > 0 ? t(`${rp(saving)} a year less than today`, `${rp(saving)} per tahun lebih hemat daripada saat ini`) : t(`${rp(-saving)} a year more than today`, `${rp(-saving)} per tahun lebih mahal daripada saat ini`)}</p>}
    </div>
  );
}

function Move({ label, today, next, share, goodWhenDown, points }: { label: string; today: string; next: string; share: number; goodWhenDown?: boolean; points?: number }) {
  const delta = share - 1;
  const good = goodWhenDown ? delta <= 0 : delta >= 0;
  const text = points != null ? `${points >= 0 ? "+" : "−"}${num(Math.abs(points * 100), 1)} ${t("points", "poin")}` : `${delta >= 0 ? "+" : "−"}${Math.abs(Math.round(delta * 100))}%`;
  return (
    <div className="flex items-baseline justify-between gap-3 text-[12.5px]">
      <span className="min-w-0 text-ink-2">{label}</span>
      <span className="flex shrink-0 items-baseline gap-2 tabular-nums">
        <span className="text-ink-3">{today} →</span>
        <b className="font-semibold">{next}</b>
        <span className={cn("w-[62px] rounded-[6px] px-1.5 py-0.5 text-center text-[11.5px] font-semibold", Math.abs(delta) < 1e-4 ? "bg-ink/[0.05] text-ink-3" : good ? "bg-ready-soft text-ready-ink" : "bg-act-soft text-act-ink")}>{text}</span>
      </span>
    </div>
  );
}

import "server-only";
import { asOf, part, taskFor, type Task, type TaskKind, type Urgency } from "./data";
import { MACHINES } from "./machines";
import { amount, num, partName, plainReason, rp, shortDate } from "./format";
import { CODE_NAME, PEOPLE, recipientFor, SUPPLIER, type Person } from "./people";
import { isId, lang, t as tx } from "./i18n";

/**
 * OpenAI is the writer, never the calculator. Every number comes from the engine in SQLite and reaches the
 * model as facts built here on the server, so a request can only name a part, not supply data.
 * With no key, or when the call fails, each function answers from a template and says so.
 */
const MODEL = process.env.OPENAI_MODEL || "gpt-6-luna";
const HOUR_CAP = Number(process.env.OPENAI_HOURLY_CAP || 300);
export type Source = "openai" | "template";

let windowStart = 0;
let used = 0;
const cache = new Map<string, unknown>();

type ToolCall = { id: string; type: "function"; function: { name: string; arguments: string } };
export type Message = { role: "system" | "user" | "assistant" | "tool"; content: string | null; tool_calls?: ToolCall[]; tool_call_id?: string };

export async function chat(system: string, user: string, schema?: { name: string; schema: object }): Promise<string | null> {
  const reply = await complete(
    [
      { role: "system", content: system },
      { role: "user", content: user },
    ],
    schema ? { response_format: { type: "json_schema", json_schema: { name: schema.name, strict: true, schema: schema.schema } } } : {},
  );
  return reply?.content?.trim() || null;
}

export async function complete(messages: Message[], extra: Record<string, unknown>): Promise<Message | null> {
  const key = process.env.OPENAI_API_KEY;
  if (!key) return null;
  const now = Date.now();
  if (now - windowStart > 3_600_000) {
    windowStart = now;
    used = 0;
  }
  if (used >= HOUR_CAP) return null;
  used++;
  try {
    const res = await fetch("https://api.openai.com/v1/chat/completions", {
      method: "POST",
      headers: { "content-type": "application/json", authorization: `Bearer ${key}` },
      signal: AbortSignal.timeout(25_000),
      body: JSON.stringify({
        model: MODEL,
        max_completion_tokens: 2000,
        messages,
        ...extra,
      }),
    });
    if (res.status === 400 && extra.reasoning_effort) {
      // Some models reject this setting; tools still work on them without it.
      const rest = { ...extra };
      delete rest.reasoning_effort;
      return complete(messages, rest);
    }
    if (!res.ok) {
      console.error(`OpenAI ${res.status}: ${(await res.text()).slice(0, 300)}`);
      return null;
    }
    const data = (await res.json()) as { choices?: { message?: Message }[] };
    return data.choices?.[0]?.message ?? null;
  } catch (e) {
    console.error("OpenAI call failed", e);
    return null;
  }
}

const RULES_EN = "You support a spare-parts planner at a petrochemical plant. recommended_action and quantity are the decision; everyday_policy_note only gives background and may show a different quantity, so never quote its quantity. Use only the numbers in FACTS and copy them exactly. Never invent a number, supplier, date or cause. Plain business English for someone who does not know planning jargon, no markdown, no filler. Never write codes: say rush order not expedite, duplicate part not twin, delivery time not lead time or p90, pieces and sets not EA and SET, turnaround not TA. Prices may be estimates, the data is a case-study dataset, and downtime in rupiah is an assumption.";

const RULES_ID = "You support a spare-parts planner at a petrochemical plant. recommended_action and quantity are the decision; everyday_policy_note only gives background and may show a different quantity, so never quote its quantity. Use only the numbers in FACTS and copy them exactly. Never invent a number, supplier, date or cause. Write every word of your answer in Bahasa Indonesia: formal, correct and natural (bahasa baku sesuai KBBI dan EYD), the way an experienced Indonesian plant engineer writes to a colleague. Do not translate word for word from English, and do not mix in English unless it is an established plant term (turnaround, overhaul, Min, Max, SAP). Write numbers the Indonesian way (1.234,5) and money as Rp1,2 miliar or Rp350 juta. No markdown, no filler. Never write codes: say percepat pesanan not expedite, suku cadang kembar not twin, waktu kirim not lead time or p90, buah and set not EA and SET, turnaround not TA. Prices may be estimates, the data is a case-study dataset, and downtime in rupiah is an assumption.";

/** The writing rules in the reader's language. Read per call, so each request follows its own language. */
export const rules = () => (isId() ? RULES_ID : RULES_EN);

export function facts(t: Task) {
  const d = part(t.material_no);
  const m = d?.m as Record<string, unknown> | undefined;
  let drivers: Record<string, unknown> = {};
  try {
    drivers = JSON.parse(String(m?.drivers ?? "{}"));
  } catch {}
  return {
    part: partName(t.description),
    material_no: t.material_no,
    criticality: t.criticality,
    recommended_action: t.kind,
    quantity: t.qty,
    unit: t.unit,
    stock: t.stock,
    current_min: m?.min_cur,
    current_max: m?.max_cur,
    new_min: m?.min_new,
    new_max: m?.max_new,
    order_by: t.order_by,
    days_left: t.days_left,
    lead_time_p90_days: Math.round(t.lead_time),
    main_supplier: m?.main_supplier ?? null,
    turnaround_part: t.ta,
    turnaround_gap: t.ta_gap,
    normal_use_before_turnaround: t.ta_routine,
    turnaround_date: d?.taDate,
    data_date: asOf(),
    chance_used_180d: m?.p_move,
    forecast_q50: m?.q50,
    forecast_q95: m?.q95,
    never_used_in_17_months: m?.cold_start === 1,
    months_used_of_17: m?.months_active,
    places_installed: m?.n_funcloc,
    breakdown_notices_90d: drivers.fl_notif_90d ?? null,
    planned_jobs_due_90d: drivers.pm_due_90 ?? null,
    open_notifications: drivers.fl_open_notif ?? null,
    estimated_value_idr: t.value,
    price_is_from_po: m?.price_source === "po",
    data_trust_score: m?.trust_score,
    equipment: t.equipment,
    twin_donor: t.twin,
    unusual_recent_use: t.unusual,
    everyday_policy_note: m?.reason,
  };
}

const VERB_EN: Record<TaskKind, string> = { expedite: "Rush order", order: "Order", twin: "Move from the duplicate part", reduce: "Stop buying", dispose: "Check if still needed", watch: "Keep an eye on" };
const VERB_ID: Record<TaskKind, string> = { expedite: "Percepat pesanan", order: "Pesan", twin: "Pindahkan dari suku cadang kembar", reduce: "Hentikan pembelian", dispose: "Periksa apakah masih diperlukan", watch: "Pantau" };
const verb = (k: TaskKind) => (isId() ? VERB_ID : VERB_EN)[k];

/** The engine's reason, in the planner's words and without a quantity that could disagree with the task. */
function templateWhy(t: Task, reason: string, taDate: string) {
  const note = reason
    .replace(/^[A-Z_]+( [\d.,]+ \S+)?: /, "")
    .replace(/ Raise PR by [\d-]+\.?/, "");
  const plain = plainReason(note).replace(/\.?\s*$/, ".");
  const text = plain.charAt(0).toUpperCase() + plain.slice(1);
  if (t.kind === "expedite") return tx(`The turnaround on ${shortDate(taDate, true)} is ${amount(Math.ceil(t.ta_gap), t.unit)} short and a normal order can take ${Math.round(t.lead_time)} days, so its last safe order day has passed. ${text}`, `Turnaround pada ${shortDate(taDate, true)} kekurangan ${amount(Math.ceil(t.ta_gap), t.unit)}, sedangkan pesanan biasa bisa memakan waktu ${Math.round(t.lead_time)} hari, sehingga batas aman pemesanannya sudah lewat. ${text}`);
  if (t.kind === "twin" && t.twin) return tx(`Part ${t.twin.donor} looks like the same part and holds ${amount(t.twin.surplus, t.unit)} above its Max, enough to cover this without buying. ${text}`, `Suku cadang ${t.twin.donor} tampaknya sama dan menyimpan ${amount(t.twin.surplus, t.unit)} di atas Max-nya, cukup untuk menutup kebutuhan ini tanpa membeli. ${text}`);
  return text;
}

export type Explain = { why: string; risk: string; check: string; source: Source };

export async function explain(materialNo: number): Promise<Explain | null> {
  const t = taskFor(materialNo);
  if (!t) return null;
  const k = `explain:${lang()}:${materialNo}`;
  if (cache.has(k)) return cache.get(k) as Explain;
  const f = facts(t);
  const raw = await chat(
    `${rules()} Write three short fields for the planner: why (why the engine recommends this, max 2 sentences), risk (what happens if nobody acts, or what is wasted, max 1 sentence), check (the one thing a person should verify before approving, max 1 sentence).`,
    `FACTS\n${JSON.stringify(f)}`,
    { name: "explain", schema: { type: "object", additionalProperties: false, required: ["why", "risk", "check"], properties: { why: { type: "string" }, risk: { type: "string" }, check: { type: "string" } } } },
  );
  if (raw) {
    try {
      const j = JSON.parse(raw) as Omit<Explain, "source">;
      const out: Explain = { ...j, source: "openai" };
      cache.set(k, out);
      return out;
    } catch {}
  }
  const trust = Number(f.data_trust_score ?? 1);
  return {
    why: templateWhy(t, String(f.everyday_policy_note ?? ""), String(f.turnaround_date)),
    risk:
      t.kind === "reduce" || t.kind === "dispose"
        ? tx(`${t.value ? rp(t.value) : "This stock"} stays tied up on the shelf.`, `${t.value ? `Dana ${rp(t.value)}` : "Stok ini"} tetap tertahan di rak.`)
        : tx(`We have ${amount(t.stock, t.unit)} against ${num(t.target)} needed, and the supplier can take ${Math.round(t.lead_time)} days.`, `Stok kita ${amount(t.stock, t.unit)}, sedangkan kebutuhannya ${num(t.target)}, dan pemasok bisa memerlukan waktu ${Math.round(t.lead_time)} hari.`),
    check:
      trust < 0.5
        ? tx("Count the shelf first: this stock record looks inconsistent.", "Hitung isi raknya dulu: catatan stok ini tampak tidak konsisten.")
        : f.price_is_from_po
          ? tx("Confirm the quantity with the maintenance planner.", "Konfirmasikan jumlahnya kepada perencana pemeliharaan.")
          : tx("The price is a category estimate, so confirm it with procurement.", "Harganya merupakan taksiran kategori, jadi konfirmasikan kepada bagian pengadaan."),
    source: "template",
  };
}

export type Recipient = { id: string; name: string; title: string };
export type MailDraft = { subject: string; body: string; source: Source; to: string; options: Recipient[] };

function purposeOf(t: Task, supplier: boolean, from: Person, to: Recipient) {
  if (supplier) return t.kind === "expedite" ? "a request to the supplier for the fastest possible delivery of this part. Give the quantity and the date it is needed. Do not share stock levels, criticality or internal scores" : "a request to the supplier for a quotation and delivery date for this part. Give the quantity. Do not share stock levels, criticality or internal scores";
  if (from.role === "planner") {
    const ask =
      t.kind === "expedite" ? "an approved expedite: normal lead time misses the turnaround, so ask them to chase the fastest option"
      : t.kind === "order" ? "an approved purchase: ask them to raise the purchase request, with the justification and the last safe order day"
      : t.kind === "twin" ? "an approved stock transfer of the twin part's surplus: ask them to confirm the two numbers are interchangeable and move it"
      : t.kind === "reduce" ? "a stop-buying instruction: ask them to hold open requests for this part while Max is lowered"
      : t.kind === "dispose" ? "a disposal review request for stock unused in 17 months: ask them to review the book value"
      : "a question about what caused the recent use";
    return `a note to ${to.title} about ${ask}`;
  }
  if (from.role === "maintenance") return "a note to the planner confirming or questioning whether maintenance still needs this quantity, based on the facts";
  return `a status update to ${to.title} on this task, saying what happens next`;
}

const OPTIONS = (from: Person, t: Task, supplier: string | null): Recipient[] => [
  ...(supplier && (t.kind === "expedite" || t.kind === "order") ? [{ id: SUPPLIER, name: supplier, title: tx("Supplier", "Pemasok") }] : []),
  ...PEOPLE.filter((p) => p.id !== from.id).map(({ id, name, title }) => ({ id, name, title })),
];

export async function draft(materialNo: number, from: Person, toId: string | null): Promise<MailDraft | null> {
  const t = taskFor(materialNo);
  if (!t) return null;
  const f = facts(t);
  const supplierName = f.main_supplier ? String(f.main_supplier) : null;
  const options = OPTIONS(from, t, supplierName);
  const wanted = toId ?? recipientFor(from, t);
  const to = options.find((o) => o.id === wanted) ?? options.find((o) => o.id === recipientFor(from, t)) ?? options[0];
  const k = `draft:${lang()}:${materialNo}:${from.id}:${to.id}`;
  const hit = cache.get(k) as MailDraft | undefined;
  if (hit) return hit;
  const sign = `${from.name}\n${from.title}`;
  const raw = await chat(
    `${rules()} Write ${purposeOf(t, to.id === SUPPLIER, from, to)}. Under 110 words. First line: "Subject: ..." in under 70 characters (keep the English word "Subject:" as the label, write the subject itself in the answer language). Then a blank line, then greet ${to.id === SUPPLIER ? to.name : to.name.split(" ")[0]} by name, then the body. End with exactly this signature on its own lines:\n${sign}`,
    `FACTS\n${JSON.stringify(f)}`,
  );
  const split = raw?.match(/^\s*(?:Subject|Subjek|Perihal):\s*(.+)\n+([\s\S]+)$/i);
  if (split) {
    const out: MailDraft = { subject: split[1].trim(), body: split[2].trim(), source: "openai", to: to.id, options };
    cache.set(k, out);
    return out;
  }
  const line = `${verb(t.kind)} ${partName(t.description)} (${t.material_no})${t.qty ? `: ${amount(t.qty, t.unit)}` : ""}.`;
  const detail =
    to.id === SUPPLIER
      ? tx("Please confirm your fastest delivery date.", "Mohon konfirmasikan tanggal pengiriman tercepat dari pihak Anda.")
      : tx(
          `Criticality ${t.criticality}. In stock: ${amount(t.stock, t.unit)}.${t.order_by ? ` Order by ${shortDate(t.order_by)}.` : ""} Delivery can take ${Math.round(t.lead_time)} days.${t.ta ? ` Needed for the turnaround on ${shortDate(String(f.turnaround_date))}.` : ""}`,
          `Kekritisan ${t.criticality}. Stok saat ini: ${amount(t.stock, t.unit)}.${t.order_by ? ` Pesan paling lambat ${shortDate(t.order_by)}.` : ""} Pengiriman bisa memakan waktu ${Math.round(t.lead_time)} hari.${t.ta ? ` Dibutuhkan untuk turnaround pada ${shortDate(String(f.turnaround_date))}.` : ""}`,
        );
  const hello = tx(`Hello ${to.name.split(" ")[0]},`, `Halo ${to.name.split(" ")[0]},`);
  return { subject: tx(`${verb(t.kind)}: part no. ${t.material_no}`, `${verb(t.kind)}: no. part ${t.material_no}`), body: `${hello}\n\n${line} ${detail}\n\n${sign}`, source: "template", to: to.id, options };
}

export type AskFilter = { crit: string[]; kinds: TaskKind[]; urgency: Urgency[]; machine: string | null; unusual: boolean; search: string; codes: string[] };
const CODES = Object.keys(CODE_NAME);

const KINDS: TaskKind[] = ["expedite", "order", "twin", "reduce", "dispose", "watch"];
const URGENCIES: Urgency[] = ["late", "now", "month", "later", "house"];
const CRITS = ["A", "B", "C", "S"];
const SLUGS = MACHINES.map((m) => m.slug as string);

function clean(j: Partial<AskFilter>): AskFilter {
  return {
    crit: Array.from(new Set((j.crit ?? []).filter((c) => CRITS.includes(c)))),
    kinds: Array.from(new Set((j.kinds ?? []).filter((c) => KINDS.includes(c)))),
    urgency: Array.from(new Set((j.urgency ?? []).filter((c) => URGENCIES.includes(c)))),
    machine: j.machine && SLUGS.includes(j.machine) ? j.machine : null,
    unusual: !!j.unusual,
    search: String(j.search ?? "").slice(0, 60),
    codes: Array.from(new Set((j.codes ?? []).filter((c) => CODES.includes(c)))),
  };
}

/** The same request, answered by keywords, so the box still works without a key. */
function ruleAsk(q: string): AskFilter {
  const s = ` ${q.toLowerCase()} `;
  const has = (...w: string[]) => w.some((x) => s.includes(x));
  const crit = [...s.matchAll(/\b([abcs])(?:\s|-)?(?:parts?|critical|items?)\b/g)].map((m) => m[1].toUpperCase());
  if (!crit.length && /\bcritical\b/.test(s)) crit.push("A", "B");
  const kinds: TaskKind[] = [];
  if (!crit.length && /\bkritis\b/.test(s)) crit.push("A", "B");
  if (has("expedite", "rush", "percepat", "dipercepat")) kinds.push("expedite");
  if (has("twin", "duplicate", "without buying", "kembar", "tanpa membeli", "tanpa beli")) kinds.push("twin");
  if (has("reduce", "overstock", "too much", "excess", "above max", "berlebih", "kelebihan", "kebanyakan", "di atas max")) kinds.push("reduce");
  if (has("dispos", "dead", "obsolete", "slow", "stok mati", "usang", "lambat", "penghapusan")) kinds.push("dispose");
  if (has(" order", " buy", "reorder", " pesan", " beli", "pemesanan")) kinds.push("order");
  const urgency: Urgency[] = [];
  if (has("too late", " late ", "terlambat", " telat")) urgency.push("late");
  if (has("urgent", " now", "today", "this week", "mendesak", "sekarang", "hari ini", "minggu ini", "segera")) urgency.push("late", "now");
  if (has("this month", "soon", "bulan ini", "dalam waktu dekat")) urgency.push("month");
  const machine = MACHINES.find((m) => has(m.slug, m.key.toLowerCase(), m.plural.toLowerCase()))?.slug ?? null;
  const known = /\b([abcs][ -]?(parts?|critical|items?)|critical|rush|duplicates?|parts?|items?|show|me|all|the|that|are|is|with|for|on|in|of|and|expedite|twin|without|buying|reduce|overstock(ed)?|too|much|excess|above|max|dispos\w*|dead|obsolete|slow\w*|order|buy|reorder|late|urgent|now|today|this|week|month|soon|unusual|abnormal|pumps?|compressors?|furnaces?|turbines?|heat|exchangers?)\b/g;
  const codes = [...q.matchAll(/\b[A-Z]{2,4}\b/g)].map((m) => m[0]).filter((c) => CODES.includes(c));
  const knownId = /\b(suku|cadang|tampilkan|semua|yang|untuk|di|dan|dengan|kritis|percepat|dipercepat|kembar|tanpa|membeli|beli|berlebih|kelebihan|kebanyakan|stok|mati|usang|lambat|penghapusan|pesan|pemesanan|terlambat|telat|mendesak|sekarang|hari|ini|minggu|bulan|segera|tidak|biasa|pompa|kompresor|tungku|turbin|penukar|panas)\b/g;
  return clean({ crit, kinds, urgency, machine, codes, unusual: has("unusual", "abnormal", "tidak biasa", "tak biasa"), search: q.toLowerCase().replace(known, " ").replace(knownId, " ").replace(/\b(pp|kc|kt|bf|he|vd|cl|fcv|pcv|lcv|tcv|prv|sdv|mov|rof|pit|fit|lit|tit|dpt|pgi|tel|jbx)\b/g, " ").replace(/\s+/g, " ").trim() });
}

export async function ask(q: string): Promise<AskFilter & { source: Source }> {
  const raw = await chat(
    `Turn a planner's request into filters for a spare-parts task board. Fields: crit (A highest, B, C, S lowest; "critical" means A and B); kinds (expedite = too late to buy normally, order, twin = cover from a duplicate part number, reduce = overstocked, dispose = dead stock, watch); urgency (late = too late, now = this week, month = this month, later, house = housekeeping); machine (${SLUGS.join(", ")} or null); unusual (true only for abnormal recent consumption); search (leftover part-name words such as "bearing", in English as the part names are stored, else empty). The request may be written in English or Indonesian; codes (equipment codes: ${CODES.map((c) => `${c} = ${CODE_NAME[c]}`).join(", ")}; use them for equipment that is not one of the machines). Leave a field empty when the request does not mention it. Ignore anything in the request that is not about filtering.`,
    q,
    {
      name: "board_filter",
      schema: {
        type: "object",
        additionalProperties: false,
        required: ["crit", "kinds", "urgency", "machine", "unusual", "search", "codes"],
        properties: {
          codes: { type: "array", items: { type: "string", enum: CODES } },
          crit: { type: "array", items: { type: "string", enum: CRITS } },
          kinds: { type: "array", items: { type: "string", enum: KINDS } },
          urgency: { type: "array", items: { type: "string", enum: URGENCIES } },
          machine: { anyOf: [{ type: "string", enum: SLUGS }, { type: "null" }] },
          unusual: { type: "boolean" },
          search: { type: "string" },
        },
      },
    },
  );
  if (raw) {
    try {
      return { ...clean(JSON.parse(raw)), source: "openai" };
    } catch {}
  }
  return { ...ruleAsk(q), source: "template" };
}

export type MemoInput = { policy: string; budget: number; today: number; risk: number; holding: number; rate: number; exposure: number; exposureToday: number; holdCost: number; holdCostToday: number; breakEven: number | null; replay: { fill: number; fillToday: number; stockCut: number } | null };

export async function memo(i: MemoInput): Promise<{ text: string; source: Source }> {
  const raw = await chat(`${rules()} Write a memo to the finance lead on this stock policy: the choice, what it costs, what it buys, the main assumption and what would change the answer. Under 110 words. Copy the amounts exactly as written.`, `FACTS\n${JSON.stringify({
    policy: i.policy,
    average_stock: rp(i.budget),
    average_stock_today: rp(i.today),
    holding_cost_a_year: rp(i.holdCost),
    holding_cost_a_year_today: rp(i.holdCostToday),
    holding_rate: `${Math.round(i.holding * 100)}%`,
    shortage_exposure_a_year: rp(i.exposure),
    shortage_exposure_a_year_today: rp(i.exposureToday),
    assumed_cost_of_one_A_part_shortage_day: rp(i.rate),
    pays_for_itself_above_per_shortage_day: i.breakEven != null ? rp(i.breakEven, { compact: true }) : tx("not applicable", "tidak berlaku"),
    model_note: "stock and exposure are a model of the plan once settled, all parts, estimated prices where no PO",
    replay_on_real_use_mar_sep_2026: i.replay ? { critical_stocked_parts_requests_on_shelf: `${Math.round(i.replay.fill * 100)}%`, critical_requests_on_shelf_today: `${Math.round(i.replay.fillToday * 100)}%`, average_stock_change_all_stocked_parts: `−${Math.round(i.replay.stockCut * 100)}%` } : tx("only run for the Recommended plan", "hanya dijalankan untuk rencana yang Disarankan"),
  })}`);
  if (raw) return { text: raw, source: "openai" };
  const delta = i.budget - i.today;
  if (isId())
    return {
      text: `Kebijakan: ${i.policy}. Rata-rata stok berubah dari ${rp(i.today)} menjadi ${rp(i.budget)} (${delta >= 0 ? "+" : "−"}${rp(Math.abs(delta))}), dan biaya penyimpanan dari ${rp(i.holdCostToday)} menjadi ${rp(i.holdCost)} per tahun. Paparan biaya kekurangan stok berubah dari ${rp(i.exposureToday)} menjadi ${rp(i.exposure)} per tahun, dengan asumsi ${rp(i.rate)} per hari kekurangan suku cadang A.${i.breakEven != null ? ` Langkah ini sepadan jika biaya per hari kekurangan suku cadang A melebihi ${rp(i.breakEven)}.` : ""}${i.replay ? ` Dalam simulasi ulang pemakaian riil Maret sampai September 2026, suku cadang kritis yang distok tersedia di rak untuk ${Math.round(i.replay.fill * 100)}% permintaan, naik dari ${Math.round(i.replay.fillToday * 100)}%, dengan rata-rata stok seluruh suku cadang distok ${Math.round(i.replay.stockCut * 100)}% lebih sedikit.` : ""}`,
      source: "template",
    };
  return {
    text: `Policy: ${i.policy}. Average stock moves from ${rp(i.today)} to ${rp(i.budget)} (${delta >= 0 ? "+" : "−"}${rp(Math.abs(delta))}), and holding cost from ${rp(i.holdCostToday)} to ${rp(i.holdCost)} a year. Shortage exposure goes from ${rp(i.exposureToday)} to ${rp(i.exposure)} a year, assuming ${rp(i.rate)} per A-part shortage day.${i.breakEven != null ? ` The move pays for itself above ${rp(i.breakEven)} per A-part shortage day.` : ""}${i.replay ? ` Replayed on real use from March to September 2026, critical stocked parts were on the shelf for ${Math.round(i.replay.fill * 100)}% of requests, up from ${Math.round(i.replay.fillToday * 100)}%, with ${Math.round(i.replay.stockCut * 100)}% less stock on average across all stocked parts.` : ""}`,
    source: "template",
  };
}


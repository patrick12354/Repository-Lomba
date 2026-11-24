"use client";

import { useCallback, useEffect, useMemo, useState, type FormEvent, type ReactNode } from "react";
import { useSearchParams } from "next/navigation";
import { AnimatePresence, LayoutGroup, motion } from "motion/react";
import * as Popover from "@radix-ui/react-popover";
import { ArrowRight, ChevronsLeft, Loader2, Mail, Plus, X } from "lucide-react";
import { Activity, ArrowLeftRight, CalendarDays, CheckCheck, Grid3x3, Lightbulb, ListFilter, ListTodo, Route, Search, Truck } from "@/components/icons";
import type { Task, TaskKind, Urgency } from "@/lib/data";
import { useDecisions } from "@/lib/decisions";
import { useMe } from "@/lib/me";
import { MACHINES } from "@/lib/machines";
import { buyBasis, buyNote, buySplit, canMove, CODE_NAME, codeSection, firstName, isMine, ownerOf, recipientFor, SECTION_NAME, SECTIONS, type Person, type Section } from "@/lib/people";
import { cn, num, partName, amount, qty, rp, shortDate } from "@/lib/format";
import { DropGap, FLOW_SPRING, LiftedCard, useBoardDrag } from "./board-drag";
import { Chip, Panel, SevBar, sevOf, STATUS_TONE, type Severity } from "./ui";
import { Hint } from "./hint";
import { KIND, KINDS, nextStep, setStatus, STATUSES, URGENCIES, type TaskStatus } from "./todo-shared";
import { emailLabel, TaskPeek } from "./task-peek";
import { Compose, type ComposeRequest } from "./compose";
import { RejectDialog, type RejectWhy } from "./reject-dialog";
import { AiBrief } from "./ai-brief";
import { isId, t as tx } from "@/lib/i18n";

type Filter = { q: string; crit: string[]; kinds: TaskKind[]; urgency: Urgency[]; machine: string | null; unusual: boolean; codes: string[]; section: Section | null };
const EMPTY: Filter = { q: "", crit: [], kinds: [], urgency: [], machine: null, unusual: false, codes: [], section: null };
type Group = "status" | "urgency" | "action" | "code";
type Sort = "urgency" | "money" | "name";
const PAGE = 30;

const q = (key: string, en: string, id: string, filter: Partial<Filter>) => ({ key, get label() { return tx(en, id); }, filter });
const QUICK: { key: string; label: string; filter: Partial<Filter> }[] = [
  q("all", "All", "Semua", {}),
  q("urgent", "Urgent", "Mendesak", { urgency: ["late", "now"] }),
  q("buy", "To buy", "Perlu dibeli", { kinds: ["expedite", "order"] }),
  q("twin", "Fix without buying", "Atasi tanpa membeli", { kinds: ["twin"] }),
  q("cash", "Free the cash", "Bebaskan dana", { kinds: ["reduce", "dispose"] }),
  q("unusual", "Unusual use", "Pemakaian tidak biasa", { unusual: true }),
];

function fromUrl(sp: URLSearchParams): Filter {
  const list = (k: string) => sp.get(k)?.split(",").filter(Boolean) ?? [];
  const f: Filter = { ...EMPTY, crit: list("crit"), kinds: list("kind") as TaskKind[], urgency: list("urgency") as Urgency[], machine: sp.get("machine"), q: sp.get("q") ?? sp.get("open") ?? "", codes: list("code") };
  const quick = QUICK.find((v) => v.key === sp.get("view"));
  return quick ? { ...f, ...quick.filter } : f;
}

const same = (a: Filter, b: Partial<Filter>) => {
  const n = { ...EMPTY, ...b };
  return a.q === n.q && a.machine === n.machine && a.unusual === n.unusual && a.section === n.section && a.codes.join() === n.codes.join() && a.crit.join() === n.crit.join() && a.kinds.join() === n.kinds.join() && a.urgency.join() === n.urgency.join();
};

/** A part is in a section when any of its equipment codes is. */
function inCodes(t: Task, f: Pick<Filter, "codes" | "section">) {
  if (f.codes.length) return t.codes.some((c) => f.codes.includes(c));
  return !f.section || t.codes.some((c) => codeSection(c) === f.section);
}

function matches(t: Task, f: Filter) {
  if (f.crit.length && !f.crit.includes(t.criticality)) return false;
  if (f.kinds.length && !f.kinds.includes(t.kind)) return false;
  if (f.urgency.length && !f.urgency.includes(t.urgency)) return false;
  if (f.machine && !t.machines.includes(f.machine)) return false;
  if (f.unusual && !t.unusual) return false;
  if (!inCodes(t, f)) return false;
  const w = f.q.trim().toLowerCase().split(/\s+/).filter(Boolean);
  if (w.length) {
    const hay = `${t.description} ${t.material_no} ${t.equipment.join(" ")}`.toLowerCase();
    if (!w.every((x) => hay.includes(x))) return false;
  }
  return true;
}

type Col = { code: string; label: string; dot: string; items: Task[]; hint?: string; who?: string };

export function TodoBoard({ counts }: { counts: { total: number; urgent: number; toBuy: number; toFree: number; buy: ReturnType<typeof buySplit> } }) {
  const sp = useSearchParams();
  const d = useDecisions();
  const { me } = useMe();
  const [scope, setScope] = useState<"mine" | "all">("mine");
  const [compose, setCompose] = useState<ComposeRequest | null>(null);
  const [rejecting, setRejecting] = useState<Task | null>(null);
  const [toast, setToast] = useState<{ text: string; undo?: () => void } | null>(null);
  // Cards only glide when someone moves one. Loading or filtering a long list should not set them all flying.
  const [flow, setFlow] = useState(false);
  useEffect(() => {
    if (!flow) return;
    const id = window.setTimeout(() => setFlow(false), 700);
    return () => window.clearTimeout(id);
  }, [flow]);
  const [all, setAll] = useState<Task[] | null>(null);
  const [failed, setFailed] = useState(false);
  const [filter, setFilter] = useState<Filter>(() => fromUrl(new URLSearchParams(sp.toString())));
  const [view, setView] = useState<"board" | "table">("board");
  const [group, setGroup] = useState<Group>("status");
  const [sort, setSort] = useState<Sort>("urgency");
  const [peek, setPeek] = useState<string | null>(() => sp.get("open"));
  const [showRejected, setShowRejected] = useState(false);
  const [collapsed, setCollapsed] = useState<string[]>([]);
  const [limits, setLimits] = useState<Record<string, number>>({});
  const [ask, setAsk] = useState("");
  const [asking, setAsking] = useState(false);
  const [askNote, setAskNote] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/tasks")
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(String(r.status)))))
      .then((j: { tasks: Task[] }) => setAll(j.tasks))
      .catch(() => setFailed(true));
  }, []);
  useEffect(() => {
    try {
      const raw = JSON.parse(localStorage.getItem("sk-board") ?? "null");
      if (raw) {
        /* eslint-disable react-hooks/set-state-in-effect */
        if (raw.view) setView(raw.view);
        if (raw.group) setGroup(raw.group);
        /* eslint-enable react-hooks/set-state-in-effect */
      }
    } catch {
      /* the defaults are fine */
    }
  }, []);
  useEffect(() => {
    try {
      localStorage.setItem("sk-board", JSON.stringify({ view, group }));
    } catch {
      /* not remembered this time */
    }
  }, [view, group]);

  // The planner decides thousands of parts, so their board opens on what cannot wait.
  const opening = sp.toString() === "" && me?.role === "planner";
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    if (opening) setFilter((f) => (same(f, {}) ? { ...EMPTY, urgency: ["late", "now"] } : f));
  }, [opening]);

  useEffect(() => {
    if (!toast) return;
    const id = window.setTimeout(() => setToast(null), 5000);
    return () => window.clearTimeout(id);
  }, [toast]);

  const statusOf = useCallback((t: Task) => (d.map[t.id] ?? "todo") as TaskStatus, [d.map]);
  const scoped = useMemo(() => (all ?? []).filter((t) => scope === "all" || !me || isMine(me, t, statusOf(t))), [all, scope, me, statusOf]);

  const list = useMemo(() => {
    const r = scoped.filter((t) => matches(t, filter));
    if (sort === "money") return [...r].sort((a, b) => (b.value ?? 0) - (a.value ?? 0));
    if (sort === "name") return [...r].sort((a, b) => partName(a.description).localeCompare(partName(b.description)));
    return r;
  }, [scoped, filter, sort]);

  /** How many tasks each code would show, with every other filter applied. */
  const codeCounts = useMemo(() => {
    const out = new Map<string, number>();
    for (const t of scoped) {
      if (!matches(t, { ...filter, codes: [], section: null })) continue;
      for (const c of t.codes) out.set(c, (out.get(c) ?? 0) + 1);
    }
    return Array.from(out, ([code, n]) => ({ code, n })).sort((a, b) => b.n - a.n);
  }, [scoped, filter]);

  const moveTo = useCallback(
    (t: Task, to: TaskStatus) => {
      const from = statusOf(t);
      if (from === to) return;
      if (!canMove(me, t, from, to)) {
        const who = from === "todo" || to === "todo" || to === "rejected" ? tx("the planner, Nadia Putri", "perencana, Nadia Putri") : ownerOf(t).name;
        setToast({ text: tx(`Only ${t.kind === "watch" ? ownerOf(t).name : who} can make this move.`, `Hanya ${t.kind === "watch" ? ownerOf(t).name : who} yang bisa memindahkan ini.`) });
        return;
      }
      if (to === "rejected") {
        setRejecting(t);
        return;
      }
      setFlow(true);
      setStatus(d, t, to);
      const label = STATUSES.find((s) => s.code === to)?.label;
      setToast({ text: tx(`${partName(t.description)} moved to ${label}`, `${partName(t.description)} dipindahkan ke ${label}`), undo: canMove(me, t, to, from) ? () => { setStatus(d, t, from); setToast(null); } : undefined });
    },
    [d, me, statusOf],
  );
  const email = useCallback(
    (t: Task, advance?: TaskStatus) => {
      if (!me) return;
      const heading = advance === "approved" ? tx(`Approve and ${emailLabel(me, t).replace(/^Email/, "email")}`, `Setujui dan kirim ${emailLabel(me, t).replace(/^Surel/, "surel")}`) : advance === "in_progress" ? tx("Request a quote and start", "Minta penawaran dan mulai") : emailLabel(me, t);
      setCompose({ kind: "task", materialNo: t.material_no, to: recipientFor(me, t), heading, advance: advance === "approved" || advance === "in_progress" ? advance : undefined, action: t.kind });
    },
    [me],
  );

  const columns = useMemo<Col[]>(() => {
    if (group === "status") {
      return STATUSES.filter((s) => s.code !== "rejected" || showRejected).map((s) => ({ code: s.code, label: s.label, dot: s.dot, hint: s.hint, who: s.who, items: list.filter((t) => statusOf(t) === s.code) }));
    }
    const open = list.filter((t) => statusOf(t) === "todo");
    if (group === "urgency") return URGENCIES.map((u) => ({ code: u.code, label: u.label, dot: u.dot, items: open.filter((t) => t.urgency === u.code) }));
    if (group === "action") return KINDS.map((k) => ({ code: k, label: KIND[k].name, dot: KIND[k].dot, items: open.filter((t) => t.kind === k) }));
    const byCode = new Map<string, Task[]>();
    for (const t of open) {
      const c = t.codes[0] ?? "OTHER";
      byCode.set(c, [...(byCode.get(c) ?? []), t]);
    }
    return Array.from(byCode, ([code, items]) => ({ code, label: CODE_NAME[code] ?? code, dot: "bg-accent", items })).sort((a, b) => b.items.length - a.items.length);
  }, [group, list, showRejected, statusOf]);

  const drop = useCallback(
    (id: string, to: string) => {
      const t = all?.find((x) => x.id === id);
      if (t) moveTo(t, to as TaskStatus);
    },
    [all, moveTo],
  );
  const dragCols = useMemo(() => columns.map((c) => ({ code: c.code, label: c.label })), [columns]);
  const { lifted, carried, target, source, x, y, trackRef, cardProps, consumeDrag, announce } = useBoardDrag({ columns: dragCols, onDrop: drop });
  const movable = group === "status";

  const activeCount = filter.crit.length + filter.kinds.length + filter.urgency.length + (filter.machine ? 1 : 0) + (filter.unusual ? 1 : 0) + filter.codes.length + (filter.section ? 1 : 0);
  const openId = sp.get("open");
  const nextUp = (all ? scoped : []).filter((t) => {
    const s = statusOf(t);
    const st = nextStep(t, s);
    return !!st && s !== "done" && s !== "rejected" && canMove(me, t, s, st.to);
  }).slice(0, 3);
  const head = all
    ? {
        total: scoped.length,
        urgent: scoped.filter((t) => t.urgency === "late" || t.urgency === "now").length,
        toBuy: scoped.filter((t) => t.kind === "order" || t.kind === "expedite").reduce((a, t) => a + (t.value ?? 0), 0),
        toFree: scoped.filter((t) => t.kind === "reduce" || t.kind === "dispose").reduce((a, t) => a + (t.value ?? 0), 0),
        buy: buySplit(scoped),
      }
    : counts;
  const peeked = peek ? all?.find((t) => t.id === peek) ?? null : null;
  const closePeek = useCallback(() => setPeek(null), []);
  const open = useCallback((id: string) => setPeek(id), []);

  const submitAsk = (e: FormEvent) => {
    e.preventDefault();
    const q = ask.trim();
    if (!q) return;
    setAsking(true);
    setAskNote(null);
    fetch("/api/ai/ask", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ q }) })
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(String(r.status)))))
      .then((j: { crit: string[]; kinds: TaskKind[]; urgency: Urgency[]; machine: string | null; unusual: boolean; search: string; codes: string[]; source: string }) => {
        setFilter({ ...EMPTY, q: j.search, crit: j.crit, kinds: j.kinds, urgency: j.urgency, machine: j.machine, unusual: j.unusual, codes: j.codes });
        setAskNote(j.source === "openai" ? tx("Filtered by AI", "Disaring oleh AI") : tx("Filtered by keywords, AI is off", "Disaring dengan kata kunci, AI tidak aktif"));
      })
      .catch(() => setAskNote(tx("Could not read that. Try the filters.", "Permintaan tidak terbaca. Coba gunakan filter.")))
      .finally(() => setAsking(false));
  };

  return (
    <div className="flex h-[calc(100dvh-132px)] min-h-[640px] flex-col gap-3">
      <header className="flex shrink-0 items-end justify-between gap-6">
        <div className="min-w-0">
          <h1 className="m-0 text-[28px] font-semibold leading-[1.15] tracking-[-0.02em]">{me && scope === "mine" ? tx(`${firstName(me)}'s work`, `Pekerjaan ${firstName(me)}`) : tx("All work", "Semua pekerjaan")}</h1>
          <p className="m-0 mt-1 text-[14px] text-ink-2">
            {me && scope === "mine" && <span className="text-ink-3">{me.title} · </span>}
            {tx(
              <><b className="font-semibold text-act-ink">{num(head.urgent)}</b> urgent out of {num(head.total)} parts that need a decision · <b className="font-semibold">{rp(head.toBuy)}</b> of suggested buying <Hint>{`${rp(head.buy.stocked.value)} for parts kept in stock. ${rp(head.buy.job.value)} for Non Stock parts the next turnaround needs. ${rp(head.buy.ahead.value)} for Non Stock parts the forecast expects to be used: those are bought per job today, so holding them means moving them to Stock first, and the plant decides that. Only parts with a PO price are counted.`}</Hint> · <b className="font-semibold">{rp(head.toFree)}</b> above our new Max, to release</>,
              <><b className="font-semibold text-act-ink">{num(head.urgent)}</b> mendesak dari {num(head.total)} suku cadang yang perlu diputuskan · usulan pembelian <b className="font-semibold">{rp(head.toBuy)}</b> <Hint>{`${rp(head.buy.stocked.value)} untuk suku cadang yang distok. ${rp(head.buy.job.value)} untuk suku cadang Non Stock yang dibutuhkan turnaround berikutnya. ${rp(head.buy.ahead.value)} untuk suku cadang Non Stock yang menurut prakiraan akan terpakai: saat ini dibeli per pekerjaan, jadi menyimpannya berarti memindahkannya ke Stock lebih dulu, dan keputusan itu ada di kilang. Hanya suku cadang berharga PO yang dihitung.`}</Hint> · <b className="font-semibold">{rp(head.toFree)}</b> di atas Max baru kami, bisa dilepas</>,
            )}
            {me?.role === "planner" && (
              <>
                {" "}· <button type="button" onClick={d.clear} className="text-ink-3 underline underline-offset-2 hover:text-ink">{tx("Reset demo", "Atur ulang demo")}</button>
              </>
            )}
          </p>
        </div>
        <div className="flex shrink-0 items-center gap-2">
        <div data-tour="scope" role="radiogroup" aria-label={tx("Whose work", "Pekerjaan siapa")} className="flex h-9 rounded-[10px] bg-ink/[0.05] p-0.5 text-[13px]">
          {([["mine", tx("My work", "Pekerjaan saya")], ["all", tx("Everyone", "Semua orang")]] as const).map(([k, label]) => (
            <button key={k} type="button" role="radio" aria-checked={scope === k} onClick={() => setScope(k)} className={cn("rounded-[8px] px-3 transition-colors", scope === k ? "bg-panel font-medium shadow-card" : "text-ink-3 hover:text-ink")}>{label}</button>
          ))}
        </div>
        <AiBrief page="todo" />
        <Popover.Root>
          <Popover.Trigger asChild>
            <button type="button" data-tour="sap" className="inline-flex h-9 shrink-0 items-center gap-2 rounded-[10px] border border-line bg-panel px-3 text-[13px] font-medium transition-colors hover:border-line-2">
              <Route aria-hidden className="h-4 w-4" />{tx("Send to SAP", "Kirim ke SAP")}
            </button>
          </Popover.Trigger>
          <Popover.Portal>
            <Popover.Content align="end" sideOffset={6} className="z-40 w-[320px] rounded-[14px] border border-line bg-panel p-1.5 shadow-float">
              <a href="/api/export?type=mm17" download className="block rounded-[10px] px-3 py-2 transition-colors hover:bg-ink/[0.04]">
                <span className="block text-[13px] font-medium">{tx("New stock limits (file for SAP)", "Batas stok baru (berkas untuk SAP)")}</span>
                <span className="block text-[12px] leading-snug text-ink-3">{tx("Every part whose Min or Max changed, ready for SAP's bulk update screen (MM17).", "Semua suku cadang yang Min atau Max-nya berubah, siap untuk layar pembaruan massal SAP (MM17).")}</span>
              </a>
              <a href="/api/export?type=pr" download className="block rounded-[10px] px-3 py-2 transition-colors hover:bg-ink/[0.04]">
                <span className="block text-[13px] font-medium">{tx("Draft purchase requests (file for SAP)", "Draf permintaan pembelian (berkas untuk SAP)")}</span>
                <span className="block text-[12px] leading-snug text-ink-3">{tx("Only the orders and rush orders you have approved.", "Hanya pesanan dan pesanan percepatan yang sudah Anda setujui.")}</span>
              </a>
              <a href="/api/export?type=stock" download className="block rounded-[10px] px-3 py-2 transition-colors hover:bg-ink/[0.04]">
                <span className="block text-[13px] font-medium">{tx("Non Stock parts on the buying list (file)", "Suku cadang Non Stock dalam daftar beli (berkas)")}</span>
                <span className="block text-[12px] leading-snug text-ink-3">{tx("Which ones to move to Stock, with the Min and Max they would need. The plant decides.", "Yang perlu dipindahkan ke Stock, beserta Min dan Max yang dibutuhkan. Keputusan ada di kilang.")}</span>
              </a>
            </Popover.Content>
          </Popover.Portal>
        </Popover.Root>
        </div>
      </header>

      <div className="flex shrink-0 items-center gap-2">
        <form data-tour="ask" onSubmit={submitAsk} className="flex h-10 min-w-0 flex-1 items-center gap-2 rounded-[12px] border border-line bg-panel pl-3 pr-1.5 focus-within:border-line-2">
          <Lightbulb aria-hidden className="h-4 w-4 shrink-0" />
          <label className="sr-only" htmlFor="ask-board">{tx("Ask the board", "Tanya papan tugas")}</label>
          <input id="ask-board" value={ask} onChange={(e) => setAsk(e.target.value)} maxLength={200} placeholder={tx("Ask in your own words: critical compressor parts that are too late", "Tanyakan dengan kata-kata Anda sendiri: suku cadang kompresor kritis yang terlambat")} className="min-w-0 flex-1 bg-transparent text-[13.5px] outline-none placeholder:text-ink-4" />
          {askNote && <span className="shrink-0 text-[12px] text-ink-3">{askNote}</span>}
          <button type="submit" disabled={asking || !ask.trim()} className="inline-flex h-7 shrink-0 items-center gap-1.5 rounded-[8px] bg-ink px-2.5 text-[12.5px] font-medium text-white transition-opacity disabled:opacity-40">
            {asking && <Loader2 aria-hidden className="h-3.5 w-3.5 animate-spin" />}
            {tx("Ask", "Tanya")}
          </button>
        </form>
        {openId && filter.q === openId && (
          <button type="button" onClick={() => setFilter({ ...filter, q: "" })} className="inline-flex h-10 shrink-0 items-center gap-1.5 rounded-[12px] bg-accent-soft px-3 text-[13px] text-accent">
            {tx("Showing 1 part", "Menampilkan 1 suku cadang")}<span className="font-medium underline underline-offset-2">{tx("Show all", "Tampilkan semua")}</span>
          </button>
        )}
        <label className="flex h-10 w-[240px] shrink-0 items-center gap-2 rounded-[12px] border border-line bg-panel px-3 text-[13px] focus-within:border-line-2">
          <Search aria-hidden className="h-4 w-4 shrink-0 text-ink-3" />
          <span className="sr-only">{tx("Search tasks", "Cari tugas")}</span>
          <input value={filter.q} onChange={(e) => setFilter({ ...filter, q: e.target.value })} placeholder={tx("Part name or number", "Nama atau nomor suku cadang")} className="min-w-0 flex-1 bg-transparent outline-none placeholder:text-ink-4" />
          {filter.q && (
            <button type="button" aria-label={tx("Clear search", "Hapus pencarian")} onClick={() => setFilter({ ...filter, q: "" })} className="text-ink-3 hover:text-ink">
              <X aria-hidden className="h-3.5 w-3.5" />
            </button>
          )}
        </label>
      </div>

      <div className="flex shrink-0 items-center gap-1 border-b border-line">
        <div role="tablist" aria-label={tx("View", "Tampilan")} className="flex">
          {([["board", tx("Board", "Papan"), Grid3x3], ["table", tx("Table", "Tabel"), ListTodo]] as const).map(([v, label, Icon]) => (
            <button key={v} type="button" role="tab" aria-selected={view === v} onClick={() => setView(v)} className={cn("relative inline-flex h-9 items-center gap-1.5 px-2.5 text-[13px] transition-colors", view === v ? "font-medium text-ink" : "text-ink-3 hover:text-ink")}>
              <Icon aria-hidden className="h-4 w-4" />
              {label}
              {view === v && <motion.span layoutId="todo-tab" aria-hidden className="absolute inset-x-1.5 -bottom-px h-0.5 rounded-full bg-ink" />}
            </button>
          ))}
        </div>
        <span className="mx-2 h-4 w-px bg-line-2" aria-hidden />
        <div className="no-scrollbar flex min-w-0 flex-1 items-center gap-1 overflow-x-auto">
          {QUICK.map((v) => {
            const on = same(filter, v.filter);
            return (
              <button key={v.key} type="button" aria-pressed={on} onClick={() => { setFilter({ ...EMPTY, ...v.filter }); setAskNote(null); setLimits({}); }} className={cn("h-7 shrink-0 whitespace-nowrap rounded-full px-2.5 text-[12.5px] transition-colors", on ? "bg-ink font-medium text-white" : "text-ink-2 hover:bg-ink/[0.05]")}>
                {v.label}
              </button>
            );
          })}
        </div>
        <div className="flex shrink-0 items-center gap-1.5 pb-1">
          <span data-tour="codes"><FilterMenu filter={filter} onChange={setFilter} active={activeCount} codes={codeCounts} /></span>
          {view === "board" && (
            <Picker label={tx("Group by", "Kelompokkan")} value={group} onChange={(v) => { setGroup(v as Group); setLimits({}); }} options={[["status", "Status"], ["urgency", tx("Urgency", "Tingkat urgensi")], ["action", tx("Action", "Tindakan")], ["code", tx("Equipment", "Peralatan")]]} />
          )}
          <Picker label={tx("Sort", "Urutkan")} value={sort} onChange={(v) => setSort(v as Sort)} options={[["urgency", tx("Urgency", "Urgensi")], ["money", tx("Money", "Nilai uang")], ["name", "A–Z"]]} />
        </div>
      </div>

      {nextUp.length > 0 && (
        <div className="flex shrink-0 items-center gap-2">
          <span className="flex shrink-0 items-center gap-1 text-[12.5px] font-semibold">{tx("Your next steps", "Langkah Anda berikutnya")}<Hint>{tx("The most urgent tasks where the next step is yours. Press one to open it with the reason and a ready email.", "Tugas paling mendesak yang langkah berikutnya ada di tangan Anda. Tekan salah satunya untuk membukanya, lengkap dengan alasan dan surel yang siap dikirim.")}</Hint></span>
          <div className="grid min-w-0 flex-1 grid-cols-3 gap-2">
            {nextUp.map((t) => {
              const st = nextStep(t, statusOf(t));
              return (
                <button key={t.id} type="button" onClick={() => open(t.id)} className="relative flex min-w-0 items-center gap-2 rounded-[10px] border border-line bg-panel py-1.5 pl-3.5 pr-2.5 text-left transition-colors hover:border-line-2">
                  <SevBar sev={taskSev(t)} className="inset-y-2 left-1" />
                  <span className="min-w-0 flex-1">
                    <span className="block truncate text-[12.5px] font-medium">{partName(t.description)}</span>
                    <span className="block truncate text-[11.5px] text-ink-3">{KIND[t.kind].label(t)} · {st?.label}</span>
                  </span>
                  <ArrowRight aria-hidden className="h-3.5 w-3.5 shrink-0 text-ink-4" />
                </button>
              );
            })}
          </div>
        </div>
      )}

      {failed ? (
        <Panel className="grid flex-1 place-items-center text-[13.5px] text-ink-3">{tx("Could not load the tasks. Refresh the page.", "Tugas gagal dimuat. Muat ulang halaman.")}</Panel>
      ) : !all ? (
        <div className="grid flex-1 grid-cols-4 gap-3" aria-label={tx("Loading tasks", "Memuat tugas")}>
          {[0, 1, 2, 3].map((i) => <div key={i} className="animate-pulse rounded-[16px] bg-ink/[0.04]" />)}
        </div>
      ) : view === "table" ? (
        <TaskTable tasks={list} statusOf={statusOf} onOpen={open} me={me} onMove={moveTo} />
      ) : (
        <div className="relative min-h-0 flex-1">
          <div ref={trackRef} className="flex h-full items-stretch gap-3 overflow-x-auto pb-1">
            <LayoutGroup>
              {columns.map((c) => {
                const isTarget = movable && target === c.code && source !== c.code;
                const isCollapsed = collapsed.includes(c.code);
                const items = c.items.filter((t) => t.id !== lifted?.id);
                const limit = limits[c.code] ?? PAGE;
                const toggle = () => setCollapsed((cs) => (cs.includes(c.code) ? cs.filter((x) => x !== c.code) : [...cs, c.code]));
                if (isCollapsed) {
                  return (
                    <section key={c.code} aria-label={c.label} data-board-col={c.code} className={cn("w-11 shrink-0 rounded-[16px] bg-ink/[0.035] transition-colors", isTarget && "bg-accent-soft ring-2 ring-accent/40")}>
                      <button type="button" onClick={toggle} aria-expanded={false} title={tx(`Expand ${c.label}`, `Bentangkan ${c.label}`)} className="flex h-full w-full flex-col items-center gap-2 rounded-[16px] px-1 py-3 text-[13px] font-semibold hover:bg-ink/[0.03]">
                        <span aria-hidden className={cn("h-2 w-2 shrink-0 rounded-full", c.dot)} />
                        <span className="text-[11.5px] tabular-nums text-ink-3">{num(c.items.length)}</span>
                        <span className="[writing-mode:vertical-rl]">{c.label}</span>
                      </button>
                    </section>
                  );
                }
                return (
                  <section key={c.code} aria-label={c.label} data-board-col={c.code} className={cn("flex min-w-[264px] flex-1 basis-0 flex-col rounded-[16px] bg-ink/[0.035] p-2 transition-colors duration-150", isTarget && "bg-accent-soft/70 ring-2 ring-accent/30")}>
                    <h2 className="m-0 shrink-0">
                      <button type="button" onClick={toggle} aria-expanded title={tx(`Collapse ${c.label}`, `Ciutkan ${c.label}`)} className="group/col flex h-8 w-full items-center gap-2 rounded-[8px] px-1.5 text-left text-[13px] font-semibold">
                        <span aria-hidden className={cn("h-2 w-2 shrink-0 rounded-full", c.dot)} />
                        <span className="truncate">{c.label}</span>
                        <span className="grid h-5 min-w-5 place-items-center rounded-[6px] bg-ink/[0.06] px-1.5 text-[11.5px] font-medium tabular-nums text-ink-2">{num(c.items.length)}</span>
                        <ChevronsLeft aria-hidden className="ml-auto h-3.5 w-3.5 text-ink-3 opacity-0 transition-opacity group-hover/col:opacity-100" />
                      </button>
                      {c.who && <span className="block px-1.5 pb-0.5 text-[11.5px] font-normal text-ink-3">{c.who}</span>}
                    </h2>
                    <div className="mt-1 flex min-h-0 flex-1 flex-col gap-2 overflow-y-auto pb-1 pr-0.5">
                      {items.slice(0, limit).map((t) => (
                        <TaskCard key={t.id} flow={flow} t={t} me={me} status={statusOf(t)} emailed={!!d.emailed[t.id]} showStatus={group !== "status"} carried={carried?.id === t.id} dragProps={movable ? cardProps(t.id, c.code, partName(t.description)) : undefined} consumeDrag={consumeDrag} onOpen={open} onMove={moveTo} onEmail={email} selected={peek === t.id} />
                      ))}
                      <AnimatePresence>{isTarget && lifted && <DropGap key="gap" height={lifted.height} />}</AnimatePresence>
                      {items.length === 0 && !isTarget && (
                        <div className="flex flex-col items-center gap-2 rounded-[12px] border border-dashed border-line-2 px-3 py-6 text-center text-[12.5px] leading-snug text-ink-3">
                          <CheckCheck aria-hidden className="h-6 w-6" />
                          {c.hint ?? tx("Nothing here.", "Belum ada apa-apa di sini.")}
                        </div>
                      )}
                      {items.length > limit && (
                        <button type="button" onClick={() => setLimits((l) => ({ ...l, [c.code]: limit + PAGE }))} className="inline-flex h-8 shrink-0 items-center justify-center gap-1.5 rounded-[8px] text-[12.5px] font-medium text-ink-2 transition-colors hover:bg-ink/[0.05]">
                          <Plus aria-hidden className="h-3.5 w-3.5" />
                          {tx(`Show ${num(Math.min(PAGE, items.length - limit))} more of ${num(items.length - limit)}`, `Tampilkan ${num(Math.min(PAGE, items.length - limit))} lagi dari ${num(items.length - limit)}`)}
                        </button>
                      )}
                    </div>
                  </section>
                );
              })}
            </LayoutGroup>
          </div>
          <AnimatePresence>
            {lifted &&
              (() => {
                const t = all.find((z) => z.id === lifted.id);
                return t ? (
                  <LiftedCard key="lifted" lifted={lifted} x={x} y={y}>
                    <TaskCard t={t} me={me} status={statusOf(t)} floating onOpen={open} onMove={moveTo} onEmail={email} />
                  </LiftedCard>
                ) : null;
              })()}
          </AnimatePresence>
          <p className="sr-only" role="status" aria-live="polite">{announce}</p>
        </div>
      )}

      {view === "board" && (
        <div className="flex h-5 shrink-0 items-center justify-between text-[12px] text-ink-3">
          <span className="truncate">{movable ? tx("Card colour: red is too late or a critical part with an empty shelf, orange is short but still in time. Press a card to see why.", "Warna kartu: merah berarti terlambat atau suku cadang kritis dengan rak kosong, oranye berarti kurang tetapi masih sempat. Tekan kartu untuk melihat alasannya.") : tx("Showing tasks still to decide. Group by Status to see the rest.", "Menampilkan tugas yang masih perlu diputuskan. Kelompokkan menurut Status untuk melihat sisanya.")}</span>
          {group === "status" && (
            <label className="inline-flex cursor-pointer items-center gap-1.5">
              <input type="checkbox" checked={showRejected} onChange={(e) => setShowRejected(e.target.checked)} className="accent-[var(--ink)]" />
              {tx("Show rejected", "Tampilkan yang ditolak")}
            </label>
          )}
        </div>
      )}

      <TaskPeek task={peeked} onClose={closePeek} onMove={moveTo} onEmail={email} />
      {compose && <Compose request={compose} onClose={() => setCompose(null)} onSent={(text) => setToast({ text })} />}
      {rejecting && (
        <RejectDialog
          task={rejecting}
          onCancel={() => setRejecting(null)}
          onReject={(why: RejectWhy) => {
            const t = rejecting;
            const from = statusOf(t);
            setRejecting(null);
            setFlow(true);
            setStatus(d, t, "rejected", why);
            setToast({ text: why.reason ? tx(`${partName(t.description)} rejected. Your reason is recorded.`, `${partName(t.description)} ditolak. Alasan Anda dicatat.`) : tx(`${partName(t.description)} moved to Rejected`, `${partName(t.description)} dipindahkan ke Ditolak`), undo: canMove(me, t, "rejected", from) ? () => { setStatus(d, t, from); setToast(null); } : undefined });
          }}
        />
      )}
      <AnimatePresence>
        {toast && (
          <motion.div role="status" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 8 }} transition={{ duration: 0.16 }} className="fixed bottom-5 left-1/2 z-[55] flex max-w-[min(560px,90vw)] -translate-x-1/2 items-center gap-3 rounded-[12px] bg-ink px-4 py-2.5 text-[13px] text-white shadow-float">
            <span className="min-w-0 truncate">{toast.text}</span>
            {toast.undo && <button type="button" onClick={toast.undo} className="shrink-0 font-semibold underline underline-offset-2">{tx("Undo", "Urungkan")}</button>}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function Picker({ label, value, onChange, options }: { label: string; value: string; onChange: (v: string) => void; options: [string, string][] }) {
  return (
    <label className="inline-flex h-8 items-center gap-1 rounded-[9px] px-2 text-[12.5px] text-ink-3 transition-colors hover:bg-ink/[0.04]">
      {label}
      <select value={value} onChange={(e) => onChange(e.target.value)} className="cursor-pointer bg-transparent font-medium text-ink outline-none">
        {options.map(([k, l]) => <option key={k} value={k}>{l}</option>)}
      </select>
    </label>
  );
}

function FilterMenu({ filter, onChange, active, codes }: { filter: Filter; onChange: (f: Filter) => void; active: number; codes: { code: string; n: number }[] }) {
  const toggle = <T extends string>(list: T[], v: T) => (list.includes(v) ? list.filter((x) => x !== v) : [...list, v]);
  const chip = (on: boolean) => cn("h-7 rounded-full border px-2.5 text-[12.5px] transition-colors", on ? "border-ink bg-ink font-medium text-white" : "border-line text-ink-2 hover:border-line-2");
  return (
    <Popover.Root>
      <Popover.Trigger asChild>
        <button type="button" className={cn("inline-flex h-8 items-center gap-1.5 rounded-[9px] px-2 text-[12.5px] font-medium transition-colors", active ? "bg-accent-soft text-accent" : "text-ink-2 hover:bg-ink/[0.04]")}>
          <ListFilter aria-hidden className="h-4 w-4" />
          {tx("Filter", "Saring")}
          {active > 0 && <span className="grid h-[18px] min-w-[18px] place-items-center rounded-full bg-accent px-1 text-[11px] text-white">{active}</span>}
        </button>
      </Popover.Trigger>
      <Popover.Portal>
        <Popover.Content align="end" sideOffset={6} className="z-40 w-[420px] space-y-3 rounded-[14px] border border-line bg-panel p-4 shadow-float">
          <Section label={tx("How critical (A is the most)", "Kekritisan (A paling kritis)")}>
            {["A", "B", "C", "S"].map((c) => <button key={c} type="button" aria-pressed={filter.crit.includes(c)} onClick={() => onChange({ ...filter, crit: toggle(filter.crit, c) })} className={chip(filter.crit.includes(c))}>{c}</button>)}
          </Section>
          <Section label={tx("Action", "Tindakan")}>
            {KINDS.map((k) => <button key={k} type="button" aria-pressed={filter.kinds.includes(k)} onClick={() => onChange({ ...filter, kinds: toggle(filter.kinds, k) })} className={chip(filter.kinds.includes(k))}>{KIND[k].name}</button>)}
          </Section>
          <Section label={tx("When", "Waktu")}>
            {URGENCIES.map((u) => <button key={u.code} type="button" aria-pressed={filter.urgency.includes(u.code)} onClick={() => onChange({ ...filter, urgency: toggle(filter.urgency, u.code) })} className={chip(filter.urgency.includes(u.code))}>{u.label}</button>)}
          </Section>
          <Section label={tx("Machine", "Mesin")}>
            {MACHINES.map((m) => <button key={m.slug} type="button" aria-pressed={filter.machine === m.slug} onClick={() => onChange({ ...filter, machine: filter.machine === m.slug ? null : m.slug })} className={chip(filter.machine === m.slug)}>{m.plural}</button>)}
          </Section>
          <Section label={tx("Section", "Bagian")}>
            {SECTIONS.map((s) => <button key={s} type="button" aria-pressed={filter.section === s} onClick={() => onChange({ ...filter, section: filter.section === s ? null : s, codes: [] })} className={chip(filter.section === s)}>{SECTION_NAME[s]}</button>)}
          </Section>
          <Section label={tx("Equipment", "Peralatan")}>
            <div className="flex max-h-[120px] flex-wrap gap-1.5 overflow-y-auto">
              {codes.filter((c) => !filter.section || codeSection(c.code) === filter.section).map(({ code, n }) => <button key={code} type="button" aria-pressed={filter.codes.includes(code)} onClick={() => onChange({ ...filter, codes: toggle(filter.codes, code) })} className={chip(filter.codes.includes(code))}>{CODE_NAME[code] ?? code} <span className="opacity-60">{num(n)}</span></button>)}
            </div>
          </Section>
          <Section label={tx("Signals", "Sinyal")}>
            <button type="button" aria-pressed={filter.unusual} onClick={() => onChange({ ...filter, unusual: !filter.unusual })} className={chip(filter.unusual)}>{tx("Unusual use", "Pemakaian tidak biasa")}</button>
          </Section>
          {active > 0 && <button type="button" onClick={() => onChange({ ...EMPTY, q: filter.q })} className="text-[12.5px] font-medium text-ink-2 underline underline-offset-2 hover:text-ink">{tx("Clear filters", "Hapus filter")}</button>}
        </Popover.Content>
      </Popover.Portal>
    </Popover.Root>
  );
}

function Section({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div>
      <div className="mb-1.5 text-[12px] font-medium text-ink-3">{label}</div>
      <div className="flex flex-wrap gap-1.5">{children}</div>
    </div>
  );
}

/** Red: too late, or a critical part with an empty shelf. Orange: buy or move in time. No colour: too much stock or watch. */
function taskSev(t: Task): Severity {
  if (t.kind === "reduce" || t.kind === "dispose" || t.kind === "watch") return "none";
  return sevOf({ short: true, late: t.urgency === "late", critical: t.criticality === "A" || t.criticality === "B", empty: t.stock <= 0 });
}

/** "Compressor KC-391D" or "Flow control valves", instead of the bare equipment code. */
function equipmentWords(t: Task): string | null {
  const unit = t.equipment.find((e) => /^(BF|KC|PP|KT|HE)-/.test(e));
  if (unit) {
    const code = unit.split("-")[0];
    // English names are plural ("Pumps"), so drop the s for one unit. Indonesian does not mark the plural.
    const name = isId() ? CODE_NAME[code] ?? "" : (CODE_NAME[code] ?? "").replace(/s$/, "");
    return name ? `${name} ${unit}` : unit;
  }
  return t.codes[0] ? CODE_NAME[t.codes[0]] ?? null : null;
}

function Foot({ t }: { t: Task }) {
  if (t.kind === "expedite") return <span className="inline-flex items-center gap-1 text-act-ink"><Truck aria-hidden className="h-3.5 w-3.5 shrink-0" />{tx(`Normal delivery: ${Math.round(t.lead_time)} days`, `Pengiriman biasa: ${Math.round(t.lead_time)} hari`)}</span>;
  if (t.kind === "twin" && t.twin) return <span className="inline-flex items-center gap-1 text-twin-ink"><ArrowLeftRight aria-hidden className="h-3.5 w-3.5 shrink-0" />{tx(`Duplicate has ${qty(t.twin.surplus, t.unit)} extra`, `Kembarannya lebih ${qty(t.twin.surplus, t.unit)}`)}</span>;
  if (t.order_by) {
    const soon = (t.days_left ?? 99) <= 7;
    return <span className={cn("inline-flex items-center gap-1", soon ? "font-medium text-plan-ink" : "text-ink-3")}><CalendarDays aria-hidden className="h-3.5 w-3.5 shrink-0" />{(t.days_left ?? 0) <= 0 ? tx("Order today", "Pesan hari ini") : tx(`Order by ${shortDate(t.order_by)}`, `Pesan s.d. ${shortDate(t.order_by)}`)}</span>;
  }
  if (t.unusual) return <span className="inline-flex items-center gap-1 text-watch-ink"><Activity aria-hidden className="h-3.5 w-3.5 shrink-0" />{tx(`${num(t.unusual.ratio, 1)}× its usual use`, `${num(t.unusual.ratio, 1)}× pemakaian biasanya`)}</span>;
  return <span className="text-ink-3">{t.kind === "reduce" ? tx("Stop buying", "Hentikan pembelian") : t.kind === "dispose" ? tx("No use in 17 months", "Tak terpakai 17 bulan") : tx("No order yet", "Belum perlu dipesan")}</span>;
}

type DragProps = ReturnType<ReturnType<typeof useBoardDrag>["cardProps"]>;

function TaskCard({ flow, t, me, status, emailed, showStatus, carried, floating, dragProps, consumeDrag, onOpen, onMove, onEmail, selected }: { flow?: boolean; t: Task; me: Person | null; status: TaskStatus; emailed?: boolean; showStatus?: boolean; carried?: boolean; floating?: boolean; dragProps?: DragProps; consumeDrag?: () => boolean; onOpen: (id: string) => void; onMove: (t: Task, to: TaskStatus) => void; onEmail: (t: Task) => void; selected?: boolean }) {
  const k = KIND[t.kind];
  const over = t.kind === "reduce" || t.kind === "dispose";
  const share = t.target > 0 ? Math.min(1, t.stock / t.target) : 0;
  const tag = equipmentWords(t);
  const step = nextStep(t, status);
  const canStep = !!step && canMove(me, t, status, step.to);
  const canReject = status === "todo" && canMove(me, t, "todo", "rejected");
  const owner = ownerOf(t);
  return (
    <motion.article data-tour={floating ? undefined : "card"} layout={floating ? false : "position"} layoutId={floating ? undefined : `task-${t.id}`} transition={flow ? FLOW_SPRING : { duration: 0 }} className={cn("group relative shrink-0 rounded-[12px] border bg-panel shadow-card transition-[border-color,box-shadow] duration-150 hover:border-line-2 hover:shadow-[0_6px_16px_-10px_rgb(30_26_20/0.3)]", selected ? "border-ink" : "border-line", carried && "ring-2 ring-accent")}>
      <div
        {...(dragProps ? { onPointerDown: dragProps.onPointerDown } : {})}
        onClick={() => {
          if (consumeDrag?.()) return;
          onOpen(t.id);
        }}
        onKeyDown={(e) => {
          if (dragProps?.onKeyDown(e)) return;
          if (e.key === "Enter") {
            e.preventDefault();
            onOpen(t.id);
          }
        }}
        tabIndex={floating ? -1 : 0}
        role="button"
        aria-label={tx(`${partName(t.description)}. Enter opens${dragProps ? ", Space moves" : ""}.`, `${partName(t.description)}. Enter untuk membuka${dragProps ? ", Spasi untuk memindahkan" : ""}.`)}
        className={cn("block cursor-pointer rounded-[12px] p-3 outline-none focus-visible:ring-2 focus-visible:ring-ink", dragProps && "active:cursor-grabbing")}
      >
        <SevBar sev={taskSev(t)} className="inset-y-3 left-0" />
        <span className="flex items-center gap-1.5">
          <Chip status={k.status} label={k.label(t)} />
          {t.unusual && <span title={tx(`${num(t.unusual.ratio, 1)}× usual use recently`, `Belakangan ${num(t.unusual.ratio, 1)}× pemakaian biasa`)} className="grid h-[22px] w-[22px] place-items-center rounded-[7px] bg-watch-soft text-watch-ink"><Activity aria-hidden className="h-3 w-3" /></span>}
          {emailed && <span title={tx("An email has gone out", "Surel sudah dikirim")} className="grid h-[22px] w-[22px] place-items-center rounded-[7px] bg-ink/[0.05] text-ink-3"><Mail aria-hidden className="h-3 w-3" /></span>}
        </span>
        <span className="mt-2 line-clamp-2 block text-[13.5px] font-medium leading-snug tracking-[-0.005em]">{partName(t.description)}</span>
        <span className="mt-0.5 block truncate text-[11.5px] text-ink-3">{tag ? `${tag} · ` : ""}{tx("Part no.", "No. part")} {t.material_no}</span>
        {over ? (
          <span className="mt-2 block text-[12px] tabular-nums text-ink-2"><b className="font-semibold text-ink">{amount(t.stock, t.unit)}</b> {tx("on the shelf", "di rak")}{t.kind === "reduce" && <span className="text-ink-3"> · {tx("new Max", "Max baru")} {qty(t.target, t.unit)}</span>}</span>
        ) : (
          <span className="mt-2 flex items-center gap-2">
            <span className="relative block h-1.5 flex-1 overflow-hidden rounded-full bg-ink/[0.07]" aria-hidden>
              <span className={cn("absolute inset-y-0 left-0 rounded-full", STATUS_TONE[k.status].solid)} style={{ width: `${Math.max(share * 100, t.stock > 0 ? 4 : 0)}%` }} />
            </span>
            <span className="shrink-0 text-[12px] tabular-nums text-ink-3">{tx("Have ", "Ada ")}<b className="font-semibold text-ink">{qty(t.stock, t.unit)}</b> {tx("of", "dari")} {amount(t.target, t.unit)}</span>
          </span>
        )}
        <span className="mt-2 flex items-center justify-between gap-2 border-t border-line pt-2 text-[12px] tabular-nums">
          <Foot t={t} />
          {t.value ? <span className="shrink-0 text-ink-3">{rp(t.value)}</span> : null}
        </span>
        {buyNote(buyBasis(t)) && <span className="mt-1.5 block text-[11.5px] leading-snug text-plan-ink">{buyNote(buyBasis(t))}</span>}
        {showStatus && status !== "todo" && <span className="mt-1.5 block text-[11.5px] text-ink-3">{STATUSES.find((s) => s.code === status)?.label}</span>}
      </div>
      {!floating && (
        <div data-tour="card-step" className="flex items-center gap-1 px-3 pb-3">
          {canStep && step ? (
            <button type="button" onClick={() => onMove(t, step.to)} title={step.label} className="inline-flex h-7 min-w-0 flex-1 items-center justify-center gap-1 rounded-[8px] bg-ink px-2 text-[12px] font-medium text-white transition-colors hover:bg-ink-2">
              <span className="truncate">{step.label}</span>
              <ArrowRight aria-hidden className="h-3.5 w-3.5 shrink-0" />
            </button>
          ) : (
            <span className="min-w-0 flex-1 truncate text-[11.5px] text-ink-3">
              {status === "done" ? tx("Closed", "Ditutup") : status === "rejected" ? tx("Rejected", "Ditolak") : status === "todo" && t.kind !== "watch" ? tx("Waiting for the planner", "Menunggu perencana") : tx(`${firstName(owner)} is handling this`, `${firstName(owner)} sedang menanganinya`)}
            </span>
          )}
          {canReject && (
            <button type="button" aria-label={tx("Reject", "Tolak")} title={tx("Reject", "Tolak")} onClick={() => onMove(t, "rejected")} className="grid h-7 w-7 shrink-0 place-items-center rounded-[8px] border border-line-2 text-ink-2 transition-colors hover:bg-ink/[0.05]">
              <X aria-hidden className="h-3.5 w-3.5" />
            </button>
          )}
          {me && (
            <button type="button" aria-label={emailLabel(me, t)} title={emailLabel(me, t)} onClick={() => onEmail(t)} className="grid h-7 w-7 shrink-0 place-items-center rounded-[8px] border border-line-2 text-ink-2 transition-colors hover:bg-ink/[0.05]">
              <Mail aria-hidden className="h-3.5 w-3.5" />
            </button>
          )}
        </div>
      )}
    </motion.article>
  );
}

function TaskTable({ tasks, statusOf, onOpen, me, onMove }: { tasks: Task[]; statusOf: (t: Task) => TaskStatus; onOpen: (id: string) => void; me: Person | null; onMove: (t: Task, to: TaskStatus) => void }) {
  const [limit, setLimit] = useState(60);
  const cols = "grid-cols-[minmax(0,2.4fr)_150px_120px_130px_130px_110px]";
  const cell = "text-[12.5px] tabular-nums text-ink-2";
  return (
    <Panel className="flex min-h-0 flex-1 flex-col overflow-hidden">
      <div className={cn("grid shrink-0 items-center gap-3 border-b border-line bg-panel-2 px-4 py-2 text-[12px] font-medium text-ink-3", cols)}>
        <span>{tx("Part", "Suku cadang")} ({num(tasks.length)})</span><span>{tx("Action", "Tindakan")}</span><span>Status</span><span>{tx("Have / need", "Ada / butuh")}</span><span>{tx("Last safe order day", "Batas aman pemesanan")}</span><span className="text-right">{tx("Value", "Nilai")}</span>
      </div>
      <ul className="m-0 min-h-0 flex-1 list-none divide-y divide-line overflow-y-auto p-0">
        {tasks.length === 0 && <li className="px-5 py-12 text-center text-[13.5px] text-ink-3">{tx("No task matches these filters.", "Tidak ada tugas yang cocok dengan filter ini.")}</li>}
        {tasks.slice(0, limit).map((t) => (
          <li key={t.id} className={cn("grid cursor-pointer items-center gap-3 px-4 py-2 transition-colors hover:bg-ink/[0.02]", cols)} onClick={() => onOpen(t.id)}>
            <span className="relative flex min-w-0 items-center gap-2.5 pl-2">
              <SevBar sev={taskSev(t)} className="-left-1" />
                  <span className="min-w-0">
                <button type="button" className="block max-w-full truncate text-left text-[13px] font-medium hover:underline">{partName(t.description)}</button>
                <span className="block font-mono text-[11px] text-ink-4">{t.material_no}</span>
              </span>
            </span>
            <span><Chip status={KIND[t.kind].status} label={KIND[t.kind].label(t)} /></span>
            <span onClick={(e) => e.stopPropagation()}>
              <select value={statusOf(t)} onChange={(e) => onMove(t, e.target.value as TaskStatus)} aria-label={tx(`Status of ${partName(t.description)}`, `Status ${partName(t.description)}`)} className="-ml-1 h-7 w-full cursor-pointer rounded-[7px] bg-transparent px-1 text-[12.5px] outline-none transition-colors hover:bg-ink/[0.05]">
                {STATUSES.map((s) => <option key={s.code} value={s.code} disabled={s.code !== statusOf(t) && !canMove(me, t, statusOf(t), s.code)}>{s.label}</option>)}
              </select>
            </span>
            <span className={cell}><b className="font-semibold text-ink">{qty(t.stock, t.unit)}</b> / {amount(t.target, t.unit)}</span>
            <span className={cell}>{t.kind === "expedite" ? <span className="text-act-ink">{tx("Passed, rush it", "Sudah lewat, percepat")}</span> : t.order_by ? ((t.days_left ?? 0) <= 0 ? <span className="font-medium text-plan-ink">{tx("Today", "Hari ini")}</span> : shortDate(t.order_by)) : "—"}</span>
            <span className={cn(cell, "text-right")}>{t.value ? rp(t.value) : "—"}</span>
          </li>
        ))}
        {tasks.length > limit && (
          <li><button type="button" onClick={() => setLimit((l) => l + 60)} className="flex h-10 w-full items-center justify-center text-[13px] font-medium text-ink-2 transition-colors hover:bg-ink/[0.03]">{tx(`Show 60 more of ${num(tasks.length - limit)}`, `Tampilkan 60 lagi dari ${num(tasks.length - limit)}`)}</button></li>
        )}
      </ul>
    </Panel>
  );
}

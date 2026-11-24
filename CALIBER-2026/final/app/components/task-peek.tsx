"use client";

import { useEffect, useState, type ReactNode } from "react";
import Link from "next/link";
import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import { ArrowUpRight, Check, Mail, X } from "lucide-react";
import { Activity, ArrowLeftRight, Lightbulb, ShieldAlert, Tag, Workflow, Wrench, type LucideIcon } from "@/components/icons";
import type { PartAnswer as Answer, Task } from "@/lib/data";
import { useDecisions } from "@/lib/decisions";
import { useMe } from "@/lib/me";
import { buyBasis, buyNote, canMove, CODE_NAME, firstName, ownerOf, personById, recipientFor, SECTION_NAME, SUPPLIER, type Person } from "@/lib/people";
import { categoryName, cn, num, partName, amount, rp, shortDate, CRIT_NAME } from "@/lib/format";
import { CritTile } from "./ui";
import { PartAnswer } from "./part-answer";
import { activityText, approveLabel, KIND, nextStep, STATUSES, type TaskStatus } from "./todo-shared";
import { isId, t as tx } from "@/lib/i18n";

/** One A-part shortage day, in rupiah. An assumption; the What if page has the slider. */
const SHORTAGE_DAY = 5e6;

export function emailLabel(me: Person, t: Task) {
  const to = recipientFor(me, t);
  return to === SUPPLIER ? tx("Email supplier", "Surel pemasok") : tx(`Email ${firstName(personById(to)!)}`, `Surel ${firstName(personById(to)!)}`);
}

export function TaskPeek({ task, onClose, onMove, onEmail }: { task: Task | null; onClose: () => void; onMove: (t: Task, to: TaskStatus) => void; onEmail: (t: Task, advance?: TaskStatus) => void }) {
  const reduce = useReducedMotion();
  useEffect(() => {
    if (!task) return;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [task, onClose]);
  return (
    <AnimatePresence>
      {task && (
        <motion.aside
          key="peek"
          aria-label={partName(task.description)}
          initial={reduce ? false : { x: 32, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          exit={{ x: 32, opacity: 0 }}
          transition={{ duration: 0.2, ease: [0.16, 1, 0.3, 1] }}
          className="fixed inset-y-0 right-0 z-40 flex w-[480px] flex-col border-l border-line bg-panel shadow-float"
        >
          <PeekBody key={task.id} t={task} onClose={onClose} onMove={onMove} onEmail={onEmail} />
        </motion.aside>
      )}
    </AnimatePresence>
  );
}

function Row({ icon: Icon, label, children }: { icon: LucideIcon; label: string; children: ReactNode }) {
  return (
    <div className="grid grid-cols-[148px_minmax(0,1fr)] items-start gap-2 py-[5px] text-[13px]">
      <span className="inline-flex items-center gap-2 pt-px text-ink-3">
        <Icon aria-hidden className="h-[15px] w-[15px] shrink-0" strokeWidth={1.9} />
        {label}
      </span>
      <span className="min-w-0 text-ink">{children}</span>
    </div>
  );
}

function SourceNote({ source }: { source: "openai" | "template" }) {
  return <span className="text-[11.5px] text-ink-4">{source === "openai" ? tx("Written by AI · numbers from the engine", "Ditulis oleh AI · angka dari mesin hitung") : tx("Template text · AI is off", "Teks templat · AI tidak aktif")}</span>;
}

type Explain = { why: string; risk: string; check: string; source: "openai" | "template" };

type Activity = { at: string; actor: string; kind: "status" | "email"; detail: string };

function PeekBody({ t, onClose, onMove, onEmail }: { t: Task; onClose: () => void; onMove: (t: Task, to: TaskStatus) => void; onEmail: (t: Task, advance?: TaskStatus) => void }) {
  const d = useDecisions();
  const { me } = useMe();
  const k = KIND[t.kind];
  const status = (d.get(t.id) ?? "todo") as TaskStatus;
  const owner = ownerOf(t);
  const step = nextStep(t, status);
  const canStep = !!step && canMove(me, t, status, step.to);
  const canReject = status === "todo" && canMove(me, t, "todo", "rejected");
  const emailed = !!d.emailed[t.id];
  // The two steps where someone else must hear about it: the planner approving, the buyer asking a supplier.
  const withEmail = canStep && !!step && t.kind !== "watch" && ((step.to === "approved") || (step.to === "in_progress" && (t.kind === "order" || t.kind === "expedite")));
  const [ai, setAi] = useState<Explain | null>(null);
  const [aiFailed, setAiFailed] = useState(false);
  const [log, setLog] = useState<Activity[]>([]);
  const [answer, setAnswer] = useState<Answer | null>(null);

  useEffect(() => {
    const ctl = new AbortController();
    fetch(`/api/parts/${t.material_no}`, { signal: ctl.signal })
      .then((r) => (r.ok ? r.json() : null))
      .then((j: { answer?: Answer } | null) => setAnswer(j?.answer ?? null))
      .catch(() => {});
    return () => ctl.abort();
  }, [t.material_no]);

  useEffect(() => {
    const ctl = new AbortController();
    fetch(`/api/activity?id=${encodeURIComponent(t.id)}`, { signal: ctl.signal })
      .then((r) => (r.ok ? r.json() : { rows: [] }))
      .then((j: { rows: Activity[] }) => setLog(j.rows))
      .catch(() => {});
    return () => ctl.abort();
  }, [t.id, status, emailed]);

  useEffect(() => {
    const ctl = new AbortController();
    fetch("/api/ai/explain", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ id: t.material_no }), signal: ctl.signal })
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(String(r.status)))))
      .then(setAi)
      .catch((e) => {
        if (e.name !== "AbortError") setAiFailed(true);
      });
    return () => ctl.abort();
  }, [t.material_no]);

  const exposure = t.risk > 0 ? (t.risk / 100) * SHORTAGE_DAY : 0;

  return (
    <>
      <header className="flex h-12 shrink-0 items-center gap-1 border-b border-line px-3">
        <button type="button" onClick={onClose} aria-label={tx("Close", "Tutup")} className="grid h-8 w-8 place-items-center rounded-[8px] text-ink-3 transition-colors hover:bg-ink/[0.05] hover:text-ink">
          <X aria-hidden className="h-4 w-4" />
        </button>
        <span className="ml-auto" />
        <Link href={`/parts/${t.material_no}`} className="inline-flex h-8 items-center gap-1.5 rounded-[8px] px-2.5 text-[12.5px] font-medium text-ink-2 transition-colors hover:bg-ink/[0.05] hover:text-ink">
          <ArrowUpRight aria-hidden className="h-3.5 w-3.5" />
          {tx("Open full page", "Buka halaman lengkap")}
        </Link>
      </header>

      <div className="min-h-0 flex-1 overflow-y-auto px-5 pb-6 pt-4">
        <h2 className="m-0 text-[20px] font-semibold leading-snug tracking-[-0.012em]">{partName(t.description)}</h2>
        {buyNote(buyBasis(t)) && <p className="m-0 mt-1 text-[12.5px] leading-snug text-plan-ink">{buyNote(buyBasis(t))}</p>}
        <p className="m-0 mt-1 text-[12px] text-ink-3">{tx("Part no.", "No. part")} {t.material_no}</p>

        <div className="mt-4">
          {answer ? <PartAnswer a={answer} task={t} compact /> : <div className="h-[260px] animate-pulse rounded-[12px] bg-ink/[0.04]" aria-label={tx("Loading", "Memuat")} />}
        </div>

        <div className="mt-4 border-y border-line py-3">
          <Row icon={Workflow} label="Status">
            <select value={status} onChange={(e) => onMove(t, e.target.value as TaskStatus)} aria-label="Status" className="-ml-1 h-7 cursor-pointer rounded-[7px] bg-transparent px-1 text-[13px] font-medium outline-none transition-colors hover:bg-ink/[0.05]">
              {STATUSES.map((s) => (
                <option key={s.code} value={s.code} disabled={s.code !== status && !canMove(me, t, status, s.code)}>{s.label}</option>
              ))}
            </select>
          </Row>
          <Row icon={k.icon} label={tx("Action", "Tindakan")}><span className={cn("font-medium", k.ink)}>{k.label(t)}</span></Row>
          <Row icon={Workflow} label={tx("Who runs it", "Pelaksana")}>{owner.name} <span className="text-ink-3">· {owner.title}</span></Row>
          <Row icon={Tag} label={tx("Category", "Kategori")}>{categoryName(t.category)}</Row>
          {t.codes.length > 0 && <Row icon={Wrench} label={tx("Used on", "Dipakai di")}>{t.codes.slice(0, 4).map((c) => CODE_NAME[c] ?? c).join(", ")}<span className="text-ink-3"> · {SECTION_NAME[t.section]}</span></Row>}
          <Row icon={ShieldAlert} label={tx("How critical", "Kekritisan")}><span className="inline-flex items-center gap-2"><CritTile crit={t.criticality} />{CRIT_NAME[t.criticality].split(", ").slice(1).join(", ")}</span></Row>
          {exposure >= 1e6 && (t.kind === "order" || t.kind === "expedite" || t.kind === "twin") && (
            <Row icon={ShieldAlert} label={tx("Cost if it runs out", "Biaya jika kehabisan")}>
              {tx(`${rp(exposure)} a year`, `${rp(exposure)} per tahun`)} <span className="text-ink-3">{tx(`· assumes ${rp(SHORTAGE_DAY)} per shortage day for an A part`, `· dengan asumsi ${rp(SHORTAGE_DAY)} per hari kekurangan suku cadang A`)}</span>
            </Row>
          )}
          {t.equipment.length > 0 && <Row icon={Wrench} label={tx("Machines", "Mesin")}>{t.equipment.slice(0, 5).join(", ")}</Row>}
          {t.twin && (
            <Row icon={ArrowLeftRight} label={tx("Duplicate part", "Suku cadang kembar")}>
              {tx("Part no. ", "No. part ")}<Link href={`/parts/${t.twin.donor}`} className="underline underline-offset-2">{t.twin.donor}</Link>{tx(` looks like the same part and holds ${amount(t.twin.surplus, t.unit)} above its Max. Confirm they are interchangeable.`, ` tampaknya suku cadang yang sama dan menyimpan ${amount(t.twin.surplus, t.unit)} di atas Max-nya. Pastikan keduanya bisa saling menggantikan.`)}
            </Row>
          )}
          {t.unusual && (
            <Row icon={Activity} label={tx("Unusual use", "Pemakaian tidak biasa")}>
              {tx(`${amount(t.unusual.qty, t.unit)} in ${shortDate(`${t.unusual.month}-01`).split(" ").slice(1).join(" ")}, ${num(t.unusual.ratio, 1)}× its usual month. Find out if this is a one-off.`, `${amount(t.unusual.qty, t.unit)} pada ${shortDate(`${t.unusual.month}-01`).split(" ").slice(1).join(" ")}, ${num(t.unusual.ratio, 1)}× bulan biasanya. Cari tahu apakah ini hanya sekali.`)}
            </Row>
          )}
        </div>

        <section data-tour="peek-why" className="mt-4">
          <h3 className="m-0 flex items-center gap-1.5 text-[13px] font-semibold"><Lightbulb aria-hidden className="h-4 w-4" />{tx("Why this, and what to check", "Alasannya, dan yang perlu diperiksa")}</h3>
          {aiFailed ? (
            <p className="m-0 mt-2 text-[13px] text-ink-3">{tx("Could not load the explanation. The full page has the numbers behind it.", "Penjelasan gagal dimuat. Angka-angkanya ada di halaman lengkap.")}</p>
          ) : !ai ? (
            <div className="mt-3 space-y-2" aria-label={tx("Loading explanation", "Memuat penjelasan")}>
              <div className="h-3.5 w-full animate-pulse rounded bg-ink/[0.06]" />
              <div className="h-3.5 w-11/12 animate-pulse rounded bg-ink/[0.06]" />
              <div className="h-3.5 w-3/4 animate-pulse rounded bg-ink/[0.06]" />
            </div>
          ) : (
            <>
              <dl className="m-0 mt-2 space-y-2.5 text-[13px] leading-[1.55]">
                <div><dt className="text-[12px] font-medium text-ink-3">{tx("Why", "Alasan")}</dt><dd className="m-0 text-ink">{ai.why}</dd></div>
                <div><dt className="text-[12px] font-medium text-ink-3">{tx("If nobody acts", "Jika tidak ada tindakan")}</dt><dd className="m-0 text-ink">{ai.risk}</dd></div>
                <div><dt className="text-[12px] font-medium text-ink-3">{tx("Check before approving", "Periksa sebelum menyetujui")}</dt><dd className="m-0 text-ink">{ai.check}</dd></div>
              </dl>
              <div className="mt-2"><SourceNote source={ai.source} /></div>
            </>
          )}
        </section>

        {log.length > 0 && (
          <section className="mt-5">
            <h3 className="m-0 text-[13px] font-semibold">{tx("History", "Riwayat")}</h3>
            <ul className="m-0 mt-2 list-none space-y-1.5 p-0 text-[12.5px] leading-snug">
              {log.map((a) => (
                <li key={`${a.at}-${a.detail}`} className="flex gap-2">
                  {a.kind === "email" ? <Mail aria-hidden className="mt-0.5 h-3.5 w-3.5 shrink-0 text-ink-3" /> : <Check aria-hidden className="mt-0.5 h-3.5 w-3.5 shrink-0 text-ink-3" />}
                  <span className="min-w-0"><b className="font-medium">{a.actor}</b> <span className="text-ink-2">{activityText(a.detail)}</span> <span className="text-ink-4">{new Date(a.at).toLocaleString(isId() ? "id-ID" : "en-GB", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" })}</span></span>
                </li>
              ))}
            </ul>
          </section>
        )}
      </div>

      <footer data-tour="peek-actions" className="shrink-0 space-y-2 border-t border-line p-3">
        {step && !canStep && <p className="m-0 text-[12.5px] text-ink-3">{status === "todo" && t.kind !== "watch" ? tx("Waiting for the planner, Nadia Putri, to decide.", "Menunggu keputusan perencana, Nadia Putri.") : tx(`This step belongs to ${owner.name}.`, `Langkah ini menjadi tugas ${owner.name}.`)}</p>}
        {withEmail && step && (
          <button type="button" onClick={() => onEmail(t, step.to)} className="flex h-10 w-full items-center justify-center gap-1.5 rounded-[10px] bg-ink px-3 text-[13.5px] font-medium text-white transition-colors hover:bg-ink-2">
            <Mail aria-hidden className="h-4 w-4 shrink-0" />
            <span className="truncate">{step.to === "approved" ? tx(`Approve and ${me ? emailLabel(me, t).replace(/^Email/, "email") : "email"}`, `Setujui dan kirim ${me ? emailLabel(me, t).replace(/^Surel/, "surel") : "surel"}`) : tx("Request a quote from the supplier", "Minta penawaran dari pemasok")}</span>
          </button>
        )}
        <div className="flex items-center gap-2">
          {canStep && step && (
            <button type="button" onClick={() => onMove(t, step.to)} className={cn("inline-flex h-10 min-w-0 flex-1 items-center justify-center gap-1.5 rounded-[10px] px-3 text-[13.5px] font-medium transition-colors", withEmail ? "border border-line-2 hover:bg-ink/[0.04]" : "bg-ink text-white hover:bg-ink-2")}>
              <Check aria-hidden className="h-4 w-4 shrink-0" strokeWidth={2.25} /><span className="truncate">{withEmail ? (step.to === "approved" ? tx("Approve only", "Setujui saja") : tx("Start without email", "Mulai tanpa surel")) : step.to === "approved" && t.kind !== "watch" ? tx(`Approve: ${approveLabel(t).toLowerCase()}`, `Setujui: ${approveLabel(t).toLowerCase()}`) : step.label}</span>
            </button>
          )}
          {!withEmail && (
            <button type="button" onClick={() => onEmail(t)} className={cn("inline-flex h-10 items-center justify-center gap-1.5 rounded-[10px] border border-line-2 px-3 text-[13.5px] font-medium transition-colors hover:bg-ink/[0.04]", !canStep && "flex-1")}>
              <Mail aria-hidden className="h-4 w-4 shrink-0" />{me ? emailLabel(me, t) : tx("Email", "Surel")}
            </button>
          )}
          {canReject && (
            <button type="button" onClick={() => onMove(t, "rejected")} className="inline-flex h-10 items-center rounded-[10px] px-3 text-[13.5px] font-medium text-ink-2 transition-colors hover:bg-ink/[0.05]">{tx("Reject", "Tolak")}</button>
          )}
        </div>
      </footer>
    </>
  );
}

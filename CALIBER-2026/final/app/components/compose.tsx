"use client";

import { useEffect, useState } from "react";
import { Check, Loader2, Mail, X } from "lucide-react";
import { useDecisions } from "@/lib/decisions";
import { useMe } from "@/lib/me";
import { DEMO_INBOX, PEOPLE, type Person } from "@/lib/people";
import { cn } from "@/lib/format";
import { Avatar } from "./brand-mark";
import { t } from "@/lib/i18n";

type Option = { id: string; name: string; title: string };
type Draft = { subject: string; body: string; source: "openai" | "template"; to: string; options: Option[] };

export type ComposeRequest =
  | { kind: "task"; materialNo: number; to: string; heading: string; advance?: "approved" | "in_progress"; action?: string }
  | { kind: "note"; to: string; subject: string; body: string; heading: string; source?: string };

const everyone = (me: Person | null): Option[] => PEOPLE.filter((p) => p.id !== me?.id).map(({ id, name, title }) => ({ id, name, title }));

/** A ready email: who it is from comes from the login, who it goes to from the task. One press sends it. */
export function Compose({ request, onClose, onSent }: { request: ComposeRequest; onClose: () => void; onSent?: (note: string) => void }) {
  const { me, mail } = useMe();
  const d = useDecisions();
  const [to, setTo] = useState(request.to);
  const [options, setOptions] = useState<Option[]>(request.kind === "note" ? everyone(me) : []);
  const [subject, setSubject] = useState(request.kind === "note" ? request.subject : "");
  const [body, setBody] = useState(request.kind === "note" ? request.body : "");
  const [source, setSource] = useState<string | null>(request.kind === "note" ? request.source ?? null : null);
  const [loading, setLoading] = useState(request.kind === "task");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const materialNo = request.kind === "task" ? request.materialNo : null;
  const advance = request.kind === "task" ? request.advance : undefined;

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  useEffect(() => {
    if (materialNo == null) return;
    const ctl = new AbortController();
    fetch("/api/ai/draft", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ id: materialNo, to }), signal: ctl.signal })
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(String(r.status)))))
      .then((j: Draft) => {
        setSubject(j.subject);
        setBody(j.body);
        setSource(j.source);
        setOptions(j.options);
        setLoading(false);
      })
      .catch((e) => {
        if (e.name === "AbortError") return;
        setError(t("Could not write the draft. You can still type your own.", "Draf gagal dibuat. Anda tetap bisa menulisnya sendiri."));
        setLoading(false);
      });
    return () => ctl.abort();
  }, [materialNo, to]);

  const gmail = `https://mail.google.com/mail/?view=cm&fs=1&to=${encodeURIComponent(DEMO_INBOX)}&su=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
  const toName = options.find((o) => o.id === to)?.name ?? "";

  const send = () => {
    setSending(true);
    setError(null);
    fetch("/api/mail", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ toId: to, subject, body, materialNo, advance }) })
      .then(async (r) => {
        const j = (await r.json().catch(() => ({}))) as { error?: string; moved?: string | null };
        if (!r.ok) throw new Error(j.error ?? t("Could not send.", "Gagal mengirim."));
        await d.refresh();
        onSent?.(t(`Email sent to ${toName}${j.moved === "approved" ? ", task approved" : j.moved === "in_progress" ? ", task started" : ""}`, `Surel terkirim ke ${toName}${j.moved === "approved" ? ", tugas disetujui" : j.moved === "in_progress" ? ", tugas dimulai" : ""}`));
        onClose();
      })
      .catch((e: Error) => setError(e.message))
      .finally(() => setSending(false));
  };

  const field = "h-9 w-full rounded-[9px] border border-line bg-panel-2 px-2.5 text-[13.5px] outline-none focus:border-line-2";

  return (
    <div className="fixed inset-0 z-[60] grid place-items-center p-4" role="dialog" aria-modal="true" aria-label={request.heading}>
      <button type="button" aria-label={t("Close", "Tutup")} onClick={onClose} className="absolute inset-0 bg-ink/30" />
      <div className="relative flex max-h-[92dvh] w-[min(620px,100%)] flex-col overflow-hidden rounded-[18px] border border-line bg-panel shadow-float">
        <header className="flex h-12 shrink-0 items-center gap-2 border-b border-line px-4">
          <Mail aria-hidden className="h-4 w-4 text-ink-3" />
          <h2 className="m-0 text-[14px] font-semibold">{request.heading}</h2>
          <button type="button" onClick={onClose} aria-label={t("Close", "Tutup")} className="ml-auto grid h-8 w-8 place-items-center rounded-[8px] text-ink-3 transition-colors hover:bg-ink/[0.05] hover:text-ink"><X aria-hidden className="h-4 w-4" /></button>
        </header>
        <div className="min-h-0 flex-1 space-y-3 overflow-y-auto p-4">
          <div className="grid grid-cols-[52px_minmax(0,1fr)] items-center gap-x-2 gap-y-2.5 text-[13px]">
            <span className="text-ink-3">{t("From", "Dari")}</span>
            <span className="flex min-w-0 items-center gap-2">
              {me && <Avatar name={me.name} className="h-6 w-6 text-[10px]" />}
              <span className="truncate"><b className="font-medium">{me?.name}</b> <span className="text-ink-3">· {me?.title}</span></span>
            </span>
            <label className="text-ink-3" htmlFor="mail-to">{t("To", "Kepada")}</label>
            <select id="mail-to" value={to} onChange={(e) => { setTo(e.target.value); if (materialNo != null) setLoading(true); }} className={cn(field, "cursor-pointer")}>
              {!options.length && <option value={to}>{t("Loading…", "Memuat…")}</option>}
              {options.map((o) => <option key={o.id} value={o.id}>{o.name} · {o.title}</option>)}
            </select>
            <label className="text-ink-3" htmlFor="mail-subject">{t("Subject", "Perihal")}</label>
            {loading ? <div className="h-9 animate-pulse rounded-[9px] bg-ink/[0.05]" /> : <input id="mail-subject" value={subject} maxLength={200} onChange={(e) => setSubject(e.target.value)} className={field} />}
          </div>
          {loading ? (
            <div className="space-y-2 rounded-[12px] bg-panel-2 p-3" aria-label={t("Writing the draft", "Menyusun draf")}>
              {[100, 92, 96, 70, 40].map((w) => <div key={w} className="h-3.5 animate-pulse rounded bg-ink/[0.06]" style={{ width: `${w}%` }} />)}
            </div>
          ) : (
            <>
              <label className="sr-only" htmlFor="mail-body">{t("Message", "Pesan")}</label>
              <textarea id="mail-body" value={body} maxLength={5000} onChange={(e) => setBody(e.target.value)} rows={11} className="w-full resize-y rounded-[12px] border border-line bg-panel-2 p-3 text-[13.5px] leading-[1.55] outline-none focus:border-line-2" />
            </>
          )}
          <p className="m-0 text-[12px] leading-snug text-ink-3">
            {source === "openai" ? t("Drafted by AI, numbers from the engine. Read it before you send. ", "Draf disusun oleh AI, angka dari mesin hitung. Baca dulu sebelum mengirim. ") : source === "template" ? t("Template text. ", "Teks templat. ") : ""}
            {t(`Demo: every address delivers to ${DEMO_INBOX}.`, `Demo: semua alamat dikirim ke ${DEMO_INBOX}.`)}
          </p>
          {advance && <p className="m-0 rounded-[10px] bg-ready-soft px-3 py-2 text-[12.5px] leading-snug text-ready-ink">{t(`Sending this also ${advance === "approved" ? "approves the task" : "moves the task to In progress"}. Cancel to leave it as it is.`, `Mengirim surel ini sekaligus ${advance === "approved" ? "menyetujui tugasnya" : "memindahkan tugasnya ke Sedang berjalan"}. Batalkan jika ingin membiarkannya seperti semula.`)}</p>}
          {error && <p role="alert" className="m-0 text-[13px] font-medium text-act-ink">{error}</p>}
          {!mail && <p className="m-0 rounded-[10px] bg-plan-soft px-3 py-2 text-[12.5px] leading-snug text-plan-ink">{t("Gmail is not connected on this server, so this opens Gmail with the draft filled in, and you press Send there.", "Gmail belum terhubung di server ini, jadi tombol ini membuka Gmail dengan draf yang sudah terisi, lalu Anda menekan Kirim di sana.")}</p>}
        </div>
        <footer className="flex shrink-0 items-center justify-end gap-2 border-t border-line p-3">
          <button type="button" onClick={onClose} className="inline-flex h-9 items-center rounded-[10px] px-3 text-[13px] font-medium text-ink-2 transition-colors hover:bg-ink/[0.05]">{t("Cancel", "Batal")}</button>
          {mail ? (
            <>
              <a href={gmail} target="_blank" rel="noreferrer" className="inline-flex h-9 items-center rounded-[10px] border border-line-2 px-3 text-[13px] font-medium transition-colors hover:bg-ink/[0.04]">{t("Open in Gmail", "Buka di Gmail")}</a>
              <button type="button" onClick={send} disabled={sending || loading || !subject.trim() || !body.trim()} className="inline-flex h-9 items-center gap-2 rounded-[10px] bg-ink px-4 text-[13px] font-medium text-white transition-colors hover:bg-ink-2 disabled:opacity-40">
                {sending ? <Loader2 aria-hidden className="h-4 w-4 animate-spin" /> : <Check aria-hidden className="h-4 w-4" strokeWidth={2.5} />}{t("Send", "Kirim")}
              </button>
            </>
          ) : (
            <a href={loading ? undefined : gmail} target="_blank" rel="noreferrer" onClick={() => { if (advance && materialNo != null && request.kind === "task") d.set(materialNo, advance, { material_no: materialNo, action: request.action }); onClose(); }} className={cn("inline-flex h-9 items-center gap-2 rounded-[10px] bg-ink px-4 text-[13px] font-medium text-white", loading && "pointer-events-none opacity-40")}>{t("Open in Gmail", "Buka di Gmail")}</a>
          )}
        </footer>
      </div>
    </div>
  );
}

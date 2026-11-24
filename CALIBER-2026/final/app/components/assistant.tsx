"use client";

import Link from "next/link";
import { useCallback, useEffect, useRef, useState, type FormEvent, type ReactNode } from "react";
import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import { ArrowUp, Loader2, MessageCircle, X } from "lucide-react";
import { useMe } from "@/lib/me";
import { firstName, type Person } from "@/lib/people";
import { cn } from "@/lib/format";
import { t as tx } from "@/lib/i18n";

type Turn = { role: "user" | "assistant"; content: string; source?: string };

const STARTERS_ID: Record<string, string[]> = {
  planner: ["Apa yang perlu saya setujui lebih dulu hari ini?", "Suku cadang A mana yang sudah terlambat untuk dibeli?", "Berapa dana yang bisa kita bebaskan?"],
  procurement: ["Pesanan yang sudah disetujui mana yang paling mendesak?", "Pesanan percepatan mana yang paling lama tiba?", "Berapa yang perlu saya beli bulan ini?"],
  warehouse: ["Pemindahan antarsuku cadang kembar mana yang didahulukan?", "Suku cadang mana yang perlu dihitung lebih dulu?", "Berapa stok yang berada di atas Max?"],
  maintenance: ["Apa yang mendesak di bagian saya?", "Seberapa siap kita menghadapi turnaround?", "Suku cadang mana yang pemakaiannya tidak biasa?"],
  finance: ["Mengapa rencana yang disarankan butuh stok lebih sedikit?", "Berapa dana yang tertahan di atas Max?", "Apa hasil simulasi ulang pemakaian riil?"],
};

const STARTERS: Record<string, string[]> = {
  planner: ["What should I approve first today?", "Which A parts are too late to buy?", "How much cash can we free?"],
  procurement: ["Which approved orders are most urgent?", "Which rush orders take longest to arrive?", "How much do I need to buy this month?"],
  warehouse: ["Which transfers between duplicate parts come first?", "Which parts should be counted first?", "How much stock sits above Max?"],
  maintenance: ["What is urgent in my section?", "How ready is the turnaround?", "Which parts had unusual use?"],
  finance: ["Why does the recommended plan need less stock?", "How much is tied up above Max?", "What does the replay on real demand show?"],
};

/** Material numbers in an answer become links to the part. */
function linked(text: string): ReactNode[] {
  return text.split(/\b(41\d{8})\b/).map((piece, i) =>
    i % 2 ? <Link key={i} href={`/parts/${piece}`} className="font-mono text-[12.5px] underline underline-offset-2">{piece}</Link> : piece,
  );
}

export function Assistant({ path }: { path: string }) {
  const { me } = useMe();
  const reduce = useReducedMotion();
  const [open, setOpen] = useState(false);
  const [turns, setTurns] = useState<Turn[]>([]);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const end = useRef<HTMLDivElement>(null);
  const input = useRef<HTMLTextAreaElement>(null);

  const send = useCallback(
    (q: string) => {
      const question = q.trim();
      if (!question || busy) return;
      const next: Turn[] = [...turns, { role: "user", content: question }];
      setTurns(next);
      setText("");
      setBusy(true);
      fetch("/api/ai/chat", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ page: path, messages: next.map(({ role, content }) => ({ role, content })) }) })
        .then((r) => (r.ok ? r.json() : Promise.reject(new Error(String(r.status)))))
        .then((j: { text: string; source: string }) => setTurns((t) => [...t, { role: "assistant", content: j.text, source: j.source }]))
        .catch(() => setTurns((t) => [...t, { role: "assistant", content: tx("I could not reach the assistant. Try again.", "Asisten tidak dapat dihubungi. Coba lagi.") }]))
        .finally(() => setBusy(false));
    },
    [busy, path, turns],
  );

  useEffect(() => {
    const onAsk = (e: Event) => {
      setOpen(true);
      send((e as CustomEvent<string>).detail);
    };
    window.addEventListener("sk-ask", onAsk);
    return () => window.removeEventListener("sk-ask", onAsk);
  }, [send]);

  useEffect(() => {
    end.current?.scrollIntoView({ block: "end" });
  }, [turns, busy]);
  useEffect(() => {
    if (open) input.current?.focus();
  }, [open]);

  const submit = (e: FormEvent) => {
    e.preventDefault();
    send(text);
  };

  return (
    <>
      {!open && (
        <button type="button" data-tour="assistant" onClick={() => setOpen(true)} className="fixed bottom-5 right-5 z-30 inline-flex h-11 items-center gap-2 rounded-full bg-ink pl-3.5 pr-4 text-[13.5px] font-medium text-white shadow-float transition-colors hover:bg-ink-2">
          <MessageCircle aria-hidden className="h-[18px] w-[18px]" />{tx("Ask Sparekit", "Tanya Sparekit")}
        </button>
      )}
      <AnimatePresence>
        {open && (
          <motion.section
            role="dialog"
            aria-label={tx("Ask Sparekit", "Tanya Sparekit")}
            initial={reduce ? false : { opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 12 }}
            transition={{ duration: 0.18, ease: [0.16, 1, 0.3, 1] }}
            className="fixed bottom-5 right-5 z-[45] flex h-[min(600px,calc(100dvh-40px))] w-[min(420px,calc(100vw-32px))] flex-col overflow-hidden rounded-[18px] border border-line bg-panel shadow-float"
          >
            <header className="flex h-12 shrink-0 items-center gap-2 border-b border-line px-4">
              <MessageCircle aria-hidden className="h-4 w-4 text-ink-3" />
              <h2 className="m-0 text-[14px] font-semibold">{tx("Ask Sparekit", "Tanya Sparekit")}</h2>
              <button type="button" onClick={() => setOpen(false)} aria-label={tx("Close", "Tutup")} className="ml-auto grid h-8 w-8 place-items-center rounded-[8px] text-ink-3 transition-colors hover:bg-ink/[0.05] hover:text-ink"><X aria-hidden className="h-4 w-4" /></button>
            </header>
            <div className="min-h-0 flex-1 space-y-3 overflow-y-auto p-4">
              {turns.length === 0 && <Starters me={me} onPick={send} />}
              {turns.map((t, i) => (
                <div key={i} className={cn("flex", t.role === "user" && "justify-end")}>
                  <div className={cn("max-w-[88%] whitespace-pre-wrap rounded-[14px] px-3 py-2 text-[13.5px] leading-[1.5]", t.role === "user" ? "bg-ink text-white" : "bg-panel-2 text-ink")}>
                    {t.role === "assistant" ? linked(t.content) : t.content}
                    {t.source === "openai" && <span className="mt-1 block text-[11px] text-ink-4">{tx("Numbers from the engine", "Angka dari mesin hitung")}</span>}
                  </div>
                </div>
              ))}
              {busy && <div className="inline-flex items-center gap-2 rounded-[14px] bg-panel-2 px-3 py-2 text-[13px] text-ink-3"><Loader2 aria-hidden className="h-4 w-4 animate-spin" />{tx("Checking the data…", "Memeriksa data…")}</div>}
              <div ref={end} />
            </div>
            <form onSubmit={submit} className="flex shrink-0 items-end gap-2 border-t border-line p-3">
              <label className="sr-only" htmlFor="ask-input">{tx("Your question", "Pertanyaan Anda")}</label>
              <textarea
                id="ask-input"
                ref={input}
                rows={1}
                value={text}
                maxLength={800}
                onChange={(e) => setText(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    send(text);
                  }
                }}
                placeholder={tx("Ask about a part, a task or the stocking plan", "Tanyakan tentang suku cadang, tugas, atau rencana stok")}
                className="max-h-24 min-h-9 min-w-0 flex-1 resize-none rounded-[10px] border border-line bg-panel-2 px-3 py-2 text-[13.5px] leading-snug outline-none placeholder:text-ink-4 focus:border-line-2"
              />
              <button type="submit" aria-label={tx("Send", "Kirim")} disabled={busy || !text.trim()} className="grid h-9 w-9 shrink-0 place-items-center rounded-[10px] bg-ink text-white transition-opacity disabled:opacity-40"><ArrowUp aria-hidden className="h-4 w-4" /></button>
            </form>
          </motion.section>
        )}
      </AnimatePresence>
    </>
  );
}

function Starters({ me, onPick }: { me: Person | null; onPick: (q: string) => void }) {
  return (
    <div>
      <p className="m-0 text-[14px] font-medium">{me ? tx(`Hi ${firstName(me)}. What do you need to know?`, `Halo, ${firstName(me)}. Apa yang ingin Anda ketahui?`) : tx("What do you need to know?", "Apa yang ingin Anda ketahui?")}</p>
      <p className="m-0 mt-1 text-[12.5px] leading-snug text-ink-3">{tx("Answers come from the engine's data. Ask in English or Bahasa Indonesia.", "Jawaban berasal dari data mesin hitung. Silakan bertanya dalam bahasa Indonesia atau Inggris.")}</p>
      <div className="mt-3 space-y-1.5">
        {(tx(STARTERS, STARTERS_ID)[me?.role ?? "planner"]).map((q) => (
          <button key={q} type="button" onClick={() => onPick(q)} className="block w-full rounded-[10px] border border-line px-3 py-2 text-left text-[13px] text-ink-2 transition-colors hover:border-line-2 hover:text-ink">{q}</button>
        ))}
      </div>
    </div>
  );
}

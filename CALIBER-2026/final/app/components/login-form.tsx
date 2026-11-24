"use client";

import { useState, type FormEvent } from "react";
import { useSearchParams } from "next/navigation";
import { ArrowRight, Loader2 } from "lucide-react";
import { BRAND } from "@/lib/brand";
import { DEMO_PASSWORD, PEOPLE } from "@/lib/people";
import { BrandMark } from "./brand-mark";
import { LangToggle } from "./lang";
import { t } from "@/lib/i18n";

export function LoginForm() {
  const sp = useSearchParams();
  const [login, setLogin] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState<"demo" | "form" | null>(null);
  const [error, setError] = useState<string | null>(null);

  const signIn = (l: string, pw: string, who: "demo" | "form") => {
    setBusy(who);
    setError(null);
    fetch("/api/auth/login", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ login: l, password: pw }) })
      .then(async (r) => {
        if (!r.ok) throw new Error(((await r.json().catch(() => ({}))) as { error?: string }).error ?? t("Could not sign in.", "Gagal masuk."));
        const next = sp.get("next");
        window.location.href = next && next.startsWith("/") && !next.startsWith("//") ? next : "/todo";
      })
      .catch((e: Error) => {
        setError(e.message);
        setBusy(null);
      });
  };
  const submit = (e: FormEvent) => {
    e.preventDefault();
    signIn(login, password, "form");
  };

  return (
    <main className="relative grid min-h-dvh lg:grid-cols-[minmax(0,1fr)_minmax(0,1.1fr)]">
      <LangToggle className="absolute right-4 top-4 z-10" />
      <section className="relative hidden flex-col justify-between overflow-hidden bg-ink p-10 text-white lg:flex">
        <div className="flex items-center gap-2.5">
          <BrandMark className="h-9 w-9" />
          <span className="text-[17px] font-semibold tracking-[-0.01em]">{BRAND}</span>
        </div>
        <div>
          <p className="m-0 max-w-[20ch] text-[36px] font-semibold leading-[1.12] tracking-[-0.025em]">{t("The right part, on the shelf, before the shutdown.", "Suku cadang yang tepat, sudah di rak, sebelum kilang berhenti.")}</p>
          <ol className="m-0 mt-8 list-none space-y-3 p-0 text-[14px] text-white/75">
            <li className="flex gap-3"><b className="w-5 font-semibold text-white">1</b>{t("The planner approves what the engine recommends.", "Perencana menyetujui rekomendasi dari mesin hitung.")}</li>
            <li className="flex gap-3"><b className="w-5 font-semibold text-white">2</b>{t("The task moves to whoever runs it, with the email drafted.", "Tugas berpindah ke pelaksananya, lengkap dengan draf surelnya.")}</li>
            <li className="flex gap-3"><b className="w-5 font-semibold text-white">3</b>{t("Each person sees only their own work.", "Setiap orang hanya melihat pekerjaannya sendiri.")}</li>
          </ol>
        </div>
        <p className="m-0 text-[12px] text-white/50">{t("Dummy case data from CALIBER 2026.", "Data kasus fiktif dari CALIBER 2026.")}</p>
      </section>

      <section className="flex items-center justify-center px-4 py-8 sm:px-8">
        <div className="w-full max-w-[420px]">
          <div className="mb-6 flex items-center gap-2.5 lg:hidden">
            <BrandMark className="h-8 w-8" />
            <span className="text-[16px] font-semibold">{BRAND}</span>
          </div>
          <h1 className="m-0 text-[26px] font-semibold tracking-[-0.02em]">{t(`Sign in to ${BRAND}`, `Masuk ke ${BRAND}`)}</h1>
          <p className="m-0 mt-1 text-[14px] text-ink-2">{t("The demo opens as the inventory planner. Switch role any time from the bottom left.", "Demo dibuka sebagai perencana persediaan. Peran bisa diganti kapan saja dari pojok kiri bawah.")}</p>

          <button type="button" disabled={!!busy} onClick={() => signIn(PEOPLE[0].login, DEMO_PASSWORD, "demo")} className="mt-5 inline-flex h-11 w-full items-center justify-center gap-2 rounded-[12px] bg-ink text-[14px] font-medium text-white transition-colors hover:bg-ink-2 disabled:opacity-60">
            {busy === "demo" ? <Loader2 aria-hidden className="h-4 w-4 animate-spin" /> : null}
            {t("Log in as demo", "Masuk sebagai demo")}
            {busy !== "demo" && <ArrowRight aria-hidden className="h-4 w-4" />}
          </button>

          <details className="mt-4 rounded-[14px] border border-line bg-panel px-3 py-2.5">
            <summary className="cursor-pointer text-[13px] font-medium text-ink-2">{t("Sign in with email and password", "Masuk dengan surel dan kata sandi")}</summary>
            <form onSubmit={submit} className="mt-3 space-y-2">
              <label className="block text-[12.5px] text-ink-3">{t("Email", "Surel")}
                <input type="email" autoComplete="username" value={login} onChange={(e) => setLogin(e.target.value)} placeholder={PEOPLE[0].login} className="mt-1 h-9 w-full rounded-[9px] border border-line bg-panel-2 px-2.5 text-[13.5px] text-ink outline-none focus:border-line-2" />
              </label>
              <label className="block text-[12.5px] text-ink-3">{t("Password", "Kata sandi")}
                <input type="password" autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} className="mt-1 h-9 w-full rounded-[9px] border border-line bg-panel-2 px-2.5 text-[13.5px] text-ink outline-none focus:border-line-2" />
              </label>
              <button type="submit" disabled={!!busy || !login || !password} className="inline-flex h-9 w-full items-center justify-center gap-2 rounded-[10px] border border-line-2 text-[13.5px] font-medium transition-colors hover:bg-ink/[0.04] disabled:opacity-40">
                {busy === "form" && <Loader2 aria-hidden className="h-4 w-4 animate-spin" />}{t("Sign in", "Masuk")}
              </button>
              <p className="m-0 text-[12px] text-ink-3">{t("Every demo account uses the password", "Semua akun demo memakai kata sandi")} <code className="font-mono">{DEMO_PASSWORD}</code>.</p>
            </form>
          </details>
          {error && <p role="alert" className="m-0 mt-3 text-[13px] font-medium text-act-ink">{error}</p>}
        </div>
      </section>
    </main>
  );
}

"use client";

import { useEffect, type ReactNode } from "react";
import { LANG_COOKIE, LANGS, lang as currentLang, setLang, t, type Lang } from "@/lib/i18n";
import { cn } from "@/lib/format";

/** Sets the language for every client component below it. Renders before its children, so they read it on the first pass. */
export function LangProvider({ lang, children }: { lang: Lang; children: ReactNode }) {
  setLang(lang);
  useEffect(() => {
    document.documentElement.lang = lang;
  }, [lang]);
  return <>{children}</>;
}

const NAME: Record<Lang, string> = { en: "English", id: "Bahasa Indonesia" };

/** Keeps the choice for a year and reloads, so server and client text change together. */
function chooseLang(l: Lang) {
  document.cookie = `${LANG_COOKIE}=${l}; path=/; max-age=31536000; samesite=lax`;
  window.location.reload();
}

/** EN | ID switch. The choice lives in a cookie, and the page reloads so the server text and the client text change together. */
export function LangToggle({ className }: { className?: string }) {
  const cur = currentLang();
  const pick = (l: Lang) => {
    if (l === cur) return;
    chooseLang(l);
  };
  return (
    <div role="radiogroup" aria-label={t("Language", "Bahasa")} className={cn("inline-flex h-8 items-center rounded-full border border-line bg-panel p-0.5 shadow-card", className)}>
      {LANGS.map((l) => (
        <button
          key={l}
          type="button"
          role="radio"
          aria-checked={l === cur}
          title={NAME[l]}
          onClick={() => pick(l)}
          className={cn(
            "h-[26px] min-w-[38px] rounded-full px-2.5 text-[12px] font-semibold tracking-[0.02em] transition-colors duration-150",
            l === cur ? "bg-ink text-white" : "text-ink-3 hover:text-ink",
          )}
        >
          {l.toUpperCase()}
        </button>
      ))}
    </div>
  );
}

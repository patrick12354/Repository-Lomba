// Shared by server and client. English is the default; Indonesian is chosen with the toggle and kept in a cookie.
//
// Text is written in place as t("English", "Bahasa Indonesia"), so both wordings sit side by side and can be read together.
// The language is read at render time, never when a module loads: call t() inside components and functions, not at the top level.

export type Lang = "en" | "id";
export const LANG_COOKIE = "sk_lang";
export const LANGS: Lang[] = ["en", "id"];

let clientLang: Lang = "en";
let ssrLang: Lang = "en";
let serverResolver: (() => Lang | null) | null = null;

/** Set by lib/i18n-server.ts so server components and API routes read the language of their own request. */
export function setServerResolver(f: () => Lang | null) {
  serverResolver = f;
}

/** Called by the client provider while it renders, before any of its children. */
export function setLang(l: Lang) {
  if (typeof window === "undefined") ssrLang = l;
  else clientLang = l;
}

export function lang(): Lang {
  if (typeof window !== "undefined") return clientLang;
  return serverResolver?.() ?? ssrLang;
}

export const isId = () => lang() === "id";

/** Pick the wording for the current language. Works for strings and for JSX. */
export function t<T>(en: T, id: T): T {
  return lang() === "id" ? id : en;
}

export const parseLang = (v: string | null | undefined): Lang => (v === "id" ? "id" : "en");

/** A label table whose values follow the language: `bi({ a: ["Act now", "Segera"] })`. Reads stay `TABLE[key]`. */
export function bi<K extends string>(table: Record<K, [string, string]>): Record<K, string> {
  const out = {} as Record<K, string>;
  for (const k of Object.keys(table) as K[]) {
    Object.defineProperty(out, k, { enumerable: true, get: () => t(table[k][0], table[k][1]) });
  }
  return out;
}

/** Number locale for Intl: Indonesian writes 1.234,5. */
export const numLocale = () => (isId() ? "id-ID" : "en-US");

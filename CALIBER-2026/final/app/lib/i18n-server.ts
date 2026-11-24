import "server-only";
import { AsyncLocalStorage } from "node:async_hooks";
import { cache } from "react";
import { cookies } from "next/headers";
import { LANG_COOKIE, parseLang, setServerResolver, type Lang } from "./i18n";

// Server components share one box per request (React cache). API routes run their handler inside withLang instead.
const box = cache((): { v: Lang | null } => ({ v: null }));
const als = new AsyncLocalStorage<Lang>();

function boxed(): Lang | null {
  try {
    return box().v;
  } catch {
    return null;
  }
}

setServerResolver(() => als.getStore() ?? boxed());

/** The request's language. Call it once near the top of a page or layout; everything rendered below then follows it. */
export async function getLang(): Promise<Lang> {
  const v = parseLang((await cookies()).get(LANG_COOKIE)?.value);
  try {
    box().v = v;
  } catch {
    /* outside a render: the caller passes it on */
  }
  return v;
}

/** Run an API handler in the caller's language, so text built on the server matches the page that asked. */
export async function withLang<T>(fn: () => T | Promise<T>): Promise<T> {
  const l = parseLang((await cookies()).get(LANG_COOKIE)?.value);
  return als.run(l, fn);
}

/** `export const generateMetadata = titled("Stock", "Stok")`: the browser tab follows the language too. */
export function titled(en: string, id: string) {
  return async () => {
    const l = await getLang();
    return { title: l === "id" ? id : en };
  };
}

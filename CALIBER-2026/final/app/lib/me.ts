"use client";

import { useEffect, useSyncExternalStore } from "react";
import type { Person } from "./people";

type Me = { me: Person | null; mail: boolean };
const EMPTY: Me = { me: null, mail: false };
const listeners = new Set<() => void>();
let cache = EMPTY;
let asked = false;

function subscribe(l: () => void) {
  listeners.add(l);
  return () => {
    listeners.delete(l);
  };
}

/** The signed-in person, and whether Gmail is connected on the server. */
export function useMe(): Me {
  const state = useSyncExternalStore(subscribe, () => cache, () => EMPTY);
  useEffect(() => {
    if (asked) return;
    asked = true;
    fetch("/api/auth/me", { cache: "no-store" })
      .then((r) => (r.ok ? r.json() : EMPTY))
      .then((d: Me) => {
        cache = d;
        listeners.forEach((l) => l());
      })
      .catch(() => {
        asked = false;
      });
  }, []);
  return state;
}

/** Takes on another demo role. A full reload resets everything held for the previous person. */
export function switchRole(id: string) {
  void fetch("/api/auth/switch", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ id }) }).finally(() => {
    window.location.reload();
  });
}

export function signOut() {
  void fetch("/api/auth/logout", { method: "POST" }).finally(() => {
    window.location.href = "/login?out=1";
  });
}

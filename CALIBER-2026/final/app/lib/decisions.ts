"use client";

import { useEffect, useSyncExternalStore } from "react";

// Task status is written to SQLite through /api/decisions (a temporary demo database on the server).
// The in-memory copy here only makes the button respond instantly; the server is the record.
export type Decision = "approved" | "in_progress" | "done" | "rejected";
type State = { map: Record<string, Decision>; emailed: Record<string, true> };
const listeners = new Set<() => void>();
const EMPTY: State = { map: {}, emailed: {} };
let cache: State = EMPTY;
let loaded = false;
let loading: Promise<void> | null = null;

function emit(next: State) {
  cache = next;
  listeners.forEach((l) => l());
}

function fetchAll(): Promise<void> {
  return fetch("/api/decisions", { cache: "no-store" })
    .then((r) => (r.ok ? r.json() : { rows: [], emailed: [] }))
    .then((d: { rows: { id: string; decision: Decision }[]; emailed: string[] }) => {
      loaded = true;
      emit({ map: Object.fromEntries(d.rows.map((r) => [r.id, r.decision])), emailed: Object.fromEntries(d.emailed.map((id) => [id, true as const])) });
    });
}

function load(): Promise<void> {
  if (loaded) return Promise.resolve();
  if (!loading) loading = fetchAll().catch(() => void (loading = null));
  return loading;
}

function subscribe(l: () => void) {
  listeners.add(l);
  return () => {
    listeners.delete(l);
  };
}

export function useDecisions() {
  const state = useSyncExternalStore(subscribe, () => cache, () => EMPTY);
  const map = state.map;
  useEffect(() => {
    void load();
  }, []);
  return {
    map,
    emailed: state.emailed,
    get: (id: string | number) => map[String(id)],
    set: (id: string | number, d: Decision | null, meta?: { material_no?: number; action?: string; note?: string; reason?: string; reason_source?: string }) => {
      const key = String(id);
      const prev = cache;
      const next = { ...cache.map };
      if (d) next[key] = d;
      else delete next[key];
      emit({ ...cache, map: next });
      const req = d
        ? fetch("/api/decisions", {
            method: "POST",
            headers: { "content-type": "application/json" },
            body: JSON.stringify({ id: key, decision: d, ...meta }),
          })
        : fetch(`/api/decisions?id=${encodeURIComponent(key)}`, { method: "DELETE" });
      req.then((r) => !r.ok && emit(prev)).catch(() => emit(prev));
    },
    count: Object.keys(map).length,
    approved: Object.values(map).filter((d) => d === "approved").length,
    refresh: () => fetchAll().catch(() => {}),
    clear: () => {
      void fetch("/api/decisions?all=1", { method: "DELETE" }).then(() => fetchAll());
    },
  };
}

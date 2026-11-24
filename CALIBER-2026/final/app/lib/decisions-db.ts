import "server-only";
import { randomBytes, scryptSync, timingSafeEqual } from "node:crypto";
import os from "node:os";
import path from "node:path";
import Database from "better-sqlite3";
import { tasks } from "./data";
import { DEMO_PASSWORD, ownerOf, PEOPLE, type Person } from "./people";

/**
 * Everything people do in the app, written to SQLite: accounts, task status, and an activity log.
 * Vercel's bundle is read-only, so the writable database lives in the temp folder (/tmp on Vercel).
 * It survives while the server instance is warm; a cold start begins a fresh demo session.
 * The analytics database (data/partpulse.db) stays read-only and untouched.
 */
let handle: Database.Database | null = null;

export const DECISIONS_PATH = path.join(process.env.VERCEL ? "/tmp" : os.tmpdir(), "sparekit-tasks-v4.sqlite");

const hash = (password: string, salt: string) => scryptSync(password, salt, 32).toString("hex");

function db(): Database.Database {
  if (!handle) {
    handle = new Database(DECISIONS_PATH);
    handle.pragma("journal_mode = WAL");
    handle.exec(`
    CREATE TABLE IF NOT EXISTS users (
      id TEXT PRIMARY KEY, login TEXT UNIQUE NOT NULL, name TEXT NOT NULL, title TEXT NOT NULL, role TEXT NOT NULL, section TEXT,
      email TEXT NOT NULL, salt TEXT NOT NULL, password_hash TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS decisions (
      id TEXT PRIMARY KEY, material_no INTEGER, action TEXT,
      decision TEXT NOT NULL CHECK (decision IN ('approved','in_progress','done','rejected')),
      note TEXT, reason TEXT, reason_source TEXT, decided_by TEXT, decided_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS activity (
      seq INTEGER PRIMARY KEY AUTOINCREMENT, task_id TEXT, at TEXT NOT NULL, actor TEXT NOT NULL, kind TEXT NOT NULL, detail TEXT NOT NULL
    );
    CREATE INDEX IF NOT EXISTS ix_activity ON activity(task_id);`);
    const add = handle.prepare("insert or ignore into users (id, login, name, title, role, section, email, salt, password_hash) values (?,?,?,?,?,?,?,?,?)");
    for (const p of PEOPLE) {
      const salt = randomBytes(16).toString("hex");
      add.run(p.id, p.login, p.name, p.title, p.role, p.section ?? null, p.email, salt, hash(DEMO_PASSWORD, salt));
    }
    if (!(handle.prepare("select count(*) as n from decisions").get() as { n: number }).n) seed(handle);
  }
  return handle;
}

/** A believable starting point: the planner has already approved a few, so each role opens to real work. */
function seed(h: Database.Database) {
  const all = tasks();
  const take = (kind: string, n: number) => all.filter((t) => t.kind === kind).slice(0, n);
  const write = h.prepare("insert or ignore into decisions (id, material_no, action, decision, decided_by, decided_at) values (?,?,?,?,?,?)");
  const log = h.prepare("insert into activity (task_id, at, actor, kind, detail) values (?,?,?,?,?)");
  const at = new Date().toISOString();
  const start = (list: typeof all, state: "approved" | "in_progress") => {
    for (const t of list) {
      write.run(t.id, t.material_no, t.kind, state, "Nadia Putri", at);
      log.run(t.id, at, "Nadia Putri", "status", "Approved");
      if (state === "in_progress") log.run(t.id, at, ownerOf(t).name, "status", "Started");
    }
  };
  start(take("expedite", 4).slice(2), "in_progress");
  start(take("expedite", 2), "approved");
  start(take("order", 6), "approved");
  start(take("twin", 5), "approved");
  start(take("dispose", 5), "approved");
  // A few rejections with reasons, so the learning panel opens on real examples.
  const reject = h.prepare("insert or ignore into decisions (id, material_no, action, decision, note, reason, reason_source, decided_by, decided_at) values (?,?,?,?,?,?,?,?,?)");
  const said: [string, number, string, string][] = [
    ["reduce", 0, "Overhaul of the same pump set is planned next quarter, keep it.", "needed"],
    ["reduce", 1, "Shelf count looks wrong, someone should check bin first.", "data"],
    ["order", 7, "Already on an open order from the central store.", "covered"],
  ];
  for (const [kind, i, note, reason] of said) {
    const t = all.filter((x) => x.kind === kind)[i];
    if (!t) continue;
    reject.run(t.id, t.material_no, t.kind, "rejected", note, reason, "planner", "Nadia Putri", at);
    log.run(t.id, at, "Nadia Putri", "status", `Rejected: ${note}`);
  }
}

export function checkPassword(login: string, password: string): string | null {
  const row = db().prepare("select id, salt, password_hash from users where login = ?").get(login.trim().toLowerCase()) as { id: string; salt: string; password_hash: string } | undefined;
  if (!row) return null;
  const given = Buffer.from(hash(password, row.salt), "hex");
  return timingSafeEqual(given, Buffer.from(row.password_hash, "hex")) ? row.id : null;
}

export type DecisionState = "approved" | "in_progress" | "done" | "rejected";
export type DecisionRow = { id: string; material_no: number | null; action: string | null; decision: DecisionState; note: string | null; reason: string | null; reason_source: string | null; decided_by: string | null; decided_at: string };
export type ActivityRow = { at: string; actor: string; kind: "status" | "email"; detail: string };

export function listDecisions(): DecisionRow[] {
  return db().prepare("select * from decisions order by decided_at desc").all() as DecisionRow[];
}

export function decisionOf(id: string): DecisionState | null {
  return (db().prepare("select decision from decisions where id = ?").get(id) as { decision: DecisionState } | undefined)?.decision ?? null;
}

const VERB: Record<DecisionState, string> = { approved: "Approved", in_progress: "Started", done: "Marked done", rejected: "Rejected" };

export function saveDecision(d: { id: string; material_no?: number | null; action?: string | null; decision: DecisionState; note?: string | null; reason?: string | null; reason_source?: string | null }, by: Person) {
  const at = new Date().toISOString();
  db()
    .prepare(
      `insert into decisions (id, material_no, action, decision, note, reason, reason_source, decided_by, decided_at) values (@id, @material_no, @action, @decision, @note, @reason, @reason_source, @by, @at)
       on conflict(id) do update set decision = excluded.decision, note = excluded.note, reason = excluded.reason, reason_source = excluded.reason_source, decided_by = excluded.decided_by, decided_at = excluded.decided_at`,
    )
    .run({ id: d.id, material_no: d.material_no ?? null, action: d.action ?? null, decision: d.decision, note: d.note ?? null, reason: d.reason ?? null, reason_source: d.reason_source ?? null, by: by.name, at });
  logActivity(d.id, by, "status", d.decision === "rejected" && d.note ? `Rejected: ${d.note}` : VERB[d.decision]);
}

/** The record of planner decisions: rejections grouped by reason, and how often each kind of suggestion is accepted. */
export function learning() {
  const rows = db().prepare("select id, material_no, action, decision, note, reason, reason_source, decided_at from decisions").all() as DecisionRow[];
  const byId = new Map(tasks().map((t) => [t.id, t]));
  const rejected = rows.filter((r) => r.decision === "rejected");
  const reasons = new Map<string, { n: number; parts: { material_no: number | null; description: string; note: string | null; source: string | null }[] }>();
  for (const r of rejected) {
    const key = r.reason ?? "none";
    const cur = reasons.get(key) ?? { n: 0, parts: [] };
    cur.n++;
    cur.parts.push({ material_no: r.material_no, description: byId.get(r.id)?.description ?? String(r.material_no ?? r.id), note: r.note, source: r.reason_source });
    reasons.set(key, cur);
  }
  const kinds = new Map<string, { yes: number; no: number }>();
  for (const r of rows) {
    const k = r.action ?? "other";
    const cur = kinds.get(k) ?? { yes: 0, no: 0 };
    if (r.decision === "rejected") cur.no++;
    else cur.yes++;
    kinds.set(k, cur);
  }
  return {
    decided: rows.length,
    rejected: rejected.length,
    reasons: Array.from(reasons, ([code, v]) => ({ code, ...v })).sort((a, b) => b.n - a.n),
    acceptance: Array.from(kinds, ([kind, v]) => ({ kind, ...v, rate: v.yes / Math.max(1, v.yes + v.no) })).sort((a, b) => a.rate - b.rate),
  };
}

export function deleteDecision(id: string, by: Person) {
  db().prepare("delete from decisions where id = ?").run(id);
  logActivity(id, by, "status", "Moved back to To decide");
}

/** Back to the opening state of the demo. */
export function resetDecisions() {
  const h = db();
  h.exec("delete from decisions; delete from activity;");
  seed(h);
}

export function logActivity(taskId: string | null, by: Person, kind: ActivityRow["kind"], detail: string) {
  db().prepare("insert into activity (task_id, at, actor, kind, detail) values (?,?,?,?,?)").run(taskId, new Date().toISOString(), by.name, kind, detail.slice(0, 200));
}

export function activityFor(taskId: string): ActivityRow[] {
  return db().prepare("select at, actor, kind, detail from activity where task_id = ? order by seq desc limit 20").all(taskId) as ActivityRow[];
}

/** Task ids with an email already sent, for the small mark on a card. */
export function emailedIds(): string[] {
  return (db().prepare("select distinct task_id from activity where kind = 'email' and task_id is not null").all() as { task_id: string }[]).map((r) => r.task_id);
}

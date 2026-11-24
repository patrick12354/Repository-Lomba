import "server-only";
import path from "node:path";
import Database from "better-sqlite3";

let handle: Database.Database | null = null;

/** One read-only connection per server instance. Vercel's filesystem is read-only anyway. */
export function db(): Database.Database {
  if (!handle) {
    handle = new Database(path.join(process.cwd(), "data/partpulse.db"), {
      readonly: true,
      fileMustExist: true,
    });
  }
  return handle;
}

export function all<T>(sql: string, ...params: unknown[]): T[] {
  return db().prepare(sql).all(...params) as T[];
}

export function one<T>(sql: string, ...params: unknown[]): T | undefined {
  return db().prepare(sql).get(...params) as T | undefined;
}

let metaCache: Record<string, string> | null = null;
export function meta(): Record<string, string> {
  if (!metaCache) {
    metaCache = Object.fromEntries(
      all<{ key: string; value: string }>("select key, value from meta").map((r) => [r.key, r.value]),
    );
  }
  return metaCache;
}

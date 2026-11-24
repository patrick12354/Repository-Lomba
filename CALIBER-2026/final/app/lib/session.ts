/** Signed session cookie: "<person id>.<expiry>.<hmac>". Web Crypto only, so proxy.ts and routes share it. */
export const SESSION_COOKIE = "sk_session";
export const SESSION_HOURS = 12;

const enc = new TextEncoder();
const hex = (b: ArrayBuffer) => Array.from(new Uint8Array(b), (x) => x.toString(16).padStart(2, "0")).join("");
const unhex = (s: string) => Uint8Array.from(s.match(/../g) ?? [], (x) => parseInt(x, 16));

/** SESSION_SECRET when set. Otherwise derived from another server secret, so a deployed app never signs with a public value. */
async function key() {
  const raw = process.env.SESSION_SECRET || `sparekit:${process.env.GMAIL_APP_PASSWORD ?? ""}:${process.env.OPENAI_API_KEY ?? "local-dev"}`;
  return crypto.subtle.importKey("raw", enc.encode(raw), { name: "HMAC", hash: "SHA-256" }, false, ["sign", "verify"]);
}

export async function signSession(id: string) {
  const body = `${id}.${Date.now() + SESSION_HOURS * 3_600_000}`;
  return `${body}.${hex(await crypto.subtle.sign("HMAC", await key(), enc.encode(body)))}`;
}

export async function readSession(token: string | undefined): Promise<string | null> {
  if (!token) return null;
  const [id, exp, sig] = token.split(".");
  if (!id || !exp || !sig || !/^[0-9a-f]+$/.test(sig) || Number(exp) < Date.now()) return null;
  const ok = await crypto.subtle.verify("HMAC", await key(), unhex(sig), enc.encode(`${id}.${exp}`));
  return ok ? id : null;
}

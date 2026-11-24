import "server-only";
import { t } from "./i18n";
import { cookies } from "next/headers";
import { personById, type Person } from "./people";
import { readSession, SESSION_COOKIE } from "./session";

export async function currentUser(): Promise<Person | null> {
  const store = await cookies();
  return personById(await readSession(store.get(SESSION_COOKIE)?.value));
}

export const signInFirst = () => Response.json({ error: t("Sign in first.", "Masuk terlebih dahulu.") }, { status: 401 });

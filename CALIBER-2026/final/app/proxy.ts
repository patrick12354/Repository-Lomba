import { NextResponse, type NextRequest } from "next/server";
import { readSession, signSession, SESSION_COOKIE, SESSION_HOURS } from "@/lib/session";

/** Visitors without a session are signed in as the demo planner, so the link opens straight into the app. */
const DEMO_ID = "planner";

export async function proxy(req: NextRequest) {
  const { pathname, searchParams } = req.nextUrl;
  const signedIn = !!(await readSession(req.cookies.get(SESSION_COOKIE)?.value));
  if (signedIn) return pathname === "/login" ? NextResponse.redirect(new URL("/todo", req.url)) : NextResponse.next();
  if (pathname === "/api/auth/login") return NextResponse.next();
  // After an explicit sign out, show the login page so another account can be picked.
  if (pathname === "/login" && searchParams.has("out")) return NextResponse.next();

  const token = await signSession(DEMO_ID);
  const cookie = { name: SESSION_COOKIE, value: token, path: "/", httpOnly: true, sameSite: "lax" as const, maxAge: SESSION_HOURS * 3600, secure: process.env.NODE_ENV === "production" };
  let res: NextResponse;
  if (pathname === "/login") {
    const next = searchParams.get("next");
    res = NextResponse.redirect(new URL(next && next.startsWith("/") && !next.startsWith("//") ? next : "/todo", req.url));
  } else {
    // Hand this same request the new session, so the first page renders signed in without a redirect.
    req.cookies.set(SESSION_COOKIE, token);
    const headers = new Headers(req.headers);
    headers.set("cookie", req.cookies.toString());
    res = NextResponse.next({ request: { headers } });
  }
  res.cookies.set(cookie);
  return res;
}

export const config = {
  matcher: ["/((?!_next/|favicon|manifest|sw\\.js|icon-|apple-|.*\\.(?:png|svg|jpg|jpeg|webp|glb|ico|woff2?)$).*)"],
};

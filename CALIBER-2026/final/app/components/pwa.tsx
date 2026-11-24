"use client";

import { useEffect } from "react";

/** Registers the tiny service worker so the app can be added to a phone's home screen. */
export function PwaRegister() {
  useEffect(() => {
    if ("serviceWorker" in navigator && process.env.NODE_ENV === "production") {
      navigator.serviceWorker.register("/sw.js").catch(() => {});
    }
  }, []);
  return null;
}

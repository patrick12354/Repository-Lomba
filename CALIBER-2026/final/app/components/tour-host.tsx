"use client";

import { useCallback, useEffect, useState } from "react";
import { useMe } from "@/lib/me";
import { Tour, type TourStep } from "./tour";
import { stepsFor, tourKey } from "./tour-steps";

const read = (k: string) => {
  try {
    return localStorage.getItem(k) === "1";
  } catch {
    return true; // storage is blocked, so do not interrupt on every visit
  }
};
const mark = (k: string) => {
  try {
    localStorage.setItem(k, "1");
  } catch {
    /* it will simply play again */
  }
};

/** The To do guide plays once per role. Every other page plays once on this device. */
const seenKey = (page: string, role: string) => (page === "/todo" ? `sk-tour:/todo:${role}` : `sk-tour:${page}`);
const FULL_TODO = "sk-tour:/todo:full";

/** Plays a page's guide on the first visit. Press Tutorial in the sidebar to replay it. */
export function TourHost({ path }: { path: string }) {
  const { me } = useMe();
  const [steps, setSteps] = useState<TourStep[] | null>(null);
  const page = tourKey(path);

  useEffect(() => {
    if (!me || !page || read(seenKey(page, me.id))) return;
    const id = window.setTimeout(() => setSteps(stepsFor(page, me, !read(FULL_TODO))), 1200);
    return () => window.clearTimeout(id);
  }, [me, page]);

  useEffect(() => {
    const replay = () => me && setSteps(stepsFor(path, me, true));
    window.addEventListener("sk-tour", replay);
    return () => window.removeEventListener("sk-tour", replay);
  }, [me, path]);

  const close = useCallback(() => {
    if (me && page) mark(seenKey(page, me.id));
    if (page === "/todo") mark(FULL_TODO);
    setSteps(null);
  }, [me, page]);

  return steps ? <Tour key={path} steps={steps} onClose={close} /> : null;
}

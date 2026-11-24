"use client";

import type { ReactNode } from "react";
import { motion, useReducedMotion } from "motion/react";

/** A short, quiet fade between pages. Opacity only, so nothing shifts or reflows. */
export default function Template({ children }: { children: ReactNode }) {
  const reduce = useReducedMotion();
  return (
    <motion.div initial={reduce ? false : { opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.18, ease: "easeOut" }}>
      {children}
    </motion.div>
  );
}

"use client";

import { t as tx } from "@/lib/i18n";
import { motion, useMotionValue, useReducedMotion, type MotionValue } from "motion/react";
import { useCallback, useEffect, useRef, useState, type KeyboardEvent, type PointerEvent as ReactPointerEvent, type ReactNode } from "react";

// Pointer drag for board cards. A card lifts only after 6px of movement, so a plain click still opens it.
// The lifted card follows the pointer on its own layer, the source gap closes and the target column opens one.
// Keyboard: Space lifts, left and right pick a column, Space drops, Esc cancels.

export type Lifted = { id: string; from: string; width: number; height: number; ox: number; oy: number };
export type Carried = { id: string; from: string; at: string };

const THRESHOLD = 6;
const LIFT_SPRING = { type: "spring", stiffness: 520, damping: 34, mass: 0.7 } as const;
export const FLOW_SPRING = { type: "spring", stiffness: 420, damping: 36, mass: 0.9 } as const;

export function useBoardDrag({ columns, onDrop }: { columns: { code: string; label: string }[]; onDrop: (id: string, to: string) => void }) {
  const [lifted, setLifted] = useState<Lifted | null>(null);
  const [over, setOver] = useState<string | null>(null);
  const [carried, setCarried] = useState<Carried | null>(null);
  const [announce, setAnnounce] = useState("");
  const x = useMotionValue(0);
  const y = useMotionValue(0);
  const trackRef = useRef<HTMLDivElement>(null);
  const press = useRef<{ id: string; from: string; el: HTMLElement; sx: number; sy: number } | null>(null);
  const liftedRef = useRef<Lifted | null>(null);
  const overRef = useRef<string | null>(null);
  const moved = useRef(false);
  const scrollStep = useRef(0);
  const label = (code: string) => columns.find((c) => c.code === code)?.label ?? code;

  const colAt = (cx: number, cy: number) => {
    for (const el of document.elementsFromPoint(cx, cy)) {
      const col = (el as HTMLElement).closest?.("[data-board-col]") as HTMLElement | null;
      if (col) return col.dataset.boardCol ?? null;
    }
    return null;
  };

  const finish = useCallback(() => {
    const l = liftedRef.current;
    const to = overRef.current;
    if (l && to && to !== l.from) onDrop(l.id, to);
    press.current = null;
    liftedRef.current = null;
    overRef.current = null;
    scrollStep.current = 0;
    setLifted(null);
    setOver(null);
  }, [onDrop]);

  useEffect(() => {
    let raf = 0;
    const onMove = (e: PointerEvent) => {
      const p = press.current;
      if (!p) return;
      if (!liftedRef.current) {
        if (Math.hypot(e.clientX - p.sx, e.clientY - p.sy) < THRESHOLD) return;
        const r = p.el.getBoundingClientRect();
        const l = { id: p.id, from: p.from, width: r.width, height: r.height, ox: p.sx - r.left, oy: p.sy - r.top };
        liftedRef.current = l;
        moved.current = true;
        setLifted(l);
        setCarried(null);
        document.getSelection()?.removeAllRanges();
      }
      const l = liftedRef.current;
      x.set(e.clientX - l.ox);
      y.set(e.clientY - l.oy);
      const col = colAt(e.clientX, e.clientY);
      if (col !== overRef.current) {
        overRef.current = col;
        setOver(col);
      }
      const track = trackRef.current;
      if (track) {
        const r = track.getBoundingClientRect();
        scrollStep.current = e.clientX < r.left + 72 ? -14 : e.clientX > r.right - 72 ? 14 : 0;
      }
    };
    const onUp = () => {
      if (liftedRef.current) finish();
      press.current = null;
    };
    const tick = () => {
      if (scrollStep.current && trackRef.current) trackRef.current.scrollLeft += scrollStep.current;
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    window.addEventListener("pointermove", onMove);
    window.addEventListener("pointerup", onUp);
    window.addEventListener("pointercancel", onUp);
    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("pointermove", onMove);
      window.removeEventListener("pointerup", onUp);
      window.removeEventListener("pointercancel", onUp);
    };
  }, [finish, x, y]);

  function cardProps(id: string, from: string, title: string) {
    return {
      onPointerDown: (e: ReactPointerEvent<HTMLElement>) => {
        if (e.button !== 0 || e.pointerType === "touch") return;
        if ((e.target as HTMLElement).closest("input, select, button, a, label, textarea")) return;
        press.current = { id, from, el: e.currentTarget, sx: e.clientX, sy: e.clientY };
        moved.current = false;
      },
      onKeyDown: (e: KeyboardEvent<HTMLElement>) => {
        const idx = columns.findIndex((c) => c.code === (carried?.at ?? from));
        if (e.key === " ") {
          e.preventDefault();
          if (carried?.id === id) {
            if (carried.at !== carried.from) onDrop(id, carried.at);
            setAnnounce(carried.at !== carried.from ? tx(`${title} moved to ${label(carried.at)}.`, `${title} dipindahkan ke ${label(carried.at)}.`) : tx(`${title} not moved.`, `${title} tidak dipindahkan.`));
            setCarried(null);
          } else {
            setCarried({ id, from, at: from });
            setAnnounce(tx(`${title} lifted. Left or right picks a column, Space drops, Esc cancels.`, `${title} diangkat. Panah kiri atau kanan memilih kolom, Spasi meletakkan, Esc membatalkan.`));
          }
          return true;
        }
        if (carried?.id !== id) return false;
        if (e.key === "Escape") {
          e.preventDefault();
          setCarried(null);
          setAnnounce(tx(`Cancelled. ${title} stays in ${label(from)}.`, `Dibatalkan. ${title} tetap di ${label(from)}.`));
          return true;
        }
        const step = e.key === "ArrowLeft" ? -1 : e.key === "ArrowRight" ? 1 : 0;
        if (step && columns[idx + step]) {
          e.preventDefault();
          const at = columns[idx + step].code;
          setCarried({ ...carried, at });
          setAnnounce(tx(`To ${label(at)}.`, `Ke ${label(at)}.`));
          return true;
        }
        return false;
      },
    };
  }

  /** The click that ends a drag must not also open the card. */
  const consumeDrag = () => {
    const was = moved.current;
    moved.current = false;
    return was;
  };

  const target = lifted ? over : carried?.at ?? null;
  const source = lifted?.from ?? carried?.from ?? null;
  return { lifted, carried, target, source, x, y, trackRef, cardProps, consumeDrag, announce };
}

export function LiftedCard({ lifted, x, y, children }: { lifted: Lifted; x: MotionValue<number>; y: MotionValue<number>; children: ReactNode }) {
  const reduce = useReducedMotion();
  return (
    <motion.div
      style={{ x, y, width: lifted.width }}
      initial={{ scale: 1, rotate: 0 }}
      animate={{ scale: reduce ? 1 : 1.03, rotate: reduce ? 0 : 1.6 }}
      exit={{ scale: 1, rotate: 0, opacity: 0 }}
      transition={LIFT_SPRING}
      className="pointer-events-none fixed left-0 top-0 z-50 origin-top-left [&>*]:shadow-[0_18px_36px_-14px_rgb(30_26_20/0.45)]"
    >
      {children}
    </motion.div>
  );
}

export function DropGap({ height }: { height: number }) {
  return <motion.div initial={{ opacity: 0, scaleY: 0.7 }} animate={{ opacity: 1, scaleY: 1 }} exit={{ opacity: 0, scaleY: 0.7 }} transition={FLOW_SPRING} style={{ height }} className="shrink-0 origin-top rounded-[12px] border border-dashed border-accent/50 bg-accent-soft/50" />;
}

"use client";

import { useRef, useState, type ReactNode } from "react";
import * as Popover from "@radix-ui/react-popover";
import { CircleHelp } from "lucide-react";
import { t } from "@/lib/i18n";

/** A small "?" that explains a number. Hover or press it; the long text stays out of the card. */
export function Hint({ children, label }: { children: ReactNode; label?: string }) {
  const [open, setOpen] = useState(false);
  const timer = useRef<number | null>(null);
  const hover = (on: boolean) => {
    if (timer.current) window.clearTimeout(timer.current);
    timer.current = window.setTimeout(() => setOpen(on), on ? 120 : 180);
  };
  return (
    <Popover.Root open={open} onOpenChange={setOpen}>
      <Popover.Trigger asChild>
        <button type="button" aria-label={label ?? t("What does this mean?", "Apa artinya?")} onPointerEnter={(e) => e.pointerType === "mouse" && hover(true)} onPointerLeave={(e) => e.pointerType === "mouse" && hover(false)} className="inline-grid h-[18px] w-[18px] shrink-0 place-items-center rounded-full align-[-3px] text-ink-4 transition-colors hover:bg-ink/[0.06] hover:text-ink focus-visible:text-ink">
          <CircleHelp aria-hidden className="h-3.5 w-3.5" />
        </button>
      </Popover.Trigger>
      <Popover.Portal>
        <Popover.Content side="top" align="center" sideOffset={6} collisionPadding={12} onPointerEnter={() => hover(true)} onPointerLeave={() => hover(false)} className="z-50 w-[300px] max-w-[90vw] rounded-[12px] bg-ink px-3.5 py-2.5 text-[12.5px] font-normal leading-[1.5] text-white shadow-float">
          {children}
          <Popover.Arrow className="fill-ink" />
        </Popover.Content>
      </Popover.Portal>
    </Popover.Root>
  );
}

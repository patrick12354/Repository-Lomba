"use client";

import { Check, X } from "lucide-react";
import { Undo2 } from "@/components/icons";
import { useDecisions } from "@/lib/decisions";
import { useMe } from "@/lib/me";
import { cn } from "@/lib/format";

/** Approve / reject pair. Approve carries the exact quantity so the button says what it does. */
export function Decide({
  id,
  approveLabel = "Approve",
  size = "md",
  full,
  compact,
  materialNo,
  action,
}: {
  id: string | number;
  approveLabel?: string;
  size?: "sm" | "md";
  full?: boolean;
  compact?: boolean;
  materialNo?: number;
  action?: string;
}) {
  const d = useDecisions();
  const { me } = useMe();
  const state = d.get(id);
  const meta = { material_no: materialNo, action };
  const h = size === "sm" ? "h-8 text-[12.5px]" : "h-10 text-[13.5px]";
  if (me && me.role !== "planner" && !state) return <p className="m-0 text-[12.5px] text-ink-3">Waiting for the planner to decide. Work on it from the To do board.</p>;
  if (state) {
    return (
      <div className={cn("flex items-center gap-2", full && "w-full")}>
        <span
          className={cn(
            "squircle inline-flex items-center gap-1.5 rounded-[10px] px-3 font-medium",
            h,
            state === "rejected" ? "bg-idle-soft text-idle-ink" : "bg-ready-soft text-ready-ink",
            full && "flex-1 justify-center",
          )}
        >
          {state === "rejected" ? <X className="h-4 w-4" strokeWidth={2.25} aria-hidden /> : <Check className="h-4 w-4" strokeWidth={2.25} aria-hidden />}
          {state === "approved" ? "Approved" : state === "in_progress" ? "In progress" : state === "done" ? "Done" : "Rejected"}
          <span className="ml-1 rounded-[5px] bg-white/70 px-1.5 py-0.5 text-[10.5px] font-medium uppercase tracking-[0.04em] text-ink-3">Demo</span>
        </span>
        <button
          type="button"
          hidden={me?.role !== "planner"}
          onClick={() => d.set(id, null)}
          aria-label="Undo decision"
          className={cn("squircle grid shrink-0 place-items-center rounded-[10px] text-ink-3 transition-colors hover:bg-ink/[0.06] hover:text-ink", size === "sm" ? "h-8 w-8" : "h-10 w-10")}
        >
          <Undo2 className="h-4 w-4" aria-hidden />
        </button>
      </div>
    );
  }
  if (compact) {
    return (
      <div className="flex items-center gap-1.5">
        <button
          type="button"
          onClick={() => d.set(id, "approved", meta)}
          aria-label={approveLabel}
          title={approveLabel}
          className="squircle grid h-9 w-9 place-items-center rounded-[10px] bg-ink text-white transition-[transform,background-color] duration-150 hover:bg-ink-2 active:scale-95"
        >
          <Check className="h-4 w-4" strokeWidth={2.5} aria-hidden />
        </button>
        <button
          type="button"
          onClick={() => d.set(id, "rejected", meta)}
          aria-label="Reject"
          title="Reject"
          className="squircle grid h-9 w-9 place-items-center rounded-[10px] border border-line-2 bg-panel text-ink-2 transition-colors duration-150 hover:bg-ink/[0.04] active:scale-95"
        >
          <X className="h-4 w-4" strokeWidth={2.5} aria-hidden />
        </button>
      </div>
    );
  }
  return (
    <div className={cn("flex items-center gap-2", full && "w-full")}>
      <button
        type="button"
        onClick={() => d.set(id, "approved", meta)}
        className={cn(
          "squircle inline-flex items-center justify-center gap-1.5 rounded-[10px] bg-ink px-3.5 font-medium text-white transition-[transform,background-color] duration-150 hover:bg-ink-2 active:scale-[0.98]",
          h,
          full && "flex-1",
        )}
      >
        <Check className="h-4 w-4" strokeWidth={2.25} aria-hidden />
        {approveLabel}
      </button>
      <button
        type="button"
        onClick={() => d.set(id, "rejected", meta)}
        className={cn(
          "squircle inline-flex items-center justify-center gap-1.5 rounded-[10px] border border-line-2 bg-panel px-3 font-medium text-ink-2 transition-colors duration-150 hover:bg-ink/[0.04] active:scale-[0.98]",
          h,
        )}
      >
        <X className="h-4 w-4" strokeWidth={2.25} aria-hidden />
        Reject
      </button>
    </div>
  );
}

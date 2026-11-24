import { cn } from "@/lib/format";

/** A spare-part crate seen from the corner. */
export function BrandMark({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 32 32" className={className} aria-hidden>
      <rect x="1" y="1" width="30" height="30" rx="9" className="fill-accent" />
      <path d="M16 7.5 24 12v8.4L16 25l-8-4.6V12z" fill="none" stroke="white" strokeWidth="1.9" strokeLinejoin="round" />
      <path d="M8 12l8 4.5 8-4.5M16 16.5V25" fill="none" stroke="white" strokeWidth="1.9" strokeLinejoin="round" />
      <path d="M12 9.8l8 4.5" stroke="#ffe0c2" strokeWidth="1.9" strokeLinecap="round" />
    </svg>
  );
}

export function Avatar({ name, className }: { name: string; className?: string }) {
  const initials = name.split(" ").map((w) => w[0]).join("").slice(0, 2);
  return <span aria-hidden className={cn("grid shrink-0 place-items-center rounded-full bg-accent-soft font-semibold text-accent", className)}>{initials}</span>;
}

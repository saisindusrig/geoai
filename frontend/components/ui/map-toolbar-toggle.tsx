"use client";

import type { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

/** Compact pill toggle for map toolbar (e.g. transparent underground view). */
export default function MapToolbarToggle({
  label,
  active,
  onChange,
  title,
  icon: Icon,
  className,
}: {
  label: string;
  active: boolean;
  onChange: () => void;
  title: string;
  icon: LucideIcon;
  className?: string;
}) {
  return (
    <button
      type="button"
      title={title}
      aria-label={title}
      aria-pressed={active}
      onClick={onChange}
      className={cn(
        "inline-flex items-center gap-1 rounded-lg border px-2 py-1 text-[10px] font-medium transition-all duration-200 backdrop-blur-md",
        active
          ? "border-primary/40 bg-primary/15 text-foreground"
          : "border-border bg-card/90 text-muted-foreground hover:text-foreground hover:bg-surface-hover",
        className,
      )}
    >
      <Icon className="h-3 w-3 shrink-0" />
      {label}
    </button>
  );
}

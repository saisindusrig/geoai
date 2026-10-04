"use client";

import { cn } from "@/lib/utils";

export function Tabs({
  tabs,
  active,
  onChange,
  className,
  compact,
  bare,
}: {
  tabs: { id: string; label: string }[];
  active: string;
  onChange: (id: string) => void;
  className?: string;
  compact?: boolean;
  bare?: boolean;
}) {
  return (
    <div className={cn("flex gap-0 border-b border-border", !bare && "bg-background-secondary", className)}>
      {tabs.map((tab) => (
        <button
          key={tab.id}
          type="button"
          aria-pressed={active === tab.id}
          onClick={() => onChange(tab.id)}
          className={cn(
            "rounded-none font-medium transition-colors duration-150",
            compact ? "px-2 py-1 text-[10px]" : "flex-1 px-3 py-1.5 text-xs",
            active === tab.id
              ? "bg-primary/10 text-primary border-b-2 border-primary"
              : "text-muted-foreground hover:text-foreground hover:bg-surface-hover border-b-2 border-transparent",
          )}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
}

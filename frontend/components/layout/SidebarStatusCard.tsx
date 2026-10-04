"use client";

import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

export function SidebarStatusCard({
  title,
  trailing,
  children,
  className,
}: {
  title: string;
  trailing?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "rounded-lg border border-border bg-background-secondary/90 backdrop-blur-sm shadow-sm p-2.5 space-y-2",
        className,
      )}
    >
      <div className="flex items-center justify-between gap-2">
        <span className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
          {title}
        </span>
        {trailing}
      </div>
      {children}
    </div>
  );
}

export function SidebarStatChip({
  label,
  ok,
  pendingLabel = "Pending",
  readyLabel = "Ready",
}: {
  label: string;
  ok: boolean;
  pendingLabel?: string;
  readyLabel?: string;
}) {
  return (
    <div
      className={cn(
        "flex-1 min-w-0 rounded-md border px-1 py-1.5 text-center",
        ok
          ? "border-success/30 bg-[rgba(34,197,94,0.1)]"
          : "border-border/60 bg-muted/20",
      )}
    >
      <div className="text-[9px] uppercase tracking-wide text-muted-foreground truncate">{label}</div>
      <div
        className={cn(
          "text-[10px] font-semibold mt-0.5 truncate",
          ok ? "text-[#4ADE80]" : "text-muted-foreground",
        )}
      >
        {ok ? readyLabel : pendingLabel}
      </div>
    </div>
  );
}

export function SidebarMetricChip({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="flex-1 min-w-0 rounded-md border border-border/60 bg-muted/20 px-1 py-1.5 text-center">
      <div className="text-[9px] uppercase tracking-wide text-muted-foreground truncate">{label}</div>
      <div className="text-[11px] font-semibold mt-0.5 text-foreground">{value}</div>
    </div>
  );
}

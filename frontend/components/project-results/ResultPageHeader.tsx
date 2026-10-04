"use client";

import type { ReactNode } from "react";
import { StatusPill } from "@/components/project-results/StatusPill";
import { cn } from "@/lib/utils";

export default function ResultPageHeader({
  title,
  subtitle,
  status,
  statusVariant = "warning",
  actions,
  className,
}: {
  title: string;
  subtitle?: string;
  status?: string;
  statusVariant?: "warning" | "success" | "accent" | "muted";
  actions?: ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("flex flex-col gap-4 border-b border-border pb-5 sm:flex-row sm:items-start sm:justify-between", className)}>
      <div className="min-w-0 space-y-2">
        <p className="font-mono text-[10px] uppercase tracking-[0.16em] text-primary">GeoAI / project data</p>
        <div className="flex flex-wrap items-center gap-2">
          <h1 className="text-2xl font-medium tracking-[-0.045em] text-foreground sm:text-3xl">{title}</h1>
          {status && <StatusPill label={status} variant={statusVariant} />}
        </div>
        {subtitle && <p className="text-sm leading-relaxed text-muted-foreground max-w-2xl">{subtitle}</p>}
      </div>
      {actions && <div className="flex flex-wrap items-center gap-2 shrink-0">{actions}</div>}
    </div>
  );
}

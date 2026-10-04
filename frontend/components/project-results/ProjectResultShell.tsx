"use client";

import type { ReactNode } from "react";
import BottomSummaryBar, { type SummaryStats } from "@/components/layout/BottomSummaryBar";
import { cn } from "@/lib/utils";

export default function ProjectResultShell({
  stats,
  loading,
  children,
  maxWidth = "max-w-7xl",
  flush,
}: {
  projectId: number;
  stats: SummaryStats;
  loading?: boolean;
  children: ReactNode;
  maxWidth?: string;
  /** Full-bleed layout (e.g. site analysis map). */
  flush?: boolean;
}) {
  return (
    <div className="app-canvas flex flex-1 flex-col min-h-0 bg-background pb-14 md:pb-0">
      <div
        className={cn(
          "flex-1 min-h-0",
          flush ? "flex flex-col overflow-hidden" : cn("overflow-y-auto px-4 py-5 sm:px-6 sm:py-6 space-y-6 mx-auto w-full", maxWidth),
        )}
      >
        {children}
      </div>
      <BottomSummaryBar stats={stats} loading={loading} />
    </div>
  );
}

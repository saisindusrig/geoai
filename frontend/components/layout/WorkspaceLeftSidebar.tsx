"use client";

import type { ReactNode } from "react";

interface WorkspaceLeftSidebarProps {
  tools: ReactNode;
  middle?: ReactNode;
  footer?: ReactNode;
  projectName?: string;
  projectType?: string;
  hasBoundary?: boolean;
  hasAlignment?: boolean;
}

/** Viewport-bound left rail — scrollable stack of tool / parameter sections. */
export default function WorkspaceLeftSidebar({
  tools,
  middle,
  footer,
  projectName,
  projectType,
}: WorkspaceLeftSidebarProps) {
  return (
    <div className="flex h-full min-h-0 flex-col overflow-hidden bg-sidebar">
      <div className="shrink-0 border-b border-border px-4 py-3">
        <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">
          Project
        </p>
        <p className="mt-1 truncate text-sm font-semibold text-foreground">
          {projectName ?? "Active workspace"}
        </p>
        <p className="mt-0.5 truncate text-[11px] text-muted-foreground">
          {projectType ?? "Infrastructure"}
        </p>
      </div>

      <div className="flex min-h-0 flex-1 flex-col gap-3 overflow-y-auto overscroll-contain p-3 scrollbar-thin-dark">
        {tools}
        {middle}
      </div>
      {footer ? (
        <div className="shrink-0 border-t border-border bg-background-secondary/80">
          {footer}
        </div>
      ) : null}
    </div>
  );
}

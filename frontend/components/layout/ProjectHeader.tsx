"use client";

import Link from "next/link";
import { Loader2 } from "lucide-react";
import type { Project } from "@/lib/types";

export function ProjectHeaderContent({
  project,
  title,
  subtitle,
  compact,
  hideSubtitle,
}: {
  project: Project;
  title?: string;
  subtitle?: string;
  compact?: boolean;
  hideSubtitle?: boolean;
}) {
  return (
    <div className="min-w-0 flex-1">
      <h1
        className={
          compact
            ? "min-w-0 font-semibold text-sm tracking-tight text-foreground truncate"
            : "min-w-0 font-semibold text-base tracking-tight text-foreground truncate"
        }
      >
        {title ?? project.name}
      </h1>
      {!hideSubtitle && (subtitle || project.location_name) && (
        <p
          className={
            compact
              ? "text-[10px] text-muted-foreground truncate mt-0.5"
              : "text-xs text-muted-foreground truncate mt-0.5"
          }
        >
          {subtitle ?? project.location_name}
        </p>
      )}
    </div>
  );
}

export default function ProjectHeader({
  project,
  title,
  subtitle,
  backHref,
}: {
  project: Project;
  title?: string;
  subtitle?: string;
  backHref?: string;
}) {
  return (
    <div className="flex items-center gap-3 px-4 py-2.5 border-b border-border bg-card shrink-0 flex-wrap">
      {backHref && (
        <Link
          href={backHref}
          className="flex h-8 w-8 items-center justify-center rounded-lg border border-border bg-card hover:bg-muted transition-colors duration-200"
        >
          ←
        </Link>
      )}
      <ProjectHeaderContent project={project} title={title} subtitle={subtitle} />
    </div>
  );
}

export function ProjectLoading({ message = "Loading project…" }: { message?: string }) {
  return (
    <div className="flex-1 flex flex-col items-center justify-center gap-3 text-muted-foreground">
      <Loader2 className="h-7 w-7 animate-spin text-primary" />
      <p className="text-sm">{message}</p>
    </div>
  );
}

export function ProjectError({ error, onRetry }: { error: string; onRetry?: () => void }) {
  return (
    <div className="flex-1 flex flex-col items-center justify-center gap-3 p-8 text-center">
      <p className="text-sm text-destructive max-w-md">{error}</p>
      {onRetry && (
        <button onClick={onRetry} className="text-sm text-primary hover:underline">
          Retry
        </button>
      )}
    </div>
  );
}

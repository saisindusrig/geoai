"use client";

import Link from "next/link";
import { Check } from "lucide-react";
import { workflowHref, WORKFLOW_STEPS, type WorkflowStepId } from "@/lib/project-workflow";
import { cn } from "@/lib/utils";

interface Props {
  projectId: number;
  hasLocation?: boolean;
  hasBoundary?: boolean;
  hasParameters?: boolean;
  hasDesign?: boolean;
  compact?: boolean;
}

export default function ProjectStepper({
  projectId,
  hasLocation,
  hasBoundary,
  hasParameters,
  hasDesign,
  compact,
}: Props) {
  const completed = [!!hasLocation, !!hasBoundary, !!hasParameters, !!hasDesign, !!hasDesign];
  const activeIdx = completed.findIndex((c) => !c);
  const current = activeIdx === -1 ? WORKFLOW_STEPS.length - 1 : activeIdx;

  return (
    <div className={cn(
      "flex items-center gap-1 overflow-x-auto",
      compact ? "py-0.5" : "px-4 py-2 border-b border-border bg-background-secondary",
    )}>
      {WORKFLOW_STEPS.map((step, i) => {
        const done = completed[i];
        const active = i === current;
        const href = workflowHref(projectId, step.id as WorkflowStepId);
        return (
          <div key={step.id} className="flex items-center gap-1 shrink-0">
            {i > 0 && !compact && <div className="w-4 h-px bg-border mx-0.5" />}
            {compact && i > 0 && <span className="text-muted-foreground text-[10px]">·</span>}
            <Link
              href={href}
              className={cn(
                "flex items-center gap-1 rounded-md font-medium transition-colors duration-200 hover:bg-muted/40",
                compact ? "px-1.5 py-0.5 text-[10px]" : "px-2 py-1 text-[11px] gap-1.5",
                done && "text-success",
                active && !done && "text-primary bg-primary/10 border border-primary/20",
                !done && !active && "text-muted-foreground",
              )}
            >
              {!compact && (
                <span
                  className={cn(
                    "flex h-4 w-4 items-center justify-center rounded-full text-[9px] border",
                    done && "bg-success/20 border-success/40 text-success",
                    active && !done && "border-primary/40 text-primary",
                    !done && !active && "border-border",
                  )}
                >
                  {done ? <Check className="h-2.5 w-2.5" /> : i + 1}
                </span>
              )}
              {compact ? (done ? "✓" : "") + step.label.split(" ")[0] : step.label}
            </Link>
          </div>
        );
      })}
    </div>
  );
}

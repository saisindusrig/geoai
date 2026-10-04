"use client";

import { useEffect } from "react";
import { Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import { toast } from "@/lib/toast";
import type { JobStatus } from "@/lib/types";
import { useProjectStore } from "@/stores/projectStore";
import { cn } from "@/lib/utils";

export default function JobStatusBar({
  onCompleted,
  compact,
}: {
  onCompleted?: () => void;
  compact?: boolean;
}) {
  const { activeJob, setActiveJob } = useProjectStore();

  useEffect(() => {
    if (!activeJob || activeJob.status === "completed" || activeJob.status === "failed") return;
    const interval = setInterval(async () => {
      try {
        const status = await api.get<JobStatus>(`/api/jobs/${activeJob.job_id}`);
        setActiveJob(status);
        if (status.status === "completed") {
          toast("Design ready", {
            variant: "success",
            description: "Model, BOQ, and cost estimate are available.",
          });
          onCompleted?.();
        }
        if (status.status === "failed") {
          toast("Generation failed", { variant: "error", description: status.error ?? undefined });
        }
      } catch {
        /* keep polling */
      }
    }, 1500);
    return () => clearInterval(interval);
  }, [activeJob, setActiveJob, onCompleted]);

  if (!activeJob) return null;

  const running = activeJob.status === "running" || activeJob.status === "queued";

  const statusLabel: Record<string, string> = {
    queued: "Queued — analyzing site",
    running: "Generating layout & estimating materials",
    completed: "Completed",
    failed: "Failed",
  };

  return (
    <div
      className={cn(
        "flex items-center gap-2 text-[11px] border-t border-border bg-background/95",
        compact ? "px-3 py-2 flex-wrap" : "h-10 px-5 gap-3 text-[12px]",
      )}
    >
      {running ? (
        <Loader2 className="h-3.5 w-3.5 animate-spin text-primary" />
      ) : (
        <span
          className={cn(
            "w-2 h-2 rounded-full shrink-0",
            activeJob.status === "completed" ? "bg-success" : activeJob.status === "failed" ? "bg-destructive" : "bg-accent",
          )}
        />
      )}
      <span className="font-medium text-foreground">
        {statusLabel[activeJob.status] ?? activeJob.status}
      </span>
      {activeJob.error && <span className="text-destructive truncate">— {activeJob.error}</span>}
      {activeJob.status === "completed" && (
        <span className="text-success">Model, quantities, and cost estimate are ready.</span>
      )}
      <button
        type="button"
        onClick={() => setActiveJob(null)}
        className="ml-auto text-muted-foreground hover:text-foreground text-[11px]"
      >
        Dismiss
      </button>
    </div>
  );
}

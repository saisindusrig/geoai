"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import { formatApiErrorMessage } from "@/lib/api";
import { toast } from "@/lib/toast";
import type { JobStatus } from "@/lib/types";
import { useProjectStore } from "@/stores/projectStore";

function terminalMessage(job: JobStatus): string {
  if (job.safe_error_message) return job.safe_error_message;
  if (job.message) return job.message;
  if (job.error) return job.error;
  return "Generation failed.";
}

/** Poll active generation job and refresh project data when preview/completion events fire. */
export function useActiveJobPolling(options?: {
  enabled?: boolean;
  onCompleted?: () => void;
  onPreviewReady?: () => void;
}) {
  const { activeJob, setActiveJob } = useProjectStore();
  const [cancelling, setCancelling] = useState(false);
  const previewNotifiedRef = useRef<string | null>(null);
  const completeNotifiedRef = useRef<string | null>(null);
  const failedNotifiedRef = useRef<string | null>(null);
  const cancelledNotifiedRef = useRef<string | null>(null);
  const onCompleted = options?.onCompleted;
  const enabled = options?.enabled ?? true;
  const onPreviewReady = options?.onPreviewReady;

  const cancelJob = useCallback(async () => {
    if (!enabled || !activeJob?.job_id) return;
    if (activeJob.status === "completed" || activeJob.status === "failed" || activeJob.status === "cancelled") {
      return;
    }
    setCancelling(true);
    try {
      await api.post(`/api/jobs/${activeJob.job_id}/cancel`);
      const status = await api.get<JobStatus>(`/api/jobs/${activeJob.job_id}`);
      setActiveJob(status);
      toast("Generation cancelled", { variant: "default" });
    } catch (e) {
      toast("Could not cancel job", {
        variant: "error",
        description: formatApiErrorMessage(e),
      });
    } finally {
      setCancelling(false);
    }
  }, [activeJob, setActiveJob, enabled]);

  useEffect(() => {
    if (
      !enabled || !activeJob ||
      activeJob.status === "completed" ||
      activeJob.status === "failed" ||
      activeJob.status === "cancelled"
    ) {
      return;
    }
    const interval = window.setInterval(async () => {
      try {
        const status = await api.get<JobStatus>(`/api/jobs/${activeJob.job_id}`);
        setActiveJob(status);

        if (status.preview_ready && status.preview_glb_url) {
          const token = `${status.job_id}:preview`;
          if (previewNotifiedRef.current !== token) {
            previewNotifiedRef.current = token;
            onPreviewReady?.();
          }
        }

        if (status.status === "completed" || status.stage === "completed") {
          const token = `${status.job_id}:completed`;
          if (completeNotifiedRef.current !== token) {
            completeNotifiedRef.current = token;
            toast("Design generated successfully", { variant: "success" });
            onCompleted?.();
          }
        }

        if (status.status === "failed" || status.stage === "failed") {
          const token = `${status.job_id}:failed`;
          if (failedNotifiedRef.current !== token) {
            failedNotifiedRef.current = token;
            toast("Generation failed", {
              variant: "error",
              description: terminalMessage(status),
            });
          }
        }

        if (status.status === "cancelled" || status.stage === "cancelled") {
          const token = `${status.job_id}:cancelled`;
          if (cancelledNotifiedRef.current !== token) {
            cancelledNotifiedRef.current = token;
            toast("Generation cancelled", { variant: "default" });
          }
        }
      } catch {
        // Keep polling on transient failures.
      }
    }, 1000);
    return () => window.clearInterval(interval);
  }, [activeJob, onCompleted, onPreviewReady, setActiveJob, enabled]);

  return { cancelJob, cancelling };
}

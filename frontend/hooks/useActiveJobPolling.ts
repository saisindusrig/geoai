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
  const [pausedJob, setPausedJob] = useState<{ id: string; message: string } | null>(null);
  const [pollVersion, setPollVersion] = useState(0);
  const [cancelling, setCancelling] = useState(false);
  const previewNotifiedRef = useRef<string | null>(null);
  const completeNotifiedRef = useRef<string | null>(null);
  const failedNotifiedRef = useRef<string | null>(null);
  const cancelledNotifiedRef = useRef<string | null>(null);
  const onCompleted = options?.onCompleted;
  const enabled = options?.enabled ?? true;
  const onPreviewReady = options?.onPreviewReady;
  const callbacksRef = useRef({ onCompleted, onPreviewReady });
  useEffect(() => {
    callbacksRef.current = { onCompleted, onPreviewReady };
  }, [onCompleted, onPreviewReady]);
  const jobId = activeJob?.job_id;
  const terminal = !activeJob || [activeJob.status, activeJob.stage].some(value => ["completed", "failed", "cancelled"].includes(value ?? ""));
  const pollingError = !terminal && pausedJob && pausedJob.id === jobId ? pausedJob.message : null;
  const retryPolling = useCallback(() => {
    setPausedJob(null);
    setPollVersion(value => value + 1);
  }, []);

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
    if (!enabled || !jobId || terminal) return;
    let disposed = false;
    let failures = 0;
    let timer: number;
    const poll = async () => {
      let finished = false;
      try {
        const status = await api.get<JobStatus>(`/api/jobs/${jobId}`);
        if (disposed) return;
        failures = 0;
        setPausedJob(null);
        finished = [status.status, status.stage].some(value => ["completed", "failed", "cancelled"].includes(value ?? ""));
        setActiveJob(status);

        if (status.preview_ready && status.preview_glb_url) {
          const token = `${status.job_id}:preview`;
          if (previewNotifiedRef.current !== token) {
            previewNotifiedRef.current = token;
            callbacksRef.current.onPreviewReady?.();
          }
        }

        if (status.status === "completed" || status.stage === "completed") {
          const token = `${status.job_id}:completed`;
          if (completeNotifiedRef.current !== token) {
            completeNotifiedRef.current = token;
            toast("Design generated successfully", { variant: "success" });
            callbacksRef.current.onCompleted?.();
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
      } catch (error) {
        if (disposed) return;
        failures += 1;
        if (failures >= 5) {
          setPausedJob({ id: jobId, message: formatApiErrorMessage(error) });
          toast("Job status polling paused", { variant: "error", description: formatApiErrorMessage(error) });
          return;
        }
      }
      if (!disposed && !finished) timer = window.setTimeout(poll, 1000 * 2 ** failures);
    };
    timer = window.setTimeout(poll, 1000);
    return () => { disposed = true; window.clearTimeout(timer); };
  }, [jobId, terminal, setActiveJob, enabled, pollVersion]);

  return { cancelJob, cancelling, pollingError, retryPolling };
}

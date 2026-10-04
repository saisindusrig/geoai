import type { GeneratedFileInfo, JobStatus, ScenarioSummary } from "@/lib/types";

export type ModelUrlSource =
  | "job_final"
  | "job_preview"
  | "scenario_detail_files"
  | "scenario_detail_model_url"
  | "scenario_summary"
  | "project_files"
  | "latest_summary"
  | null;

export interface ResolvedModelUrls {
  modelUrl: string | null;
  modelSource: ModelUrlSource;
  excavationUrl: string | null;
  excavationSource: ModelUrlSource;
}

export interface ResolveModelUrlInput {
  activeJob?: JobStatus | null;
  /** True while a generation job is actively running (not completed/failed). */
  generating?: boolean;
  scenarioId?: number | null;
  /** Files from GET /exports/files for the project. */
  projectFiles?: GeneratedFileInfo[];
  /** Files from GET /scenarios/{id} detail `generated_files`. */
  scenarioDetailFiles?: GeneratedFileInfo[];
  /** Summary for the currently selected scenario. */
  activeSummary?: ScenarioSummary | null;
  /** All scenario summaries (newest first). */
  scenarioSummaries?: ScenarioSummary[];
  /** Optional model_url from scenario detail payload (same as summary when present). */
  scenarioDetailModelUrl?: string | null;
}

export function isJobGenerating(job: JobStatus | null | undefined): boolean {
  if (!job) return false;
  if (job.status === "completed" || job.status === "failed" || job.status === "cancelled") return false;
  if (job.stage === "completed" || job.stage === "failed" || job.stage === "cancelled") return false;
  return true;
}

/** Final GLB from a completed generation job (`result.glb_url` or preview fallback). */
export function jobFinalGlbUrl(job: JobStatus | null | undefined): string | null {
  if (!job) return null;
  const completed = job.status === "completed" || job.stage === "completed";
  if (!completed) return null;

  const result = job.result;
  if (result && typeof result === "object") {
    const record = result as Record<string, unknown>;
    const fromResult =
      (typeof record.final_glb_url === "string" && record.final_glb_url) ||
      (typeof record.glb_url === "string" && record.glb_url) ||
      null;
    if (fromResult) return fromResult;
  }
  if (typeof job.final_glb_url === "string" && job.final_glb_url) {
    return job.final_glb_url;
  }
  return job.preview_glb_url ?? null;
}

export function jobExcavationGlbUrl(job: JobStatus | null | undefined): string | null {
  if (!job) return null;
  const completed = job.status === "completed" || job.stage === "completed";
  if (!completed) return null;
  const result = job.result;
  if (result && typeof result === "object") {
    const url = (result as Record<string, unknown>).excavation_glb_url;
    if (typeof url === "string" && url) return url;
  }
  return null;
}

function glbFromFiles(
  files: GeneratedFileInfo[] | undefined,
  scenarioId: number | null | undefined,
  fileType: "glb" | "glb-excavation",
): string | null {
  if (!files?.length) return null;
  const match =
    files.find((f) => f.file_type === fileType && (scenarioId == null || f.scenario_id === scenarioId)) ??
    files.find((f) => f.file_type === fileType);
  return match?.file_url ?? null;
}

function latestSummaryWithModel(summaries: ScenarioSummary[] | undefined): ScenarioSummary | null {
  if (!summaries?.length) return null;
  return summaries.find((s) => s.status === "completed" && s.model_url) ?? summaries.find((s) => s.model_url) ?? null;
}

/**
 * Resolve the best model + excavation URLs.
 *
 * Priority (saved models beat stale running jobs):
 * 1. Completed job final GLB
 * 2. Selected scenario detail generated files
 * 3. Selected scenario detail / summary `model_url`
 * 4. Project files API for selected scenario
 * 5. Latest completed scenario summary `model_url`
 *
 * During active generation only: live preview URL overrides when `preview_ready`.
 */
export function resolveModelUrls(input: ResolveModelUrlInput): ResolvedModelUrls {
  const generating = input.generating ?? isJobGenerating(input.activeJob);
  const scenarioId = input.scenarioId ?? input.activeSummary?.scenario_id ?? null;

  if (generating && input.activeJob?.preview_ready && input.activeJob.preview_glb_url) {
    return {
      modelUrl: input.activeJob.preview_glb_url,
      modelSource: "job_preview",
      excavationUrl: null,
      excavationSource: null,
    };
  }

  const finalJobUrl = jobFinalGlbUrl(input.activeJob);
  if (finalJobUrl) {
    return {
      modelUrl: finalJobUrl,
      modelSource: "job_final",
      excavationUrl: jobExcavationGlbUrl(input.activeJob),
      excavationSource: jobExcavationGlbUrl(input.activeJob) ? "job_final" : null,
    };
  }

  const detailFilesUrl = glbFromFiles(input.scenarioDetailFiles, scenarioId, "glb");
  if (detailFilesUrl) {
    return {
      modelUrl: detailFilesUrl,
      modelSource: "scenario_detail_files",
      excavationUrl: glbFromFiles(input.scenarioDetailFiles, scenarioId, "glb-excavation"),
      excavationSource: glbFromFiles(input.scenarioDetailFiles, scenarioId, "glb-excavation")
        ? "scenario_detail_files"
        : null,
    };
  }

  const detailModelUrl = input.scenarioDetailModelUrl ?? input.activeSummary?.model_url ?? null;
  if (detailModelUrl) {
    return {
      modelUrl: detailModelUrl,
      modelSource: input.scenarioDetailModelUrl ? "scenario_detail_model_url" : "scenario_summary",
      excavationUrl: glbFromFiles(input.projectFiles, scenarioId, "glb-excavation"),
      excavationSource: glbFromFiles(input.projectFiles, scenarioId, "glb-excavation")
        ? "project_files"
        : null,
    };
  }

  const projectFilesUrl = glbFromFiles(input.projectFiles, scenarioId, "glb");
  if (projectFilesUrl) {
    return {
      modelUrl: projectFilesUrl,
      modelSource: "project_files",
      excavationUrl: glbFromFiles(input.projectFiles, scenarioId, "glb-excavation"),
      excavationSource: glbFromFiles(input.projectFiles, scenarioId, "glb-excavation")
        ? "project_files"
        : null,
    };
  }

  const latest = latestSummaryWithModel(input.scenarioSummaries);
  if (latest?.model_url) {
    return {
      modelUrl: latest.model_url,
      modelSource: "latest_summary",
      excavationUrl: glbFromFiles(input.projectFiles, latest.scenario_id, "glb-excavation"),
      excavationSource: glbFromFiles(input.projectFiles, latest.scenario_id, "glb-excavation")
        ? "project_files"
        : null,
    };
  }

  return {
    modelUrl: null,
    modelSource: null,
    excavationUrl: null,
    excavationSource: null,
  };
}

/** @deprecated Use resolveModelUrls */
export function resolveModelUrl(input: ResolveModelUrlInput): string | null {
  return resolveModelUrls(input).modelUrl;
}

export function hasCompletedGlbModel(resolved: ResolvedModelUrls): boolean {
  if (!resolved.modelUrl) return false;
  return resolved.modelSource !== "job_preview";
}

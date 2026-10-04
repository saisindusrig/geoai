/** Job stage helpers shared by frontend. */

export type JobStage =
  | "queued"
  | "analyzing_site"
  | "generating_layout"
  | "generating_3d_preview"
  | "calculating_boq"
  | "exporting_model"
  | "saving_result"
  | "completed"
  | "failed"
  | "cancelled";

export type GenerationMode = "fast_preview" | "balanced" | "high_detail";

export const GENERATION_MODE_LABELS: Record<GenerationMode, string> = {
  fast_preview: "Fast Preview",
  balanced: "Balanced",
  high_detail: "High Detail",
};

export const JOB_STAGE_STEPS: { stage: JobStage; label: string }[] = [
  { stage: "queued", label: "Queued" },
  { stage: "analyzing_site", label: "Reading site geometry" },
  { stage: "generating_layout", label: "Generating layout" },
  { stage: "generating_3d_preview", label: "Generating 3D preview" },
  { stage: "calculating_boq", label: "Calculating BOQ" },
  { stage: "exporting_model", label: "Exporting model" },
  { stage: "saving_result", label: "Saving result" },
];

export function jobStageIndex(stage?: JobStage | null): number {
  if (!stage) return -1;
  return JOB_STAGE_STEPS.findIndex((s) => s.stage === stage);
}

export function isJobActive(status?: string, stage?: JobStage | null): boolean {
  if (
    status === "completed" ||
    status === "failed" ||
    status === "cancelled" ||
    stage === "completed" ||
    stage === "failed" ||
    stage === "cancelled"
  ) {
    return false;
  }
  return Boolean(status);
}

export function stageLabel(stage: JobStage | "idle"): string {
  if (stage === "idle") return "Idle";
  const found = JOB_STAGE_STEPS.find((s) => s.stage === stage);
  if (found) return found.label;
  return stage.replace(/_/g, " ");
}

export function stageMapLabel(stage: JobStage | "idle"): string {
  switch (stage) {
    case "queued":
      return "Preparing generation…";
    case "analyzing_site":
      return "Reading site geometry";
    case "generating_layout":
      return "Generating layout";
    case "generating_3d_preview":
      return "Generating 3D layout";
    case "calculating_boq":
      return "Estimating quantities";
    case "exporting_model":
    case "saving_result":
      return "Finalizing design";
    default:
      return "";
  }
}

import type { DesignScenario, GeneratedFileInfo, ScenarioListResponse, ScenarioSummary } from "@/lib/types";

/** Full scenarios embedded in legacy list responses (pre–Phase 5 API). */
export function extractLegacyScenarios(
  data: ScenarioListResponse | ScenarioSummary[] | DesignScenario[],
): Map<number, DesignScenario> {
  const map = new Map<number, DesignScenario>();
  if (!Array.isArray(data)) return map;
  for (const item of data) {
    if ("id" in item && "design_output_json" in item) {
      map.set(item.id, item as DesignScenario);
    }
  }
  return map;
}

export function parseScenarioList(
  data: ScenarioListResponse | ScenarioSummary[] | DesignScenario[],
): ScenarioSummary[] {
  if (Array.isArray(data)) {
    return data.map((item) => {
      if ("scenario_id" in item) return item as ScenarioSummary;
      const legacy = item as DesignScenario;
      return {
        scenario_id: legacy.id,
        name: legacy.name,
        status: legacy.status,
        created_at: legacy.created_at,
        cost_total: legacy.design_output_json?.calculated?.cost_summary?.total_medium ?? null,
        validation_score: legacy.design_output_json?.design_review?.validation_score ?? null,
        validation_status: legacy.design_output_json?.validation?.validation_status ?? null,
        geometry_mode: legacy.design_output_json?.geometry_spec?.geometry_mode ?? null,
        elevation_mode: legacy.design_output_json?.geometry_spec?.elevation_mode ?? null,
        warning_count: legacy.design_output_json?.design_review?.warnings?.length ?? 0,
      };
    });
  }
  return data.summaries ?? data.scenarios ?? [];
}

export function detailToDesignScenario(detail: Record<string, unknown>): DesignScenario {
  return {
    id: detail.scenario_id as number,
    name: detail.name as string,
    status: detail.status as string,
    input_parameters_json: (detail.input_parameters as Record<string, unknown>) ?? null,
    design_output_json: (detail.design_output as DesignScenario["design_output_json"]) ?? null,
    assumptions_json: (detail.assumptions as string[]) ?? null,
    created_at: (detail.created_at as string) ?? new Date().toISOString(),
  };
}

export function extractGeneratedFilesFromDetail(detail: Record<string, unknown>): GeneratedFileInfo[] {
  const raw = detail.generated_files;
  if (!Array.isArray(raw)) return [];
  return raw
    .map((item) => {
      if (!item || typeof item !== "object") return null;
      const row = item as Record<string, unknown>;
      const fileUrl = row.file_url;
      const fileType = row.file_type;
      if (typeof fileUrl !== "string" || typeof fileType !== "string") return null;
      return {
        id: typeof row.id === "number" ? row.id : 0,
        file_type: fileType,
        file_url: fileUrl,
        scenario_id: typeof detail.scenario_id === "number" ? detail.scenario_id : null,
        created_at: typeof detail.created_at === "string" ? detail.created_at : "",
      } satisfies GeneratedFileInfo;
    })
    .filter((f): f is GeneratedFileInfo => f != null);
}

export function detailModelUrl(detail: Record<string, unknown>): string | null {
  const url = detail.model_url;
  return typeof url === "string" && url ? url : null;
}

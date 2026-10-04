"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { api, ApiError } from "@/lib/api";
import { logModelViewerState } from "@/lib/model-viewer-debug";
import {
  hasCompletedGlbModel,
  isJobGenerating,
  resolveModelUrls,
  type ResolvedModelUrls,
} from "@/lib/model-url-resolution";
import { modelLayerEnableState } from "@/lib/model-viewer-state";
import { resolveWorkspaceMapEngine } from "@/lib/map/workspace-engine";
import {
  detailModelUrl,
  detailToDesignScenario,
  extractGeneratedFilesFromDetail,
  extractLegacyScenarios,
  parseScenarioList,
} from "@/lib/scenario-api";
import type {
  DesignScenario,
  GeneratedFileInfo,
  JobStatus,
  Project,
  QuantityEstimate,
  ScenarioListResponse,
  ScenarioSummary,
  SiteAnalysis,
} from "@/lib/types";
import type { SummaryStats } from "@/components/layout/BottomSummaryBar";
import { localSandboxProject } from "@/lib/local-sandbox";
import { useProjectStore } from "@/stores/projectStore";

const scenarioStorageKey = (projectId: number) => `project-${projectId}-scenario-id`;

export function useProjectData(
  projectId: number,
  options?: {
    activeJob?: JobStatus | null;
    publicDemo?: boolean;
    localSandbox?: boolean;
  },
) {
  const [project, setProject] = useState<Project | null>(null);
  const [scenarioSummaries, setScenarioSummaries] = useState<ScenarioSummary[]>([]);
  const [scenario, setScenario] = useState<DesignScenario | null>(null);
  const [scenarioDetailFiles, setScenarioDetailFiles] = useState<GeneratedFileInfo[]>([]);
  const [scenarioDetailModelUrl, setScenarioDetailModelUrl] = useState<string | null>(null);
  const [estimate, setEstimate] = useState<QuantityEstimate | null>(null);
  const [analysis, setAnalysis] = useState<SiteAnalysis | null>(null);
  const [files, setFiles] = useState<GeneratedFileInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const legacyScenariosRef = useRef<Map<number, DesignScenario>>(new Map());
  const activeJob = options?.activeJob ?? null;
  const publicDemo = options?.publicDemo ?? false;
  const localSandbox = options?.localSandbox ?? false;

  const pickSummary = useCallback((list: ScenarioSummary[], preferredId?: number | null) => {
    if (preferredId) {
      const found = list.find((s) => s.scenario_id === preferredId);
      if (found) return found;
    }
    return list.find((s) => s.status === "completed") ?? list[0] ?? null;
  }, []);

  const applyScenarioDetail = useCallback((detail: Record<string, unknown>) => {
    const mapped = detailToDesignScenario(detail);
    setScenario(mapped);
    setScenarioDetailFiles(extractGeneratedFilesFromDetail(detail));
    setScenarioDetailModelUrl(detailModelUrl(detail));
    const spec = mapped.design_output_json?.geometry_spec;
    if (spec) {
      useProjectStore.getState().syncDesignMeshFromSpec(spec);
    }
    return mapped;
  }, []);

  const loadScenarioDetail = useCallback(
    async (summary: ScenarioSummary, legacy?: Map<number, DesignScenario>) => {
      const legacyScenario = legacy?.get(summary.scenario_id);
      if (legacyScenario?.design_output_json) {
        setScenario(legacyScenario);
        setScenarioDetailFiles([]);
        setScenarioDetailModelUrl(null);
        const spec = legacyScenario.design_output_json?.geometry_spec;
        if (spec) {
          useProjectStore.getState().syncDesignMeshFromSpec(spec);
        }
        if (typeof window !== "undefined") {
          localStorage.setItem(scenarioStorageKey(projectId), String(summary.scenario_id));
        }
        return legacyScenario;
      }

      const detail = await api.getOptional<Record<string, unknown>>(
        `/api/projects/${projectId}/scenarios/${summary.scenario_id}`,
      );
      if (detail) {
        const mapped = applyScenarioDetail(detail);
        if (typeof window !== "undefined") {
          localStorage.setItem(scenarioStorageKey(projectId), String(summary.scenario_id));
        }
        return mapped;
      }

      if (legacyScenario) {
        setScenario(legacyScenario);
        setScenarioDetailFiles([]);
        setScenarioDetailModelUrl(null);
        return legacyScenario;
      }

      throw new ApiError(404, "Scenario not found");
    },
    [applyScenarioDetail, projectId],
  );

  const load = useCallback(async (loadOptions?: { silent?: boolean }) => {
    if (!projectId || Number.isNaN(projectId)) return;
    if (!loadOptions?.silent) {
      setLoading(true);
    }
    setError("");
    try {
      if (localSandbox) {
        const sandboxProject = localSandboxProject();
        setProject(sandboxProject);
        useProjectStore.getState().setProject(sandboxProject);
        setScenarioSummaries([]);
        setScenario(null);
        setScenarioDetailFiles([]);
        setScenarioDetailModelUrl(null);
        setFiles([]);
        setEstimate(null);
        setAnalysis(null);
        return;
      }
      if (publicDemo) {
        const demoProject = await api.get<Project>("/api/projects/demo");
        setProject(demoProject);
        useProjectStore.getState().setProject(demoProject);
        setScenarioSummaries([]);
        setScenario(null);
        setScenarioDetailFiles([]);
        setScenarioDetailModelUrl(null);
        setFiles([]);
        setEstimate(null);
        setAnalysis(null);
        return;
      }
      const storedId =
        typeof window !== "undefined"
          ? Number(localStorage.getItem(scenarioStorageKey(projectId)) || "") || null
          : null;

      const [p, scenarioRes, fileList] = await Promise.all([
        api.get<Project>(`/api/projects/${projectId}`),
        api.get<ScenarioListResponse | ScenarioSummary[] | DesignScenario[]>(
          `/api/projects/${projectId}/scenarios`,
        ),
        api.get<GeneratedFileInfo[]>(`/api/projects/${projectId}/exports/files`),
      ]);
      setProject(p);
      useProjectStore.getState().setProject(p);
      const legacyScenarios = extractLegacyScenarios(scenarioRes);
      legacyScenariosRef.current = legacyScenarios;
      const summaries = parseScenarioList(scenarioRes);
      setScenarioSummaries(summaries);
      setFiles(fileList);

      const picked = pickSummary(summaries, storedId);
      if (picked) {
        try {
          await loadScenarioDetail(picked, legacyScenarios);
        } catch (e) {
          if (e instanceof ApiError && e.status === 404 && typeof window !== "undefined") {
            localStorage.removeItem(scenarioStorageKey(projectId));
          }
          const fallback = pickSummary(summaries, null);
          if (fallback && fallback.scenario_id !== picked.scenario_id) {
            await loadScenarioDetail(fallback, legacyScenarios);
          } else {
            setScenario(null);
            setScenarioDetailFiles([]);
            setScenarioDetailModelUrl(null);
          }
        }
      } else {
        setScenario(null);
        setScenarioDetailFiles([]);
        setScenarioDetailModelUrl(null);
      }

      const [e, a] = await Promise.all([
        api.getOptional<QuantityEstimate>(`/api/projects/${projectId}/estimates`),
        api.getOptional<SiteAnalysis>(`/api/projects/${projectId}/site-analysis`),
      ]);
      setEstimate(e);
      setAnalysis(a);
    } catch (e) {
      setError(String(e instanceof Error ? e.message : e));
    } finally {
      if (!loadOptions?.silent) {
        setLoading(false);
      }
    }
  }, [projectId, pickSummary, loadScenarioDetail, publicDemo, localSandbox]);

  useEffect(() => {
    let cancelled = false;
    void Promise.resolve().then(async () => {
      if (cancelled) return;
      await load();
    });
    return () => {
      cancelled = true;
    };
  }, [load]);

  const selectScenario = useCallback(
    async (summary: ScenarioSummary) => {
      await loadScenarioDetail(summary, legacyScenariosRef.current);
    },
    [loadScenarioDetail],
  );

  const scenarios: DesignScenario[] = useMemo(
    () =>
      scenarioSummaries.map((s) => ({
        id: s.scenario_id,
        name: s.name,
        status: s.status,
        created_at: s.created_at ?? "",
        input_parameters_json: null,
        design_output_json:
          scenario?.id === s.scenario_id ? scenario.design_output_json : null,
        assumptions_json: scenario?.id === s.scenario_id ? scenario.assumptions_json : s.key_assumptions ?? null,
      })),
    [scenarioSummaries, scenario],
  );

  const calc = scenario?.design_output_json?.calculated;
  const activeSummary = scenarioSummaries.find((s) => s.scenario_id === scenario?.id);

  const generating = isJobGenerating(activeJob);

  const resolvedModels: ResolvedModelUrls = useMemo(
    () =>
      resolveModelUrls({
        activeJob,
        generating,
        scenarioId: scenario?.id ?? null,
        projectFiles: files,
        scenarioDetailFiles,
        activeSummary,
        scenarioSummaries,
        scenarioDetailModelUrl,
      }),
    [
      activeJob,
      generating,
      scenario?.id,
      files,
      scenarioDetailFiles,
      activeSummary,
      scenarioSummaries,
      scenarioDetailModelUrl,
    ],
  );

  const modelFile = useMemo((): GeneratedFileInfo | undefined => {
    if (!resolvedModels.modelUrl) return undefined;
    return {
      id: 0,
      file_type: "glb",
      file_url: resolvedModels.modelUrl,
      scenario_id: scenario?.id ?? activeSummary?.scenario_id ?? null,
      created_at: activeSummary?.created_at ?? "",
    };
  }, [resolvedModels.modelUrl, scenario?.id, activeSummary]);

  const excavationFile = useMemo((): GeneratedFileInfo | undefined => {
    if (!resolvedModels.excavationUrl) return undefined;
    return {
      id: 0,
      file_type: "glb-excavation",
      file_url: resolvedModels.excavationUrl,
      scenario_id: scenario?.id ?? activeSummary?.scenario_id ?? null,
      created_at: activeSummary?.created_at ?? "",
    };
  }, [resolvedModels.excavationUrl, scenario?.id, activeSummary]);

  useEffect(() => {
    if (!project || !resolvedModels.modelUrl) return;
    const enable = modelLayerEnableState(project.project_type, true);
    useProjectStore.getState().setLayers(enable.layers);
    useProjectStore.getState().setScene3dLayers(enable.scene3dLayers);

    logModelViewerState({
      scenarioId: scenario?.id ?? null,
      modelUrl: resolvedModels.modelUrl,
      modelSource: resolvedModels.modelSource,
      mapEngine: resolveWorkspaceMapEngine(hasCompletedGlbModel(resolvedModels)),
      projectModelLayerEnabled: enable.projectModelEnabled,
      generating,
    });
  }, [
    project,
    resolvedModels,
    scenario?.id,
    generating,
  ]);

  const summaryStats: SummaryStats = {
    totalCost:
      estimate?.total_cost_estimate ??
      activeSummary?.cost_total ??
      calc?.cost_summary.total_medium,
    cementBags: estimate?.cement_bags ?? calc?.quantities.cement_bags,
    steelKg: estimate?.steel_kg ?? calc?.quantities.steel_kg,
    excavationM3: estimate?.excavation_m3 ?? calc?.quantities.excavation_m3,
    timelineMonths: calc?.timeline.estimated_months_medium as number | undefined,
    areaSqm: analysis?.area_sqm ?? undefined,
    riskScore: analysis?.risks_json?.length
      ? Math.min(10, analysis.risks_json.length + 3)
      : scenario?.design_output_json?.risks?.length
        ? Math.min(10, scenario.design_output_json.risks.length + 4)
        : undefined,
    currency: calc?.cost_summary.currency,
  };

  return {
    project,
    scenarios,
    scenarioSummaries,
    scenario,
    selectScenario,
    estimate,
    analysis,
    files,
    loading,
    error,
    load,
    calc,
    modelFile,
    excavationFile,
    resolvedModels,
    summaryStats,
    design: scenario?.design_output_json ?? null,
  };
}

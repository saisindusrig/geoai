"use client";

import { useParams, useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import BottomSummaryBar from "@/components/layout/BottomSummaryBar";
import {
  ProjectError,
  ProjectLoading,
} from "@/components/layout/ProjectHeader";
import WorkspaceLayout from "@/components/layout/WorkspaceLayout";
import WorkspaceMapEngine from "@/components/map/WorkspaceMapEngine";
import { ProfessionalModelPanel } from "@/components/model-editor/ProfessionalModelEditor";
import WorkspaceToolRail from "@/components/workspace/WorkspaceToolRail";
import BuildingAssistant from "@/components/workspace/BuildingAssistant";
import EmptyProjectStarter from "@/components/workspace/EmptyProjectStarter";
import SandboxWorkspace from "@/components/sandbox/SandboxWorkspace";
import { assetSupportsGeneration } from "@/lib/asset-types";
import { Button } from "@/components/ui/button";
import { Sun, Search, Sparkles } from "lucide-react";
import { useEditableModelEditor } from "@/hooks/useEditableModelEditor";
import { useProjectData } from "@/hooks/useProjectData";
import { useActiveJobPolling } from "@/hooks/useActiveJobPolling";
import { isJobGenerating } from "@/lib/model-url-resolution";
import {
  api,
  formatApiErrorMessage,
  isUsageLimitError,
  ApiError,
} from "@/lib/api";
import { toast, toastPromise } from "@/lib/toast";
import type { GeoJSONGeometry, GenerationMode, JobStatus } from "@/lib/types";
import { useProjectStore } from "@/stores/projectStore";

export default function WorkspacePage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const searchParams = useSearchParams();
  const projectId = Number(params.id);
  const isPublicDemo = searchParams.get("demo") === "1";
  const isLocalSandbox = searchParams.get("local") === "1";
  const { setActiveJob, activeJob } = useProjectStore();
  const {
    project,
    scenario,
    design,
    modelFile,
    excavationFile,
    resolvedModels,
    summaryStats,
    loading,
    error,
    load,
  } = useProjectData(projectId, {
    activeJob,
    publicDemo: isPublicDemo,
    localSandbox: isLocalSandbox,
  });

  const { cancelJob, cancelling } = useActiveJobPolling({
    enabled: !isLocalSandbox,
    onCompleted: () => load({ silent: true }),
    onPreviewReady: () => load({ silent: true }),
  });

  const [pendingParams, setPendingParams] = useState<Record<
    string,
    unknown
  > | null>(null);
  const generationMode: GenerationMode = "balanced";

  const [mapCreditsContainer, setMapCreditsContainer] = useState<HTMLDivElement | null>(null);
  const [buildingAssistantOpen, setBuildingAssistantOpen] = useState(false);
  const showBuildingJob = async (jobId: string, scenarioId?: number | null) => {
    const job = await api.get<JobStatus>(`/api/jobs/${jobId}`);
    if (scenarioId) localStorage.setItem(`project-${projectId}-scenario-id`, String(scenarioId));
    setActiveJob(job);
    if (job.status === "completed") await load({ silent: true });
  };

  const generate = useCallback(
    async (
      parameters: Record<string, unknown>,
      mode: GenerationMode = generationMode,
    ) => {
      if (project && !assetSupportsGeneration(project.project_type)) {
        toast("Engineering generation is unavailable for this reference asset", { variant: "error" });
        return;
      }
      try {
        const res = await api.post<{ job_id: string; generation_mode: string }>(
          `/api/projects/${projectId}/design/generate`,
          {
            scenario_name: `Scenario ${new Date().toLocaleTimeString()}`,
            parameters,
            generation_mode: mode,
          },
        );
        setActiveJob({
          job_id: res.job_id,
          status: "queued",
          stage: "queued",
          stage_label: "Queued",
          progress: 5,
          preview_ready: false,
          preview_glb_url: null,
          message: "Preparing generation",
          result: null,
          error: null,
        } as JobStatus);
        toast("Design generation started", { variant: "default" });
      } catch (e) {
        const requestHint =
          e instanceof ApiError && e.requestId
            ? ` Request ID: ${e.requestId}`
            : "";
        if (isUsageLimitError(e)) {
          toast("Usage limit reached", {
            variant: "error",
            description: `${formatApiErrorMessage(e)}${requestHint}`,
          });
          return;
        }
        if (e instanceof ApiError && e.status === 403) {
          toast("Access denied", {
            variant: "error",
            description: `${formatApiErrorMessage(e)}${requestHint}`,
          });
          return;
        }
        if (e instanceof ApiError && e.status >= 500) {
          toast("Server error", {
            variant: "error",
            description: `${formatApiErrorMessage(e)}${requestHint}`,
          });
          return;
        }
        toast("Generation failed", {
          variant: "error",
          description: `${formatApiErrorMessage(e)}${requestHint}`,
        });
      }
    },
    [projectId, setActiveJob, generationMode, project],
  );

  const saveBoundary = async (g: GeoJSONGeometry) => {
    await toastPromise(
      api.put(`/api/projects/${projectId}`, { boundary_geojson: g }),
      {
        loading: "Saving boundary…",
        success: "Boundary saved",
      },
    );
    load();
  };

  const saveAlignment = async (g: GeoJSONGeometry) => {
    await toastPromise(
      api.put(`/api/projects/${projectId}`, { alignment_geojson: g }),
      {
        loading: "Saving alignment…",
        success: "Alignment saved",
      },
    );
    load();
  };

  const saveLocation = async (lng: number, lat: number, name: string) => {
    await toastPromise(
      api.put(`/api/projects/${projectId}`, {
        center_lng: lng,
        center_lat: lat,
        location_name: name,
      }),
      { loading: "Updating location…", success: "Location updated" },
    );
    load();
  };

  const runSiteAnalysis = useCallback(async () => {
    await toastPromise(api.post(`/api/projects/${projectId}/site-analysis`), {
      loading: "Running site analysis…",
      success: "Site analysis complete",
      error: "Site analysis failed — draw a boundary or alignment first",
    });
    load();
  }, [projectId, load]);
  const analyzeSite = () => router.push(`/projects/${projectId}/analysis`);

  useEffect(() => {
    if (typeof window === "undefined" || loading) return;
    if (window.location.hash === "#parameters") {
      document
        .getElementById("parameters-panel")
        ?.scrollIntoView({ behavior: "smooth" });
    }
    if (window.location.hash === "#copilot") {
      window.dispatchEvent(new CustomEvent("geoai:open-copilot"));
    }
  }, [loading]);

  useEffect(() => {
    if (!isLocalSandbox || !project) return;
    useProjectStore.getState().setLayers({ projectModel: true, satellite: true });
    useProjectStore.getState().setScene3dLayers({ flyover: true });
  }, [isLocalSandbox, project]);

  const modelEditor = useEditableModelEditor({
    project,
    scenario,
    localSandbox: isLocalSandbox,
    onSaved: () => load({ silent: true }),
  });

  if (loading) return <ProjectLoading />;
  if (error || !project)
    return <ProjectError error={error || "Project not found"} onRetry={load} />;
  if (isLocalSandbox) return <SandboxWorkspace project={project} editor={modelEditor} />;
  const generating = isJobGenerating(activeJob);

  const liveModelUrl = isLocalSandbox
    ? null
    : modelFile?.file_url ?? null;
  const editorStats = modelEditor.impact
    ? {
        ...summaryStats,
        totalCost: modelEditor.impact.total_cost_estimate,
        cementBags: modelEditor.impact.quantities.cement_bags,
        steelKg: modelEditor.impact.quantities.steel_kg + modelEditor.impact.quantities.rebar_kg,
        excavationM3: undefined,
        currency: modelEditor.impact.currency,
      }
    : summaryStats;

  return (
    <div className="engineering-workspace flex flex-1 flex-col min-h-0 overflow-hidden pb-0">
      <div className="flex min-h-0 flex-1 flex-col overflow-hidden">
        <WorkspaceLayout
          projectId={projectId}
          defaultFocus={false}
          mapCreditsContainer={mapCreditsContainer}
          toolRail={<WorkspaceToolRail editor={modelEditor} />}
          mapToolbar={
            <div className="workspace-commandbar pointer-events-auto relative flex min-w-0 flex-wrap items-center gap-2">
              {project.project_type === "building" && !isPublicDemo && !isLocalSandbox && <div className="relative">
                <Button className="h-10 gap-2 rounded-xl" onClick={() => setBuildingAssistantOpen(value => !value)}><Sparkles className="size-4" />AI Building Assistant</Button>
                {buildingAssistantOpen && <BuildingAssistant projectId={projectId} boundaryKey={JSON.stringify(project.boundary_geojson ?? null)} revisionId={modelEditor.baseRevision?.id ?? null} dirty={modelEditor.dirty} generating={generating} onStarted={showBuildingJob} onClose={() => setBuildingAssistantOpen(false)} />}
              </div>}
              <div className="flex items-center" title="Scene / Sun study">
                <Button variant="ghost" size="icon" className="size-10 rounded-xl border border-transparent bg-transparent text-muted-foreground shadow-none hover:border-border hover:bg-white/10 hover:text-foreground" aria-label="Scene / Sun study" title="Scene / Sun study" onClick={() => window.dispatchEvent(new CustomEvent("geoai:open-scene-controls"))}><Sun className="size-4" /></Button>
              </div>
              <div className="flex items-center gap-2">
                <Button variant="ghost" size="icon" className="size-10 rounded-xl border border-transparent bg-transparent text-muted-foreground shadow-none hover:border-border hover:bg-white/10 hover:text-foreground" data-workspace-popup="search" aria-label="Search workspace" title="Search places" onClick={() => window.dispatchEvent(new CustomEvent("geoai:open-location-search"))}><Search className="size-4" /></Button>
              </div>
            </div>
          }
          ai={{
            projectId,
            design,
            onApplyParameters: setPendingParams,
            onRegenerate: generate,
            onRunSiteAnalysis: runSiteAnalysis,
            currentParameters:
              pendingParams ??
              (scenario?.input_parameters_json as
                Record<string, unknown> | undefined) ??
              null,
          }}
          rightPanel={<ProfessionalModelPanel editor={modelEditor} projectId={!isPublicDemo && !isLocalSandbox ? projectId : undefined} siteGeometry={project.boundary_geojson ?? project.alignment_geojson ?? (project.center_lng !== null && project.center_lat !== null ? { type: "Point", coordinates: [project.center_lng, project.center_lat] } : null)} />}
          map={
            <>
              <WorkspaceMapEngine
                project={project}
                modelUrl={liveModelUrl}
                excavationUrl={excavationFile?.file_url}
                resolvedModels={resolvedModels}
                onBoundaryDrawn={saveBoundary}
                onAlignmentDrawn={saveAlignment}
                onLocationChange={saveLocation}
                onGenerate={() =>
                  generate(
                    pendingParams ??
                      (scenario?.input_parameters_json as Record<
                        string,
                        unknown
                      >) ??
                      {},
                  )
                }
                onAnalyze={analyzeSite}
                onGenerationCompleted={load}
                onCancelJob={cancelJob}
                cancellingJob={cancelling}
                editor={modelEditor}
                editableModel={modelEditor.document}
                modelRevisionId={modelEditor.baseRevision?.id}
                selectedComponentIds={modelEditor.selectedIds}
                onSelectComponent={(id, additive) => {
                  modelEditor.select(id, additive);
                }}
              />
              {!isPublicDemo && (
                <div className="pointer-events-none absolute left-1/2 top-24 z-20 w-[min(90%,30rem)] -translate-x-1/2">
                  <EmptyProjectStarter
                    projectId={projectId}
                    active
                    hasSite={Boolean(
                      project.boundary_geojson ||
                      project.alignment_geojson ||
                      project.location_name ||
                      project.center_lat !== null ||
                      project.center_lng !== null
                    )}
                  >
                    {null}
                  </EmptyProjectStarter>
                </div>
              )}
            </>
          }
        />
        <BottomSummaryBar
          variant="bar"
          editor={modelEditor}
          project={project}
          stats={editorStats}
          loading={generating}
          onCreditsContainerChange={setMapCreditsContainer}
        />
      </div>
    </div>
  );
}







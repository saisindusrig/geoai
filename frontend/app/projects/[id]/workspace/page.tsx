"use client";

import { useParams, useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import BottomSummaryBar from "@/components/layout/BottomSummaryBar";
import DrawingToolsToolbar from "@/components/layout/DrawingToolsToolbar";
import {
  ProjectError,
  ProjectLoading,
} from "@/components/layout/ProjectHeader";
import WorkspaceLayout from "@/components/layout/WorkspaceLayout";
import WorkspaceMapEngine from "@/components/map/WorkspaceMapEngine";
import { ProfessionalModelPanel } from "@/components/model-editor/ProfessionalModelEditor";
import WorkspaceToolRail from "@/components/workspace/WorkspaceToolRail";
import SandboxWorkspace from "@/components/sandbox/SandboxWorkspace";
import { assetSupportsGeneration } from "@/lib/asset-types";
import ParameterForm from "@/components/workspace/ParameterForm";
import { Button } from "@/components/ui/button";
import { ChevronDown, Crosshair, Layers3, MapPinned, Search, Sparkles, Wrench } from "lucide-react";
import TransformOptions from "@/components/model-editor/TransformOptions";
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
import { useWorkspacePanel } from "@/hooks/useWorkspacePanel";

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
  const [generationMode, setGenerationMode] =
    useState<GenerationMode>("balanced");
  const { open: conceptOpen, toggle: toggleConcept, close: closeConcept } = useWorkspacePanel("generation");
  const { open: toolsOpen, toggle: toggleTools, close: closeTools } = useWorkspacePanel("drawing");
  const [mapCreditsContainer, setMapCreditsContainer] = useState<HTMLDivElement | null>(null);

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
    useProjectStore.getState().setLayers({ projectModel: true, terrain: true, satellite: true });
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
          mapBottomControls={<TransformOptions editor={modelEditor} />}
          mapToolbar={
            <div className="workspace-commandbar pointer-events-auto relative flex min-w-0 flex-wrap items-start gap-1.5">
              <div className="relative">
                <Button variant="ghost" size="icon" className="size-10 rounded-xl border border-transparent bg-transparent text-muted-foreground shadow-none hover:border-white/15 hover:bg-white/10 hover:text-foreground" title="Drawing and site tools" onClick={toggleTools}><Wrench className="size-4" /></Button>
                {toolsOpen && (
                  <section className="absolute left-0 top-12 w-[500px] max-w-[calc(100vw-6rem)] rounded-xl border border-white/10 bg-background-secondary/95 p-2.5 shadow-md backdrop-blur-md" aria-label="Drawing and site tools">
                    <div className="mb-2 flex items-center justify-between gap-3"><p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-primary">Site & drawing tools <span className="ml-2 normal-case font-normal tracking-normal text-muted-foreground">Boundary · alignment · snap · measure</span></p><Button variant="ghost" size="sm" className="h-6 px-1.5 text-[10px]" onClick={closeTools}>Close</Button></div>
                    <DrawingToolsToolbar projectType={project.project_type} boundary={project.boundary_geojson} alignment={project.alignment_geojson} onSaveBoundary={saveBoundary} onSaveAlignment={saveAlignment} onGenerate={assetSupportsGeneration(project.project_type) ? (mode) => generate(pendingParams ?? (scenario?.input_parameters_json as Record<string, unknown>) ?? {}, mode ?? generationMode) : undefined} onAnalyze={analyzeSite} generating={generating} generationMode={generationMode} onGenerationModeChange={setGenerationMode} />
                  </section>
                )}
              </div>
              <div className="flex items-center" title="Project layers">
                <Button variant="ghost" size="icon" className="size-10 rounded-xl border border-transparent bg-transparent text-muted-foreground shadow-none hover:border-white/15 hover:bg-white/10 hover:text-foreground" aria-label="World context layers" onClick={() => window.dispatchEvent(new CustomEvent("geoai:open-scene-controls"))}><Layers3 className="size-4" /></Button>
              </div>
              <div className="flex items-center">
                <Button variant="ghost" size="icon" className="size-10 rounded-xl border border-transparent bg-transparent text-muted-foreground shadow-none hover:border-white/15 hover:bg-white/10 hover:text-foreground" title="Search location" onClick={() => window.dispatchEvent(new CustomEvent("geoai:open-location-search"))}><Search className="size-4" /></Button>
                <Button variant="ghost" size="icon" className="size-10 rounded-xl border border-transparent bg-transparent text-muted-foreground shadow-none hover:border-white/15 hover:bg-white/10 hover:text-foreground" title="Toggle 2D / 3D view" onClick={() => window.dispatchEvent(new CustomEvent("geoai:toggle-map-view"))}><MapPinned className="size-4" /></Button>
                <Button variant="ghost" size="icon" className="size-10 rounded-xl border border-transparent bg-transparent text-muted-foreground shadow-none hover:border-white/15 hover:bg-white/10 hover:text-foreground" title="Fit project in view" onClick={() => window.dispatchEvent(new CustomEvent("geoai:fit-project"))}><Crosshair className="size-4" /></Button>
              </div>
              <div className="relative">
                <Button disabled={!assetSupportsGeneration(project.project_type)} title={assetSupportsGeneration(project.project_type) ? "Generate concept" : "Site reference only; generation unavailable"} onClick={toggleConcept} className="workspace-generate-button h-10 gap-2 rounded-xl bg-primary/90 px-4 text-xs font-semibold shadow-md brightness-[0.94] hover:bg-primary/80">
                  <Sparkles className="size-4" /> Generate · {generationMode === "fast_preview" ? "Fast" : generationMode === "high_detail" ? "Detailed" : "Balanced"} <ChevronDown className="size-3.5" />
                </Button>
                {conceptOpen && (
                  <section className="absolute right-0 top-12 w-[320px] rounded-2xl border border-white/15 bg-background/95 p-4 shadow-2xl backdrop-blur-xl" aria-label="Generate concept">
                    <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-primary">Generate concept</p>
                    <p className="mt-1 text-xs text-muted-foreground">Create a preliminary {project.project_type} model using the current site and engineering parameters.</p>
                    <label className="mt-4 block text-[10px] font-semibold uppercase tracking-[0.12em] text-muted-foreground">Mode
                      <select value={generationMode} onChange={(event) => setGenerationMode(event.target.value as GenerationMode)} className="mt-1.5 h-9 w-full rounded-sm border border-border bg-background px-2 text-xs text-foreground outline-none">
                        <option value="fast_preview">Fast</option><option value="balanced">Balanced</option><option value="high_detail">Detailed</option>
                      </select>
                    </label>
                    <div className="mt-4 border-t border-white/10 pt-3"><p className="mb-2 text-[10px] font-semibold uppercase tracking-[0.12em] text-muted-foreground">Engineering parameters</p><ParameterForm compact projectType={project.project_type} initialValues={pendingParams ?? (scenario?.input_parameters_json as Record<string, unknown> | null)} generating={generating} onGenerate={(parameters) => { closeConcept(); generate(parameters, generationMode); }} /></div>
                    <div className="mt-3 flex justify-end"><Button variant="ghost" size="sm" onClick={closeConcept}>Cancel</Button></div>
                  </section>
                )}
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
          rightPanel={<ProfessionalModelPanel editor={modelEditor} />}
          map={
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
                if (id) {
                  closeTools();
                  closeConcept();
                }
              }}
            />
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

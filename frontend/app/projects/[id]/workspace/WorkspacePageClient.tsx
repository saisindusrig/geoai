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
import GeoJsonImport from "@/components/map/GeoJsonImport";
import { ProfessionalModelPanel } from "@/components/model-editor/ProfessionalModelEditor";
import WorkspaceToolRail from "@/components/workspace/WorkspaceToolRail";
import EmptyProjectStarter from "@/components/workspace/EmptyProjectStarter";
import SandboxWorkspace from "@/components/sandbox/SandboxWorkspace";
import { assetSupportsGeneration } from "@/lib/asset-types";
import { Button } from "@/components/ui/button";
import { Sun, Search, Upload } from "lucide-react";
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

  const { cancelJob, cancelling, pollingError, retryPolling } = useActiveJobPolling({
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
  const activeTool = useProjectStore(state => state.activeTool);
  const drawnBoundary = useProjectStore(state => state.drawnBoundary);
  const drawnAlignment = useProjectStore(state => state.drawnAlignment);
  const pendingSave = useProjectStore(state => state.pendingSave);
  const measuring = useProjectStore(state => state.scene3dMeasureTool !== "none");
  const [inspectorOpen, setInspectorOpen] = useState(false);
  const [importOpen, setImportOpen] = useState(false);
  const [workflowStep, setWorkflowStep] = useState("model");
  const [createMenuOpen, setCreateMenuOpen] = useState(false);
  useEffect(() => {
    let presentation = "model";
    const onPresentation = (event: Event) => {
      presentation = (event as CustomEvent<string>).detail === "site" ? "site" : "model";
      setWorkflowStep(presentation);
    };
    const onInspector = (event: Event) => {
      const tab = (event as CustomEvent<string | null>).detail;
      setWorkflowStep(tab === "properties" ? "edit" : tab === "analysis" ? "analysis" : tab === "layout" ? "review" : presentation);
    };
    window.addEventListener("geoai:presentation", onPresentation);
    window.addEventListener("geoai:presentation-view", onPresentation);
    window.addEventListener("geoai:inspector-view", onInspector);
    return () => { window.removeEventListener("geoai:presentation", onPresentation); window.removeEventListener("geoai:presentation-view", onPresentation); window.removeEventListener("geoai:inspector-view", onInspector); };
  }, []);
  const workflowClass = "rounded-md border border-transparent px-2 py-2 transition-colors hover:bg-white/10 focus-visible:outline-2 focus-visible:outline-primary aria-[current=step]:border-primary/30 aria-[current=step]:bg-primary/15 aria-[current=step]:font-semibold aria-[current=step]:text-primary";


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
  const visualOnly = Boolean(modelEditor.document?.components.length && modelEditor.document.components.every(component => component.quantity?.included === false));
  const editorStats = visualOnly
    ? { ...summaryStats, totalCost: undefined, cementBags: undefined, steelKg: undefined, excavationM3: undefined, timelineMonths: undefined, riskScore: undefined }
    : modelEditor.impact
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
          toolbar={<>
            {pollingError && <div role="alert" className="flex w-full items-center gap-3 border-l-2 border-warning px-3 py-2 text-warning-text"><span>Job status disconnected. {pollingError} The job may still be running.</span><button type="button" onClick={retryPolling} className="min-h-11 shrink-0 underline underline-offset-4">Retry job status</button></div>}
          <div className="flex min-w-0 items-center gap-2 text-xs" aria-label="Design workflow">
            <button aria-current={workflowStep === "site" && !importOpen && !createMenuOpen ? "step" : undefined} className={workflowClass} onClick={() => window.dispatchEvent(new CustomEvent("geoai:presentation", { detail: "site" }))}>1 Site</button>
            <details className="relative"><summary className="cursor-pointer list-none rounded px-2 py-2 hover:bg-white/10">Workflow help</summary><div className="absolute left-0 top-full z-50 w-72 space-y-2 rounded border border-border bg-background p-3 text-xs"><p>Open Create / Import to review a source drawing. Review 3D, then click a member to inspect its dimensions.</p><p>Edit fields → Preview → Apply → Save model. Undo and Redo reverse applied edits before saving.</p><p>Analyze / Results opens existing engineering tasks and evidence. Solver verification applies only to the stated numerical model; unsupported checks stay unverified.</p><p>Save site geometry stores boundary and alignment. Save model stores 3D component revisions.</p></div></details><details className="group relative" onToggle={event => setCreateMenuOpen(event.currentTarget.open)}><summary aria-current={importOpen || createMenuOpen ? "step" : undefined} className={`${workflowClass} cursor-pointer list-none group-open:border-primary/30 group-open:bg-primary/15 group-open:text-primary`}>2 Create / Import</summary><div onClick={event=>event.currentTarget.closest("details")?.removeAttribute("open")} className="absolute left-0 top-full z-50 w-52 rounded-lg border border-border bg-background p-2"><button className="block w-full rounded p-2 text-left hover:bg-white/10" onClick={() => window.dispatchEvent(new Event("geoai:open-site-assistant"))}>Ask Assistant</button><button className="block w-full rounded p-2 text-left hover:bg-white/10" onClick={() => { window.dispatchEvent(new CustomEvent("geoai:presentation", { detail: "site" })); setImportOpen(true); }}>Import site geometry</button><button className="block w-full rounded p-2 text-left hover:bg-white/10" onClick={() => window.dispatchEvent(new Event("geoai:show-analysis"))}>Review CAD drawing</button></div></details>
            <button aria-current={workflowStep === "model" && !importOpen && !createMenuOpen ? "step" : undefined} className={workflowClass} onClick={() => window.dispatchEvent(new CustomEvent("geoai:presentation", { detail: "model" }))}>3 Review 3D</button>
            <button aria-current={workflowStep === "edit" && !importOpen && !createMenuOpen ? "step" : undefined} className={workflowClass} onClick={() => window.dispatchEvent(new Event("geoai:inspect-component"))}>4 Edit</button>
            <button aria-current={workflowStep === "analysis" && !importOpen && !createMenuOpen ? "step" : undefined} className={workflowClass} onClick={() => window.dispatchEvent(new Event("geoai:show-analysis"))}>5 Analyze / Results</button>
            <button aria-current={workflowStep === "review" && !importOpen && !createMenuOpen ? "step" : undefined} className={workflowClass} onClick={() => window.dispatchEvent(new Event("geoai:show-review"))}>6 Review</button>
            <span role="status" className="ml-auto whitespace-nowrap text-[11px] text-muted-foreground">{modelEditor.dirty ? "Draft · unsaved edits" : modelEditor.baseRevision ? `Saved · v${modelEditor.baseRevision.revision_number}` : "Needs Inputs"}</span>
            <Button title="Saves 3D components as a model revision. Site geometry is saved separately using Save Site." size="sm" disabled={!modelEditor.dirty || modelEditor.saving || !modelEditor.canPersist || !!modelEditor.platformPreview} onClick={() => void toastPromise(modelEditor.save(), { loading: "Saving model revision…", success: "Model revision saved", error: "Model save failed; draft retained" }).catch(() => undefined)}>{modelEditor.saving ? "Saving…" : "Save model"}</Button>
          </div></>}
          mapCreditsContainer={mapCreditsContainer}
          toolRail={<WorkspaceToolRail editor={modelEditor} />}
          mapToolbar={
            <div className="workspace-commandbar pointer-events-auto relative flex min-w-0 flex-wrap items-center gap-2">
              <div className="flex items-center" title="Scene / Sun study">
                <Button variant="ghost" size="icon" className="size-10 rounded-xl border border-transparent bg-transparent text-muted-foreground shadow-none hover:border-border hover:bg-white/10 hover:text-foreground" aria-label="Scene / Sun study" title="Scene / Sun study" onClick={() => window.dispatchEvent(new CustomEvent("geoai:open-scene-controls"))}><Sun className="size-4" /></Button>
              </div>
              <div className="flex items-center gap-2">
                <Button variant="ghost" size="icon" className="size-10 rounded-xl border border-transparent bg-transparent text-muted-foreground shadow-none hover:border-border hover:bg-white/10 hover:text-foreground" data-workspace-popup="search" aria-label="Search workspace" title="Search places" onClick={() => window.dispatchEvent(new CustomEvent("geoai:open-location-search"))}><Search className="size-4" /></Button>
              </div>
              {!isPublicDemo && <details open={importOpen} onToggle={event => setImportOpen(event.currentTarget.open)} className="relative" data-workspace-popup="import">
                <summary aria-label="Import site geometry" title="Import site geometry" className="flex h-9 cursor-pointer list-none items-center gap-2 rounded-lg bg-background/90 px-3 text-xs text-muted-foreground"><Upload className="size-4" />Import</summary>
                <div className="absolute left-0 top-full mt-2 w-56 rounded-lg border border-border bg-background p-2 shadow-lg">
                  <GeoJsonImport onImportBoundary={saveBoundary} onImportAlignment={saveAlignment} />
                  <p className="px-2 py-1 text-[10px] leading-relaxed text-muted-foreground">WGS84 coordinates · imports replace the current boundary or alignment.</p>
                </div>
              </details>}
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
          compactInspector={!isPublicDemo}
          inspectorOpen={inspectorOpen}
          rightPanel={<ProfessionalModelPanel onInspectorOpenChange={setInspectorOpen} separateAssistant={!isPublicDemo} showStarter={false} editor={modelEditor} projectId={!isPublicDemo && !isLocalSandbox ? projectId : undefined} siteGeometry={project.boundary_geojson ?? project.alignment_geojson ?? (project.center_lng !== null && project.center_lat !== null ? { type: "Point", coordinates: [project.center_lng, project.center_lat] } : null)} />}
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
                    active={activeTool === "select" && !measuring && !modelEditor.loading && !modelEditor.document}
                    hasSite={Boolean(
                      project.boundary_geojson ||
                      drawnBoundary || drawnAlignment || pendingSave ||
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







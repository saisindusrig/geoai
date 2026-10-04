import { describe, expect, it } from "vitest";
import {
  hasCompletedGlbModel,
  isJobGenerating,
  jobFinalGlbUrl,
  resolveModelUrls,
} from "@/lib/model-url-resolution";
import { modelLayerEnableState, scene3dLayersForProjectType } from "@/lib/model-viewer-state";
import { resolveWorkspaceMapEngine } from "@/lib/map/workspace-engine";
import type { GeneratedFileInfo, JobStatus, ScenarioSummary } from "@/lib/types";

const summary = (id: number, modelUrl: string | null): ScenarioSummary => ({
  scenario_id: id,
  name: `Scenario ${id}`,
  status: "completed",
  created_at: "2026-06-14T10:00:00Z",
  model_url: modelUrl,
});

const file = (scenarioId: number, url: string, type = "glb"): GeneratedFileInfo => ({
  id: scenarioId,
  file_type: type,
  file_url: url,
  scenario_id: scenarioId,
  created_at: "2026-06-14T10:00:00Z",
});

describe("resolveModelUrls", () => {
  it("prefers completed job final GLB over saved scenario files", () => {
    const job: JobStatus = {
      job_id: "j1",
      status: "completed",
      stage: "completed",
      preview_glb_url: "http://localhost:8000/files/preview.glb",
      result: { glb_url: "http://localhost:8000/files/final.glb" },
      error: null,
    };
    const resolved = resolveModelUrls({
      activeJob: job,
      projectFiles: [file(4, "http://localhost:8000/files/saved.glb")],
      scenarioId: 4,
    });
    expect(resolved.modelUrl).toBe("http://localhost:8000/files/final.glb");
    expect(resolved.modelSource).toBe("job_final");
  });

  it("does not let stale running job block saved scenario model", () => {
    const job: JobStatus = {
      job_id: "j2",
      status: "running",
      stage: "generating_layout",
      preview_ready: false,
      preview_glb_url: null,
      result: null,
      error: null,
    };
    const resolved = resolveModelUrls({
      activeJob: job,
      generating: true,
      activeSummary: summary(4, "http://localhost:8000/files/scenario_4/model.glb"),
      scenarioId: 4,
    });
    expect(resolved.modelUrl).toBe("http://localhost:8000/files/scenario_4/model.glb");
    expect(resolved.modelSource).toBe("scenario_summary");
  });

  it("uses live preview only while generating with preview_ready", () => {
    const job: JobStatus = {
      job_id: "j3",
      status: "running",
      stage: "generating_3d_preview",
      preview_ready: true,
      preview_glb_url: "http://localhost:8000/files/preview-live.glb",
      result: null,
      error: null,
    };
    const resolved = resolveModelUrls({
      activeJob: job,
      generating: true,
      activeSummary: summary(4, "http://localhost:8000/files/scenario_4/model.glb"),
    });
    expect(resolved.modelUrl).toBe("http://localhost:8000/files/preview-live.glb");
    expect(resolved.modelSource).toBe("job_preview");
  });

  it("falls back to scenario detail generated files", () => {
    const resolved = resolveModelUrls({
      scenarioDetailFiles: [file(5, "http://localhost:8000/files/detail.glb")],
      scenarioId: 5,
    });
    expect(resolved.modelUrl).toBe("http://localhost:8000/files/detail.glb");
    expect(resolved.modelSource).toBe("scenario_detail_files");
  });

  it("falls back to latest summary when nothing else is available", () => {
    const resolved = resolveModelUrls({
      scenarioSummaries: [
        summary(8, "http://localhost:8000/files/latest.glb"),
        summary(4, null),
      ],
    });
    expect(resolved.modelUrl).toBe("http://localhost:8000/files/latest.glb");
    expect(resolved.modelSource).toBe("latest_summary");
  });

  it("returns null when no model exists", () => {
    const resolved = resolveModelUrls({ scenarioSummaries: [summary(1, null)] });
    expect(resolved.modelUrl).toBeNull();
    expect(resolved.modelSource).toBeNull();
  });
});

describe("isJobGenerating", () => {
  it("treats completed jobs as not generating", () => {
    expect(
      isJobGenerating({
        job_id: "x",
        status: "completed",
        stage: "completed",
        result: null,
        error: null,
      }),
    ).toBe(false);
  });

  it("treats running jobs as generating", () => {
    expect(
      isJobGenerating({
        job_id: "x",
        status: "running",
        stage: "calculating_boq",
        result: null,
        error: null,
      }),
    ).toBe(true);
  });
});

describe("jobFinalGlbUrl", () => {
  it("reads glb_url from completed job result", () => {
    expect(
      jobFinalGlbUrl({
        job_id: "x",
        status: "completed",
        result: { glb_url: "http://localhost:8000/files/final.glb" },
        error: null,
      }),
    ).toBe("http://localhost:8000/files/final.glb");
  });
});

describe("modelLayerEnableState", () => {
  it("enables project model layers when a model URL exists", () => {
    const state = modelLayerEnableState("flyover", true);
    expect(state.projectModelEnabled).toBe(true);
    expect(state.layers.projectModel).toBe(true);
    expect(state.scene3dLayers.flyover).toBe(true);
  });

  it("does not enable layers without a model URL", () => {
    const state = modelLayerEnableState("flyover", false);
    expect(state.projectModelEnabled).toBe(false);
    expect(state.layers.projectModel).toBeUndefined();
  });

  it("enables road layers for road projects", () => {
    expect(scene3dLayersForProjectType("road").roads).toBe(true);
  });
});

describe("resolveWorkspaceMapEngine", () => {
  it("uses Cesium when a completed GLB exists", () => {
    expect(resolveWorkspaceMapEngine(true, "maplibre")).toBe("cesium");
  });

  it("uses MapLibre when no GLB and engine not forced", () => {
    expect(resolveWorkspaceMapEngine(false, "maplibre")).toBe("maplibre");
  });

  it("forces Cesium when NEXT_PUBLIC_MAP_ENGINE=cesium", () => {
    expect(resolveWorkspaceMapEngine(false, "cesium")).toBe("cesium");
  });
});

describe("hasCompletedGlbModel", () => {
  it("treats preview-only URLs as not completed", () => {
    expect(
      hasCompletedGlbModel({
        modelUrl: "http://localhost:8000/files/preview.glb",
        modelSource: "job_preview",
        excavationUrl: null,
        excavationSource: null,
      }),
    ).toBe(false);
  });
});

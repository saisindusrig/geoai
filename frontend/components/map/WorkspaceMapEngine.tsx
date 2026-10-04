"use client";
import type { EditableModelEditor } from "@/hooks/useEditableModelEditor";

import dynamic from "next/dynamic";
import type { EditableModelDocument, GeoJSONGeometry, Project } from "@/lib/types";
import { hasCompletedGlbModel, type ResolvedModelUrls } from "@/lib/model-url-resolution";
import { shouldUseCesiumWorkspace } from "@/lib/map/workspace-engine";
import { getMapEngine } from "@/lib/map/providers";

const MapViewerWorkspace = dynamic(() => import("@/components/map/MapViewerArea"), {
  ssr: false,
});

const LiveGenerationPreview = dynamic(
  () => import("@/components/workspace/LiveGenerationPreview"),
  { ssr: false },
);

interface WorkspaceMapEngineProps {
  project: Project;
  modelUrl?: string | null;
  excavationUrl?: string | null;
  resolvedModels?: ResolvedModelUrls | null;
  onBoundaryDrawn?: (g: GeoJSONGeometry) => void;
  onAlignmentDrawn?: (g: GeoJSONGeometry) => void;
  onLocationChange?: (lng: number, lat: number, name: string) => void | Promise<void>;
  onGenerate?: () => void;
  onAnalyze?: () => void;
  onGenerationCompleted?: () => void;
  onCancelJob?: () => void;
  cancellingJob?: boolean;
  editor?: EditableModelEditor;
  editableModel?: EditableModelDocument | null;
  modelRevisionId?: number;
  selectedComponentIds?: string[];
  onSelectComponent?: (id: string | null, additive?: boolean) => void;
}

export default function WorkspaceMapEngine(props: WorkspaceMapEngineProps) {
  const configuredEngine = getMapEngine();
  const hasCompletedGlb =
    Boolean(props.modelUrl || props.excavationUrl) ||
    (props.resolvedModels != null && hasCompletedGlbModel(props.resolvedModels));
  const useCesium = shouldUseCesiumWorkspace(hasCompletedGlb, configuredEngine);

  if (useCesium) {
    return (
      <div className="absolute inset-0">
        <MapViewerWorkspace
          {...props}
          showToolbar={false}
          showSuggestionsPanel={false}
          defaultView="3d"
        />
        {configuredEngine !== "cesium" && (
          <LiveGenerationPreview
            map={null}
            project={props.project}
            onCancel={props.onCancelJob}
            cancelling={props.cancellingJob}
          />
        )}
      </div>
    );
  }

  return (
    <div className="absolute inset-0">
      <MapViewerWorkspace
        {...props}
        showToolbar={false}
        showSuggestionsPanel
        defaultView="3d"
      />
      <LiveGenerationPreview
        map={null}
        project={props.project}
        onCancel={props.onCancelJob}
        cancelling={props.cancellingJob}
      />
    </div>
  );
}

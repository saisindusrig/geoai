"use client";

import {
  Copy,
  Download,
  Magnet,
  MousePointer2,
  Pencil,
  Pipette,
  RectangleHorizontal,
  Route,
  Ruler,
  Sparkles,
  SquareDashed,
  Trash2,
  Undo2,
  Waypoints,
} from "lucide-react";
import GeoJsonImport from "@/components/map/GeoJsonImport";
import SurveyModePanel from "@/components/survey/SurveyModePanel";
import { Button } from "@/components/ui/button";
import { CollapsibleSection, SidebarSection } from "@/components/ui/collapsible-section";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import { downloadGeoJson, verticesToLine, verticesToPolygon } from "@/lib/map-draw";
import { type MapTool, useProjectStore } from "@/stores/projectStore";
import type { GeoJSONGeometry } from "@/lib/types";
import { toast } from "@/lib/toast";

function ToolButton({
  label,
  icon: Icon,
  active,
  onClick,
  compact,
  iconOnly,
  hint,
}: {
  id: MapTool;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  active: boolean;
  onClick: () => void;
  compact?: boolean;
  iconOnly?: boolean;
  hint?: string;
}) {
  const tooltip = hint ?? label;

  if (iconOnly) {
    const buttonClass = cn(
      "h-8 w-8 flex items-center justify-center rounded-md border transition-colors shrink-0",
      active
        ? "bg-primary text-primary-foreground border-primary/50"
        : "bg-card text-foreground border-border hover:bg-muted",
    );

    return active ? (
      <button
        type="button"
        title={tooltip}
        aria-label={label}
        aria-pressed="true"
        onClick={onClick}
        className={buttonClass}
      >
        <Icon className="h-4 w-4 shrink-0" />
      </button>
    ) : (
      <button
        type="button"
        title={tooltip}
        aria-label={label}
        aria-pressed="false"
        onClick={onClick}
        className={buttonClass}
      >
        <Icon className="h-4 w-4 shrink-0" />
      </button>
    );
  }

  return (
    <Button
      variant={active ? "default" : "ghost"}
      size="sm"
      title={tooltip}
      className="justify-start gap-2 h-8 text-[12px] w-full"
      onClick={onClick}
    >
      <Icon className="h-3.5 w-3.5 shrink-0" />
      {!compact && label}
    </Button>
  );
}

function IconActionButton({
  label,
  hint,
  icon: Icon,
  active,
  onClick,
  disabled,
}: {
  label: string;
  hint?: string;
  icon: React.ComponentType<{ className?: string }>;
  active?: boolean;
  onClick?: () => void;
  disabled?: boolean;
}) {
  return (
    <button
      type="button"
      title={hint ?? label}
      aria-label={label}
      disabled={disabled}
      onClick={onClick}
      className={cn(
        "h-8 w-8 flex items-center justify-center rounded-md border transition-colors shrink-0 disabled:opacity-40",
        active
          ? "bg-primary text-primary-foreground border-primary/50"
          : "bg-card text-foreground border-border hover:bg-muted disabled:hover:bg-card",
      )}
    >
      <Icon className="h-4 w-4 shrink-0" />
    </button>
  );
}

function ToolGrid({ iconOnly, children }: { iconOnly?: boolean; children: React.ReactNode }) {
  if (!iconOnly) return <>{children}</>;
  return <div className="grid grid-cols-4 gap-1">{children}</div>;
}

function ToolFullWidth({ iconOnly, children }: { iconOnly?: boolean; children: React.ReactNode }) {
  if (!iconOnly) return <>{children}</>;
  return <div className="col-span-4">{children}</div>;
}

function PanelSection({
  title,
  defaultOpen = true,
  iconOnly,
  children,
}: {
  title: string;
  defaultOpen?: boolean;
  iconOnly?: boolean;
  children: React.ReactNode;
}) {
  return iconOnly ? (
    <SidebarSection title={title}>{children}</SidebarSection>
  ) : (
    <CollapsibleSection title={title} defaultOpen={defaultOpen}>
      {children}
    </CollapsibleSection>
  );
}

export default function DrawingToolsPanel({
  compact,
  iconOnly,
  hidePrimaryTools,
  projectId,
  projectType = "flyover",
  boundary,
  alignment,
  onImportBoundary,
  onImportAlignment,
  onSaveBoundary,
  onSaveAlignment,
  onDeleteBoundary,
  onDeleteAlignment,
  onAnalyzeTerrain,
}: {
  compact?: boolean;
  iconOnly?: boolean;
  /** When true, Select/Define Site/Measure render in the header toolbar instead. */
  hidePrimaryTools?: boolean;
  projectId?: number;
  projectType?: string;
  boundary?: GeoJSONGeometry | null;
  alignment?: GeoJSONGeometry | null;
  onImportBoundary?: (g: GeoJSONGeometry) => void | Promise<void>;
  onImportAlignment?: (g: GeoJSONGeometry) => void | Promise<void>;
  onSaveBoundary?: (g: GeoJSONGeometry) => void | Promise<void>;
  onSaveAlignment?: (g: GeoJSONGeometry) => void | Promise<void>;
  onDeleteBoundary?: () => void | Promise<void>;
  onDeleteAlignment?: () => void | Promise<void>;
  onAnalyzeTerrain?: () => void;
}) {
  const {
    activeTool,
    activateTool,
    popDrawVertex,
    clearDrawVertices,
    drawVertices,
    snapEnabled,
    toggleSnap,
    corridorWidthM,
    setCorridorWidthM,
    editVertices,
    revertEditVertices,
    pendingSave,
    setPendingSave,
    measureHistory,
    clearMeasureHistory,
    setSurveyModeEnabled,
    setSurveyAccuracyTier,
    setEngineeringLayerFeatures,
    setSurveyGcpFeatures,
  } = useProjectStore();

  const select = (tool: MapTool, hint?: "flyover" | "pipeline" | "building" | "terrain") => {
    activateTool(tool, hint ?? null);
  };

  const saveEdit = async () => {
    if (activeTool === "edit-boundary" && editVertices.length >= 3) {
      await onSaveBoundary?.(verticesToPolygon(editVertices));
      activateTool("select");
    } else if (activeTool === "edit-alignment" && editVertices.length >= 2) {
      await onSaveAlignment?.(verticesToLine(editVertices));
      activateTool("select");
    }
  };

  const confirmPending = async () => {
    if (!pendingSave) return;
    if (pendingSave.kind === "boundary") await onSaveBoundary?.(pendingSave.geometry);
    else await onSaveAlignment?.(pendingSave.geometry);
    setPendingSave(null);
    activateTool("select");
  };

  const copyMeasure = (value: string) => {
    void navigator.clipboard.writeText(value);
    toast("Copied", { variant: "success" });
  };

  return (
    <div className={cn("space-y-3", (compact || iconOnly) && "space-y-2")}>
      {!hidePrimaryTools && (
        <>
      <PanelSection title="Select & Suggest" iconOnly={iconOnly}>
        <ToolGrid iconOnly={iconOnly}>
          <ToolButton
            id="select"
            label="Select"
            icon={MousePointer2}
            active={activeTool === "select"}
            onClick={() => select("select")}
            compact={compact}
            iconOnly={iconOnly}
            hint="Select and pan · click building for boundary"
          />
          <ToolButton
            id="suggest-site"
            label="Smart Suggest"
            icon={Sparkles}
            active={activeTool === "suggest-site"}
            onClick={() => select("suggest-site")}
            compact={compact}
            iconOnly={iconOnly}
            hint="AI site suggestions along alignment"
          />
          {iconOnly ? (
            <IconActionButton
              label="Snap"
              hint={`Snap to vertices: ${snapEnabled ? "on" : "off"}`}
              icon={Magnet}
              active={snapEnabled}
              onClick={toggleSnap}
            />
          ) : (
            <Button
              variant={snapEnabled ? "default" : "ghost"}
              size="sm"
              className="justify-start gap-2 h-8 text-[12px] w-full"
              title={`Snap to vertices: ${snapEnabled ? "on" : "off"}`}
              onClick={toggleSnap}
            >
              <Magnet className="h-3.5 w-3.5 shrink-0" />
              {!compact && `Snap ${snapEnabled ? "on" : "off"}`}
            </Button>
          )}
        </ToolGrid>
      </PanelSection>

      <PanelSection title="Define Site" iconOnly={iconOnly}>
        <ToolGrid iconOnly={iconOnly}>
          <ToolButton
            id="draw-rectangle"
            label="Rectangle site"
            icon={RectangleHorizontal}
            active={activeTool === "draw-rectangle"}
            onClick={() => select("draw-rectangle", projectType === "building" ? "building" : undefined)}
            compact={compact}
            iconOnly={iconOnly}
            hint="Rectangle site · two opposite corners"
          />
          <ToolButton
            id="draw-polygon"
            label="Draw boundary"
            icon={SquareDashed}
            active={activeTool === "draw-polygon"}
            onClick={() => select("draw-polygon")}
            compact={compact}
            iconOnly={iconOnly}
            hint="Draw boundary polygon · Enter or double-click to finish"
          />
          <ToolButton
            id="draw-corridor"
            label="Corridor / alignment"
            icon={Route}
            active={activeTool === "draw-corridor"}
            onClick={() => select("draw-corridor")}
            compact={compact}
            iconOnly={iconOnly}
            hint="Draw corridor / alignment with width"
          />
          <ToolButton
            id="draw-line"
            label="Road / line"
            icon={Waypoints}
            active={activeTool === "draw-line"}
            onClick={() => select("draw-line")}
            compact={compact}
            iconOnly={iconOnly}
            hint="Draw road centerline or polyline"
          />
          <ToolButton
            id="edit-boundary"
            label="Edit boundary"
            icon={Pencil}
            active={activeTool === "edit-boundary"}
            onClick={() => select("edit-boundary")}
            compact={compact}
            iconOnly={iconOnly}
            hint={boundary ? "Edit boundary · drag handles" : "Draw a boundary first"}
          />
          <ToolButton
            id="edit-alignment"
            label="Edit alignment"
            icon={Waypoints}
            active={activeTool === "edit-alignment"}
            onClick={() => select("edit-alignment")}
            compact={compact}
            iconOnly={iconOnly}
            hint={alignment ? "Edit alignment · drag handles" : "Draw alignment first"}
          />
          {iconOnly && (
            <>
              <IconActionButton
                label="Undo vertex"
                hint="Undo last drawn vertex"
                icon={Undo2}
                disabled={drawVertices.length === 0}
                onClick={() => popDrawVertex()}
              />
              <IconActionButton
                label="Clear draw"
                hint="Clear drawing and return to select"
                icon={Trash2}
                onClick={() => {
                  clearDrawVertices();
                  setPendingSave(null);
                  activateTool("select");
                }}
              />
            </>
          )}
        </ToolGrid>
        {activeTool === "draw-corridor" && (
          <ToolFullWidth iconOnly={iconOnly}>
            <div className="flex items-center gap-2 px-1 py-1 mt-1">
              <span className="text-[10px] text-muted-foreground shrink-0">Width (m)</span>
              <Input
                type="number"
                min={5}
                max={200}
                value={corridorWidthM}
                onChange={(e) => setCorridorWidthM(Number(e.target.value) || 30)}
                className="h-7 text-xs"
              />
            </div>
          </ToolFullWidth>
        )}
        {(activeTool === "edit-boundary" || activeTool === "edit-alignment") && (
          <ToolFullWidth iconOnly={iconOnly}>
            <div className="flex flex-col gap-1 mt-1">
              <Button size="sm" className="h-7 text-xs" onClick={saveEdit}>
                Save edits
              </Button>
              <Button size="sm" variant="ghost" className="h-7 text-xs" onClick={revertEditVertices}>
                Revert
              </Button>
            </div>
          </ToolFullWidth>
        )}
        {!iconOnly && (
          <>
            {(onImportBoundary || onImportAlignment) && (
              <GeoJsonImport
                onImportBoundary={onImportBoundary}
                onImportAlignment={onImportAlignment}
                boundary={boundary}
                alignment={alignment}
              />
            )}
            {(boundary || alignment) && (
              <div className="flex flex-col gap-1">
                {boundary && (
                  <Button
                    variant="ghost"
                    size="sm"
                    className="justify-start gap-2 h-7 text-[11px] w-full"
                    onClick={() => downloadGeoJson("boundary.geojson", boundary)}
                  >
                    <Download className="h-3.5 w-3.5" />
                    Export boundary
                  </Button>
                )}
                {alignment && (
                  <Button
                    variant="ghost"
                    size="sm"
                    className="justify-start gap-2 h-7 text-[11px] w-full"
                    onClick={() => downloadGeoJson("alignment.geojson", alignment)}
                  >
                    <Download className="h-3.5 w-3.5" />
                    Export alignment
                  </Button>
                )}
              </div>
            )}
            {boundary && onDeleteBoundary && (
              <Button
                variant="ghost"
                size="sm"
                className="justify-start gap-2 h-7 text-[11px] w-full text-destructive hover:text-destructive"
                onClick={() => {
                  if (window.confirm("Delete saved boundary?")) void onDeleteBoundary();
                }}
              >
                <Trash2 className="h-3.5 w-3.5" />
                Delete boundary
              </Button>
            )}
            {alignment && onDeleteAlignment && (
              <Button
                variant="ghost"
                size="sm"
                className="justify-start gap-2 h-7 text-[11px] w-full text-destructive hover:text-destructive"
                onClick={() => {
                  if (window.confirm("Delete saved alignment?")) void onDeleteAlignment();
                }}
              >
                <Trash2 className="h-3.5 w-3.5" />
                Delete alignment
              </Button>
            )}
            <Button
              variant="ghost"
              size="sm"
              className="justify-start gap-2 h-8 text-[12px] w-full"
              disabled={drawVertices.length === 0}
              onClick={() => popDrawVertex()}
            >
              <Undo2 className="h-3.5 w-3.5 shrink-0" />
              Undo vertex
            </Button>
            <Button
              variant="ghost"
              size="sm"
              className="justify-start gap-2 h-7 text-[11px] w-full text-muted-foreground"
              onClick={() => {
                clearDrawVertices();
                setPendingSave(null);
                activateTool("select");
              }}
            >
              Clear draw
            </Button>
          </>
        )}
        {pendingSave && (
          <div className="border border-primary/30 bg-primary/5 p-2 space-y-1 mt-1">
            <p className="text-[10px] text-muted-foreground">Ready to save</p>
            <Button size="sm" className="h-7 text-xs w-full" onClick={confirmPending}>
              Confirm save
            </Button>
          </div>
        )}
      </PanelSection>

      <PanelSection title="Measure" defaultOpen={false} iconOnly={iconOnly}>
        <ToolGrid iconOnly={iconOnly}>
          <ToolButton
            id="measure-distance"
            label="Measure distance"
            icon={Ruler}
            active={activeTool === "measure-distance"}
            onClick={() => select("measure-distance")}
            compact={compact}
            iconOnly={iconOnly}
            hint="Measure distance between points"
          />
          <ToolButton
            id="measure-area"
            label="Measure area"
            icon={SquareDashed}
            active={activeTool === "measure-area"}
            onClick={() => select("measure-area")}
            compact={compact}
            iconOnly={iconOnly}
            hint="Measure polygon area"
          />
        </ToolGrid>
        {measureHistory.length > 0 && (
          <div className="space-y-1 pt-1">
            <p className="text-[10px] text-muted-foreground px-1">Recent</p>
            {measureHistory.map((m) => (
              <div key={m.id} className="flex items-center gap-1 px-1">
                <span className="text-[10px] flex-1 truncate">
                  {m.kind === "distance" ? "↔" : "▦"} {m.value}
                </span>
                <button
                  type="button"
                  className="p-1 hover:bg-muted"
                  onClick={() => copyMeasure(m.value)}
                  title="Copy"
                >
                  <Copy className="h-3 w-3" />
                </button>
              </div>
            ))}
            <Button
              variant="ghost"
              size="sm"
              className="h-6 text-[10px] w-full"
              onClick={clearMeasureHistory}
            >
              Clear history
            </Button>
          </div>
        )}
      </PanelSection>
        </>
      )}

      {!compact && !iconOnly && (
        <CollapsibleSection title="Infrastructure" defaultOpen={false}>
          <Button
            variant="ghost"
            size="sm"
            className="justify-start gap-2 h-8 text-[12px] w-full"
            onClick={() => select("draw-corridor", "flyover")}
          >
            <Waypoints className="h-3.5 w-3.5 shrink-0" />
            Flyover path
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="justify-start gap-2 h-8 text-[12px] w-full"
            onClick={() => select("draw-corridor", "pipeline")}
          >
            <Pipette className="h-3.5 w-3.5 shrink-0" />
            Pipeline ROW
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="justify-start gap-2 h-8 text-[12px] w-full"
            onClick={() => select("draw-rectangle", "building")}
          >
            <RectangleHorizontal className="h-3.5 w-3.5 shrink-0" />
            Building zone
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="justify-start gap-2 h-8 text-[12px] w-full"
            onClick={onAnalyzeTerrain}
          >
            <Sparkles className="h-3.5 w-3.5 shrink-0" />
            Terrain study
          </Button>
        </CollapsibleSection>
      )}

      {projectId != null && (
          <SurveyModePanel
            projectId={projectId}
            onStatusChange={(st) => {
              setSurveyModeEnabled(st.survey_mode_enabled);
              setSurveyAccuracyTier(st.accuracy_tier);
            }}
            onDataLoaded={(layers, gcps) => {
              setEngineeringLayerFeatures(
                layers
                  .filter((l) => l.geom_wgs84_geojson)
                  .map((l) => ({
                    type: "Feature" as const,
                    geometry: l.geom_wgs84_geojson!,
                    properties: {
                      name: l.name,
                      layer_type: l.layer_type,
                      width_m: l.width_m,
                      tier: l.metadata.tier,
                    },
                  })),
              );
              setSurveyGcpFeatures(
                gcps.map((g) => ({
                  type: "Feature" as const,
                  geometry: { type: "Point", coordinates: [g.lng, g.lat] },
                  properties: { name: g.name, source: g.source },
                })),
              );
            }}
          />
      )}
    </div>
  );
}

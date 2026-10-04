"use client";

import {
  MousePointer2,
  RectangleHorizontal,
  Route,
  Sparkles,
  SquareDashed,
  Trash2,
  Undo2,
  Waypoints,
} from "lucide-react";
import SiteSuggestionsPanel from "@/components/map/SiteSuggestionsPanel";
import EmptyState from "@/components/ui/empty-state";
import { GlassCard } from "@/components/ui/glass-card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { lineLengthM, polygonAreaSqm } from "@/lib/geo";
import { toolInstruction } from "@/lib/map-draw";
import type { GeoJSONGeometry, ProjectType } from "@/lib/types";
import { cn } from "@/lib/utils";
import { type MapTool, useProjectStore } from "@/stores/projectStore";
import { toast } from "@/lib/toast";

function ToolIcon({
  label,
  icon: Icon,
  active,
  onClick,
  hint,
}: {
  label: string;
  icon: React.ComponentType<{ className?: string; strokeWidth?: number }>;
  active: boolean;
  onClick: () => void;
  hint?: string;
}) {
  return (
    <button
      type="button"
      title={hint ?? label}
      aria-label={label}
      aria-pressed={active}
      onClick={onClick}
      className={cn(
        "flex h-9 w-9 items-center justify-center rounded-lg border transition-all duration-200",
        active
          ? "border-primary bg-primary/15 text-primary shadow-[var(--shadow-glow-primary)]"
          : "border-border bg-background-secondary text-foreground-secondary hover:border-[rgba(56,189,248,0.35)] hover:bg-primary/10",
      )}
    >
      <Icon className="h-4 w-4 shrink-0" strokeWidth={1.75} />
    </button>
  );
}

function geometryStats(boundary: GeoJSONGeometry | null, alignment: GeoJSONGeometry | null) {
  let areaSqm: number | null = null;
  let lengthM: number | null = null;
  let points = 0;

  if (boundary?.type === "Polygon") {
    const ring = (boundary.coordinates as [number, number][][])[0];
    areaSqm = polygonAreaSqm(ring.slice(0, -1));
    points = ring.length - 1;
  }
  if (alignment?.type === "LineString") {
    const coords = alignment.coordinates as [number, number][];
    lengthM = lineLengthM(coords);
    points += coords.length;
  }

  return { areaSqm, lengthM, points };
}

export default function NewProjectBoundaryPanel({
  projectType,
  centerLng,
  centerLat,
  boundary,
  alignment,
  onApplyBoundary,
  onApplyAlignment,
  onClearBoundary,
  onClearAlignment,
}: {
  projectType: ProjectType;
  centerLng: number;
  centerLat: number;
  boundary: GeoJSONGeometry | null;
  alignment: GeoJSONGeometry | null;
  onApplyBoundary: (g: GeoJSONGeometry) => void;
  onApplyAlignment: (g: GeoJSONGeometry) => void;
  onClearBoundary?: () => void;
  onClearAlignment?: () => void;
}) {
  const { activeTool, activateTool, drawVertices, popDrawVertex, clearDrawVertices } =
    useProjectStore();

  const select = (tool: MapTool) => {
    activateTool(tool, null);
    if (tool === "suggest-site") {
      toast("Click the map", { description: "Pick a point to generate site suggestions" });
    }
  };

  const stats = geometryStats(boundary, alignment);
  const drawing = drawVertices.length > 0;
  const hasGeometry = !!(boundary || alignment);

  return (
    <GlassCard
      hover
      className="pointer-events-auto absolute left-3 top-3 z-20 flex w-[min(100%,380px)] max-h-[calc(100%-5.5rem)] flex-col overflow-hidden sm:left-4 sm:top-4"
    >
      <div className="shrink-0 border-b border-border px-4 py-3 space-y-2">
        <h2 className="text-sm font-semibold text-foreground">Site geometry</h2>
        <p className="text-xs text-muted-foreground">
          Draw or apply a suggestion. Optional — skip to continue without geometry.
        </p>
        <div className="flex flex-wrap gap-2">
          <Badge variant={boundary ? "success" : "secondary"} className="text-[10px] font-normal">
            Boundary {boundary ? "set" : "none"}
          </Badge>
          <Badge variant={alignment ? "success" : "secondary"} className="text-[10px] font-normal">
            Alignment {alignment ? "set" : "none"}
          </Badge>
        </div>
      </div>

      <div className="shrink-0 border-b border-border px-4 py-3 space-y-2">
        <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
          Drawing tools
        </p>
        <div className="grid grid-cols-4 gap-1.5">
          <ToolIcon label="Select" icon={MousePointer2} active={activeTool === "select"} onClick={() => select("select")} hint="Select / pan" />
          <ToolIcon label="Draw boundary polygon" icon={SquareDashed} active={activeTool === "draw-polygon"} onClick={() => select("draw-polygon")} hint="Draw boundary polygon" />
          <ToolIcon label="Draw road/alignment line" icon={Waypoints} active={activeTool === "draw-line"} onClick={() => select("draw-line")} hint="Draw road/alignment line" />
          <ToolIcon label="Draw rectangle" icon={RectangleHorizontal} active={activeTool === "draw-rectangle"} onClick={() => select("draw-rectangle")} hint="Draw rectangle site" />
          <ToolIcon label="Corridor" icon={Route} active={activeTool === "draw-corridor"} onClick={() => select("draw-corridor")} hint="Corridor with width" />
          <ToolIcon label="Smart suggest" icon={Sparkles} active={activeTool === "suggest-site"} onClick={() => select("suggest-site")} hint="AI suggestions at map point" />
          <ToolIcon label="Undo" icon={Undo2} active={false} onClick={() => drawVertices.length > 0 && popDrawVertex()} hint="Undo last vertex" />
          <ToolIcon label="Clear" icon={Trash2} active={false} onClick={() => { clearDrawVertices(); select("select"); }} hint="Clear current draw" />
        </div>
        <p className="text-[11px] leading-snug text-muted-foreground min-h-[2rem]">
          {toolInstruction(activeTool)}
          {drawing && <span className="text-foreground-secondary"> · {drawVertices.length} point(s)</span>}
        </p>
      </div>

      <div className="shrink-0 border-b border-border px-4 py-3">
        <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground mb-2">
          Selected geometry
        </p>
        {hasGeometry ? (
          <dl className="grid grid-cols-2 gap-2 text-[11px]">
            <div className="rounded-lg border border-border bg-[rgba(5,7,10,0.5)] px-2.5 py-2">
              <dt className="text-muted-foreground">Boundary area</dt>
              <dd className="font-mono font-medium text-foreground mt-0.5">
                {stats.areaSqm != null ? `${Math.round(stats.areaSqm).toLocaleString()} m²` : "—"}
              </dd>
            </div>
            <div className="rounded-lg border border-border bg-[rgba(5,7,10,0.5)] px-2.5 py-2">
              <dt className="text-muted-foreground">Alignment length</dt>
              <dd className="font-mono font-medium text-foreground mt-0.5">
                {stats.lengthM != null ? `${Math.round(stats.lengthM).toLocaleString()} m` : "—"}
              </dd>
            </div>
          </dl>
        ) : (
          <EmptyState
            icon={SquareDashed}
            title="No geometry yet"
            description="Draw a boundary or choose a suggested corridor to continue."
            className="py-4"
          />
        )}
        {(boundary || alignment) && (
          <div className="flex gap-2 mt-2">
            {boundary && onClearBoundary && (
              <Button type="button" variant="ghost" size="sm" className="h-7 text-[10px] px-2" onClick={onClearBoundary}>
                Clear boundary
              </Button>
            )}
            {alignment && onClearAlignment && (
              <Button type="button" variant="ghost" size="sm" className="h-7 text-[10px] px-2" onClick={onClearAlignment}>
                Clear alignment
              </Button>
            )}
          </div>
        )}
      </div>

      <div className="flex min-h-0 flex-1 flex-col overflow-hidden px-4 py-3">
        <SiteSuggestionsPanel
          sidebar
          autoLoadOnMount
          projectType={projectType}
          centerLng={centerLng}
          centerLat={centerLat}
          onApplyBoundary={async (s) => onApplyBoundary(s.geometry)}
          onApplyAlignment={async (s) => onApplyAlignment(s.geometry)}
        />
      </div>
    </GlassCard>
  );
}

"use client";

import { formatAreaForUnit, formatDistanceForUnit, lineLengthM, polygonAreaSqm } from "@/lib/geo";
import { toolInstruction } from "@/lib/map-draw";
import { Button } from "@/components/ui/button";
import { useProjectStore } from "@/stores/projectStore";

interface DrawHudProps {
  onConfirmSave?: () => void;
}

export default function DrawHud({ onConfirmSave }: DrawHudProps) {
  const activeTool = useProjectStore((s) => s.activeTool);
  const vertices = useProjectStore((s) => s.drawVertices);
  const measureUnit = useProjectStore((s) => s.measureUnit);
  const pendingSave = useProjectStore((s) => s.pendingSave);
  const corridorWidthM = useProjectStore((s) => s.corridorWidthM);
  const saving = useProjectStore(s => s.geometrySaving);
  const error = useProjectStore(s => s.drawingError);
  const editing = activeTool.startsWith("edit-");

  const instruction = toolInstruction(activeTool);

  let segmentLabel = "";
  let totalLabel = "";
  if (vertices.length >= 2) {
    const lastSeg = lineLengthM([vertices[vertices.length - 2], vertices[vertices.length - 1]]);
    segmentLabel = `Segment: ${formatDistanceForUnit(lastSeg, measureUnit)}`;
    totalLabel = `Total: ${formatDistanceForUnit(lineLengthM(vertices), measureUnit)}`;
  }
  const areaLabel =
    vertices.length >= 3 &&
    (activeTool === "draw-polygon" || activeTool === "measure-area" || activeTool === "draw-rectangle")
      ? `Area: ${formatAreaForUnit(polygonAreaSqm(vertices), measureUnit)}`
      : "";

  const pendingSummary =
    pendingSave?.kind === "boundary" && pendingSave.geometry.type === "Polygon"
      ? formatAreaForUnit(
          polygonAreaSqm((pendingSave.geometry.coordinates as [number, number][][])[0]),
          measureUnit,
        )
      : pendingSave?.kind === "alignment" && pendingSave.geometry.type === "LineString"
        ? formatDistanceForUnit(
            lineLengthM(pendingSave.geometry.coordinates as [number, number][]),
            measureUnit,
          )
        : "";

  return (
    <>
      {instruction && activeTool !== "select" && (!pendingSave || editing) && (
        <div className="absolute top-14 left-1/2 -translate-x-1/2 z-10 panel-glass rounded-md px-3 py-1.5 text-xs text-foreground border border-border/60 pointer-events-none max-w-[90vw] text-center">
          {instruction}
          {activeTool === "draw-corridor" && (
            <span className="ml-2 text-muted-foreground">· Width {corridorWidthM} m</span>
          )}
        </div>
      )}

      {(segmentLabel || areaLabel) && !pendingSave && activeTool.startsWith("draw") && (
        <div className="absolute bottom-2 left-2 z-10 panel px-3 py-2 text-xs font-medium space-y-0.5 pointer-events-none">
          {segmentLabel && <div>{segmentLabel}</div>}
          {totalLabel && vertices.length > 2 && <div>{totalLabel}</div>}
          {areaLabel && <div>{areaLabel}</div>}
        </div>
      )}

      {activeTool.startsWith("measure") && (segmentLabel || areaLabel) && (
        <div className="absolute bottom-2 left-2 z-10 panel px-3 py-1.5 text-xs font-medium pointer-events-none">
          {areaLabel || `${segmentLabel}${totalLabel ? ` · ${totalLabel}` : ""}`}
        </div>
      )}

      {pendingSave && !editing && (
        <div className="absolute bottom-2 left-1/2 -translate-x-1/2 z-20 panel-glass rounded-lg px-4 py-3 text-xs shadow-lg border border-primary/30 flex flex-col sm:flex-row items-center gap-3">
          <span>
            {pendingSave.kind === "boundary" ? "Boundary" : "Alignment"}: {pendingSummary} · Unsaved
          </span>
          <div className="flex gap-2 pointer-events-auto">
            <Button disabled={saving} size="sm" className="h-8 text-xs" onClick={onConfirmSave}>
              {saving ? "Saving…" : pendingSave.kind === "boundary" ? "Save boundary" : "Save alignment"}
            </Button>
            <Button
              size="sm"
              variant="ghost"
              className="h-7 text-xs"
              disabled={saving}
              onClick={() => useProjectStore.getState().activateTool(pendingSave.kind === "boundary" ? "edit-boundary" : "edit-alignment")}
            >
              Continue editing
            </Button>
            <Button disabled={saving} size="sm" variant="ghost" onClick={() => useProjectStore.getState().cancelDrawing()}>Discard draft</Button>
          </div>
        </div>
      )}
      {error && <div role="alert" className="absolute bottom-20 left-1/2 -translate-x-1/2 z-40 max-w-sm rounded border border-destructive bg-background p-3 text-xs">{error}</div>}
    </>
  );
}

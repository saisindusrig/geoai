"use client";

import { Trash2 } from "lucide-react";
import type { WorkspaceFeature } from "@/components/map/mapTypes";
import { formatArea, formatLength } from "@/lib/map/measurements";

interface FeaturePropertiesPanelProps {
  feature: WorkspaceFeature | null;
  onRename: (name: string) => void;
  onDelete: () => void;
}

function coordinateSummary(feature: WorkspaceFeature | null) {
  if (!feature) return "—";
  if (feature.geometry.type === "Point") {
    const [lng, lat] = feature.geometry.coordinates;
    return `${lat.toFixed(5)}, ${lng.toFixed(5)}`;
  }
  if (feature.geometry.type === "LineString") return `${feature.geometry.coordinates.length} vertices`;
  return `${feature.geometry.coordinates[0]?.length ?? 0} ring vertices`;
}

export default function FeaturePropertiesPanel({
  feature,
  onRename,
  onDelete,
}: FeaturePropertiesPanelProps) {
  return (
    <aside className="pointer-events-auto absolute right-4 top-24 z-30 hidden w-80 rounded-2xl border border-border bg-[rgba(5,7,10,0.82)] p-4 text-foreground-secondary shadow-2xl backdrop-blur-xl xl:block">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
            Feature Inspector
          </p>
          <p className="mt-1 text-sm font-semibold text-foreground">
            {feature ? feature.properties.name ?? "Unnamed feature" : "No selection"}
          </p>
        </div>
        {feature && (
          <button
            type="button"
            onClick={onDelete}
            className="flex h-8 w-8 items-center justify-center rounded-lg text-[#FCA5A5] hover:bg-[rgba(239,68,68,0.12)]"
            title="Delete selected"
          >
            <Trash2 className="h-4 w-4" />
          </button>
        )}
      </div>

      {!feature ? (
        <p className="mt-4 rounded-xl border border-[rgba(148,163,184,0.14)] bg-white/[0.04] px-3 py-3 text-[12px] leading-relaxed text-muted-foreground">
          Select a road, area, rectangle, point, or project geometry to inspect editable properties and measurements.
        </p>
      ) : (
        <div className="mt-4 space-y-3">
          <label className="block">
            <span className="text-[10px] uppercase tracking-wide text-muted-foreground">Name</span>
            <input
              value={feature.properties.name ?? ""}
              onChange={(event) => onRename(event.target.value)}
              className="mt-1 h-9 w-full rounded-lg border border-border bg-background px-3 text-[12px] text-foreground"
            />
          </label>

          <div className="grid grid-cols-2 gap-2 text-[11px]">
            <div className="rounded-xl border border-border bg-white/[0.04] px-3 py-2">
              <p className="text-[9px] uppercase tracking-wide text-muted-foreground">Type</p>
              <p className="mt-1 font-data text-foreground">{feature.properties.kind}</p>
            </div>
            <div className="rounded-xl border border-border bg-white/[0.04] px-3 py-2">
              <p className="text-[9px] uppercase tracking-wide text-muted-foreground">Coordinates</p>
              <p className="mt-1 truncate font-data text-foreground">{coordinateSummary(feature)}</p>
            </div>
            <div className="rounded-xl border border-border bg-white/[0.04] px-3 py-2">
              <p className="text-[9px] uppercase tracking-wide text-muted-foreground">Length</p>
              <p className="mt-1 font-data text-foreground">{formatLength(feature.properties.lengthM)}</p>
            </div>
            <div className="rounded-xl border border-border bg-white/[0.04] px-3 py-2">
              <p className="text-[9px] uppercase tracking-wide text-muted-foreground">Area</p>
              <p className="mt-1 font-data text-foreground">{formatArea(feature.properties.areaSqm)}</p>
            </div>
          </div>

          <pre className="max-h-40 overflow-auto rounded-xl border border-border bg-black/30 p-3 text-[10px] text-muted-foreground">
            {JSON.stringify(feature.properties, null, 2)}
          </pre>
        </div>
      )}
    </aside>
  );
}

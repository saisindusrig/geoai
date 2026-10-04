"use client";

import { cn } from "@/lib/utils";
import type { MapBasemap } from "@/lib/map-imagery";

const ALL_OPTIONS: { id: MapBasemap; label: string }[] = [
  { id: "satellite", label: "Satellite" },
  { id: "terrain", label: "Terrain" },
  { id: "street", label: "Streets" },
];

export default function MapStyleToggle({
  value,
  onChange,
  compact,
  className,
  view = "2d",
}: {
  value: MapBasemap;
  onChange: (v: MapBasemap) => void;
  compact?: boolean;
  className?: string;
  /** Topographic basemap is 2D-only; hidden in 3D so the globe stays on satellite. */
  view?: "2d" | "3d";
}) {
  const options = view === "3d" ? ALL_OPTIONS.filter((o) => o.id !== "terrain") : ALL_OPTIONS;

  return (
    <div
      className={cn(
        "inline-flex items-center gap-0.5 rounded-lg border border-border bg-card/90 p-0.5 backdrop-blur-md",
        className,
      )}
    >
      {options.map(({ id, label }) => (
        <button
          key={id}
          type="button"
          onClick={() => onChange(id)}
          className={cn(
            "rounded-md font-medium transition-all duration-200",
            compact ? "px-2 py-1 text-[10px]" : "px-2.5 py-1 text-[11px]",
            value === id
              ? "bg-primary/15 text-foreground border border-primary/30"
              : "text-muted-foreground hover:text-foreground hover:bg-surface-hover border border-transparent",
          )}
        >
          {label}
        </button>
      ))}
    </div>
  );
}

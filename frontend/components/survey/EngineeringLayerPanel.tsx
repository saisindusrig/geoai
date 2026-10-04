"use client";

import type { EngineeringLayer } from "@/lib/types";
import AccuracyBadge from "./AccuracyBadge";

export default function EngineeringLayerPanel({
  layers,
  compact,
}: {
  layers: EngineeringLayer[];
  compact?: boolean;
}) {
  if (!layers.length) {
    if (compact) return null;
    return <p className="text-xs text-muted-foreground">No engineering layers imported yet.</p>;
  }

  return (
    <ul className={compact ? "max-h-28 space-y-1 overflow-y-auto text-[10px]" : "max-h-40 space-y-1 overflow-y-auto text-xs"}>
      {layers.map((layer) => (
        <li key={layer.id} className="rounded border border-border px-2 py-1">
          <div className="flex items-center justify-between gap-2">
            <span className="font-medium truncate">{layer.name || layer.layer_type}</span>
            <AccuracyBadge tier={layer.metadata.tier} compact />
          </div>
          {!compact && (
            <p className="text-[10px] text-muted-foreground mt-0.5">
              {layer.layer_type}
              {layer.metadata.crsEpsg ? ` · EPSG:${layer.metadata.crsEpsg}` : ""}
            </p>
          )}
        </li>
      ))}
    </ul>
  );
}

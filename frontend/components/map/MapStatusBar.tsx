"use client";

import type { ProviderStatus, WorkspaceFeature, WorkspaceMapStatus } from "@/components/map/mapTypes";
import { formatArea, formatLength } from "@/lib/map/measurements";

interface MapStatusBarProps {
  status: WorkspaceMapStatus;
  selectedFeature: WorkspaceFeature | null;
  providerStatus: ProviderStatus;
  drawingError?: string | null;
}

export default function MapStatusBar({
  status,
  selectedFeature,
  providerStatus,
  drawingError,
}: MapStatusBarProps) {
  return (
    <div className="pointer-events-auto absolute bottom-4 left-4 right-4 z-30 overflow-x-auto rounded-2xl border border-border bg-[rgba(5,7,10,0.82)] px-3 py-2 text-[11px] text-muted-foreground shadow-2xl backdrop-blur-xl">
      <div className="flex min-w-max items-center gap-4">
        <span>
          Lat/Lng{" "}
          <b className="font-data text-foreground">
            {status.lngLat ? `${status.lngLat[1].toFixed(5)}, ${status.lngLat[0].toFixed(5)}` : "—"}
          </b>
        </span>
        <span>
          Zoom <b className="font-data text-foreground">{status.zoom.toFixed(1)}</b>
        </span>
        <span>
          Pitch <b className="font-data text-foreground">{status.pitch.toFixed(0)}°</b>
        </span>
        <span>
          Road length{" "}
          <b className="font-data text-foreground">{formatLength(selectedFeature?.properties.lengthM)}</b>
        </span>
        <span>
          Area <b className="font-data text-foreground">{formatArea(selectedFeature?.properties.areaSqm)}</b>
        </span>
        <span className="rounded-full border border-primary/25 bg-primary/10 px-2 py-0.5 text-foreground-secondary">
          Engine: {providerStatus.mapEngine}
        </span>
        {!providerStatus.googleMapsKey && (
          <span className="rounded-full border border-[rgba(245,158,11,0.24)] bg-[rgba(245,158,11,0.1)] px-2 py-0.5 text-[#FCD34D]">
            Google 3D key missing
          </span>
        )}
        {drawingError && (
          <span className="rounded-full border border-[rgba(239,68,68,0.24)] bg-[rgba(239,68,68,0.1)] px-2 py-0.5 text-[#FCA5A5]">
            {drawingError}
          </span>
        )}
      </div>
    </div>
  );
}

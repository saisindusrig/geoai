import { ScenegraphLayer } from "@deck.gl/mesh-layers";
import type { Layer } from "@deck.gl/core";
import { alignmentModelPlacement } from "@/lib/project-workflow";
import type { GeoJSONGeometry } from "@/lib/types";

interface DesignModelLayerOptions {
  modelUrl: string;
  centerLng: number;
  centerLat: number;
  alignment: GeoJSONGeometry | null;
  id?: string;
  opacity?: number;
  /** Deck altitude in meters (flyover deck clearance hint). */
  altitudeM?: number;
}

/** Anchor an exported design GLB (local meters, Y-up) on the map workspace. */
export function designModelLayer(options: DesignModelLayerOptions): Layer {
  const placement = alignmentModelPlacement(options.alignment, options.centerLng, options.centerLat);
  const bearingDeg = (placement.bearingRad * 180) / Math.PI;
  const altitudeM = options.altitudeM ?? 8;

  return new ScenegraphLayer({
    id: options.id ?? "design-model-glb",
    data: [
      {
        url: options.modelUrl,
        position: [placement.lng, placement.lat, altitudeM] as [number, number, number],
      },
    ],
    scenegraph: (d: { url: string }) => d.url,
    getPosition: (d: { position: [number, number, number] }) => d.position,
    getOrientation: () => [0, 90 - bearingDeg, 90],
    sizeScale: 1,
    pickable: false,
    opacity: options.opacity ?? 1,
    _lighting: "flat",
    onError: (error: Error) => {
      if (process.env.NODE_ENV === "development") {
        console.warn("[design-model-layer] Failed to load GLB:", error.message);
      }
    },
  });
}

import { PathLayer, PolygonLayer, ScatterplotLayer, TextLayer } from "@deck.gl/layers";
import type { Layer } from "@deck.gl/core";
import type { LineString, Point, Polygon, Position } from "geojson";
import type { JobStage } from "@/lib/generation-job";
import type { PreviewLayoutGeometry } from "@/lib/map/generation-preview-geometry";

interface PreviewLayerOptions {
  layout: PreviewLayoutGeometry;
  stage: JobStage | "idle";
  pulse: number;
  scanProgress: number;
  visibleCount: number;
  showLabels: boolean;
}

function pulseAlpha(base: number, pulse: number, amplitude = 0.35) {
  return Math.round(base * (1 - amplitude + amplitude * (0.5 + 0.5 * Math.sin(pulse * Math.PI * 2))));
}

export function buildGenerationPreviewLayers(options: PreviewLayerOptions): Layer[] {
  const { layout, stage, pulse, scanProgress, visibleCount, showLabels } = options;
  if (stage === "idle" || stage === "completed" || stage === "failed") return [];

  const layers: Layer[] = [];

  if (layout.boundaryRing && (stage === "queued" || stage === "analyzing_site" || stage === "generating_layout")) {
    layers.push(
      new PolygonLayer({
        id: "gen-preview-boundary-pulse",
        data: [{ polygon: layout.boundaryRing }],
        getPolygon: (d: { polygon: Position[] }) => d.polygon,
        getFillColor: [34, 211, 238, pulseAlpha(stage === "queued" ? 48 : 28, pulse)],
        getLineColor: [34, 211, 238, pulseAlpha(220, pulse, 0.45)],
        getLineWidth: stage === "queued" ? 4 : 3,
        lineWidthMinPixels: 2,
        stroked: true,
        filled: true,
        pickable: false,
        updateTriggers: {
          getFillColor: [pulse, stage],
          getLineColor: [pulse, stage],
        },
      }),
    );
  }

  if (layout.siteHighlight && (stage === "analyzing_site" || stage === "generating_layout" || stage === "generating_3d_preview" || stage === "calculating_boq")) {
    layers.push(
      new PolygonLayer({
        id: "gen-preview-site-highlight",
        data: [layout.siteHighlight],
        getPolygon: (d: Polygon) => d.coordinates[0],
        getFillColor: [59, 130, 246, stage === "analyzing_site" ? pulseAlpha(36, pulse) : 24],
        getLineColor: [59, 130, 246, 80],
        getLineWidth: 1,
        stroked: true,
        filled: true,
        pickable: false,
        updateTriggers: { getFillColor: [pulse, stage] },
      }),
    );
  }

  if (layout.boundaryRing && stage === "analyzing_site") {
    const scanY = layout.boundaryRing[0]
      ? scanProgress
      : 0;
    const ring = layout.boundaryRing;
    const minLat = Math.min(...ring.map((c) => c[1]));
    const maxLat = Math.max(...ring.map((c) => c[1]));
    const minLng = Math.min(...ring.map((c) => c[0]));
    const maxLng = Math.max(...ring.map((c) => c[0]));
    const y = minLat + (maxLat - minLat) * scanY;
    layers.push(
      new PathLayer({
        id: "gen-preview-scan-line",
        data: [
          {
            path: [
              [minLng, y],
              [maxLng, y],
            ] as [number, number][],
          },
        ],
        getPath: (d: { path: [number, number][] }) => d.path,
        getColor: [34, 211, 238, pulseAlpha(200, pulse, 0.25)],
        getWidth: 6,
        widthMinPixels: 3,
        pickable: false,
        updateTriggers: { getColor: [pulse, scanProgress] },
      }),
    );
  }

  if (
    stage === "generating_layout" ||
    stage === "generating_3d_preview" ||
    stage === "calculating_boq" ||
    stage === "exporting_model" ||
    stage === "saving_result"
  ) {
    const roads = layout.roads.slice(0, Math.max(1, Math.min(visibleCount, layout.roads.length)));
    if (roads.length) {
      layers.push(
        new PathLayer({
          id: "gen-preview-roads",
          data: roads,
          getPath: (d: LineString) => d.coordinates as [number, number][],
          getColor: [148, 163, 184, 180],
          getWidth: 5,
          widthMinPixels: 2,
          pickable: false,
        }),
      );
    }

    const blocks = layout.blocks.slice(0, Math.max(0, visibleCount - 1));
    if (blocks.length) {
      layers.push(
        new PolygonLayer({
          id: "gen-preview-blocks",
          data: blocks,
          getPolygon: (d: Polygon) => d.coordinates[0],
          getFillColor: [100, 116, 139, 70],
          getLineColor: [148, 163, 184, 160],
          getLineWidth: 2,
          extruded: true,
          getElevation: 8,
          pickable: false,
        }),
      );
    }

    const buildings = layout.buildings.slice(0, Math.max(0, visibleCount - 2));
    if (buildings.length) {
      layers.push(
        new PolygonLayer({
          id: "gen-preview-buildings",
          data: buildings,
          getPolygon: (d: Polygon) => d.coordinates[0],
          getFillColor: [59, 130, 246, 90],
          getLineColor: [191, 219, 254, 180],
          getLineWidth: 2,
          extruded: true,
          getElevation: (d: Polygon, { index }: { index: number }) => 12 + index * 6,
          pickable: false,
        }),
      );
    }

    if (layout.flyoverDeck && visibleCount >= 2) {
      layers.push(
        new PathLayer({
          id: "gen-preview-flyover",
          data: [layout.flyoverDeck],
          getPath: (d: LineString) => d.coordinates as [number, number][],
          getColor: [191, 219, 254, 200],
          getWidth: 10,
          widthMinPixels: 4,
          pickable: false,
        }),
      );
    }

    const piers = layout.piers.slice(0, Math.max(0, visibleCount - 1));
    if (piers.length) {
      layers.push(
        new ScatterplotLayer({
          id: "gen-preview-piers",
          data: piers,
          getPosition: (d: Point) => d.coordinates as [number, number],
          getFillColor: [125, 211, 252, 180],
          getRadius: 8,
          radiusMinPixels: 4,
          pickable: false,
        }),
      );
    }
  }

  const mapLabel =
    stage === "queued"
      ? "Preparing generation…"
      : stage === "analyzing_site"
        ? "Reading site geometry"
        : stage === "generating_layout"
          ? "Generating layout"
          : stage === "generating_3d_preview"
            ? "Generating 3D layout"
            : stage === "calculating_boq"
              ? "Estimating quantities"
              : stage === "exporting_model" || stage === "saving_result"
                ? "Finalizing design"
                : "";

  if (mapLabel && layout.boundaryRing) {
    const [lng, lat] = layout.boundaryRing[0] ?? [0, 0];
    layers.push(
      new TextLayer({
        id: "gen-preview-main-label",
        data: [{ position: [lng, lat], text: mapLabel }],
        getPosition: (d: { position: Position }) => d.position as [number, number],
        getText: (d: { text: string }) => d.text,
        getSize: 14,
        getColor: [248, 250, 252, 240],
        getBackgroundColor: [5, 7, 10, 200],
        backgroundPadding: [6, 4],
        fontFamily: "system-ui, sans-serif",
        pickable: false,
      }),
    );
  }

  if (showLabels && stage === "calculating_boq") {
    const labels = layout.labelAnchors.slice(0, Math.min(3, visibleCount));
    layers.push(
      new TextLayer({
        id: "gen-preview-boq-labels",
        data: labels,
        getPosition: (d: { position: Position }) => d.position as [number, number],
        getText: (d: { text: string }) => d.text,
        getSize: 12,
        getColor: [253, 224, 71, 240],
        getBackgroundColor: [5, 7, 10, 180],
        backgroundPadding: [4, 3],
        fontFamily: "system-ui, sans-serif",
        pickable: false,
      }),
    );
  }

  return layers;
}

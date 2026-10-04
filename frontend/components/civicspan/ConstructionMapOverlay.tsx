"use client";

import { MapboxOverlay } from "@deck.gl/mapbox";
import { PolygonLayer } from "@deck.gl/layers";
import { ScenegraphLayer } from "@deck.gl/mesh-layers";
import type { Layer } from "@deck.gl/core";
import type maplibregl from "maplibre-gl";
import { useEffect, useMemo, useRef } from "react";
import type { GeoPoint } from "@/lib/civicspan";
import type {
  ConstructionSpec,
  ConstructionStage,
} from "@/lib/construction";
import { spanMeters } from "@/lib/construction";

export type ConstructionMapPlacement = {
  rotationDeg: number;
  offsetAcrossM: number;
  scale: number;
  elevationM: number;
};

type MapBox = {
  id: string;
  polygon: [number, number, number][];
  height: number;
  color: [number, number, number, number];
};

const COLORS = {
  foundation: [71, 85, 80, 245] as [number, number, number, number],
  structure: [201, 221, 207, 250] as [number, number, number, number],
  detail: [114, 214, 190, 250] as [number, number, number, number],
};
const DUMMY_BRIDGE_NATIVE_LENGTH = 405.52701950073197;

function headingDegrees(start: GeoPoint, end: GeoPoint) {
  const lat1 = (start.lat * Math.PI) / 180;
  const lat2 = (end.lat * Math.PI) / 180;
  const dLng = ((end.lng - start.lng) * Math.PI) / 180;
  const y = Math.sin(dLng) * Math.cos(lat2);
  const x =
    Math.cos(lat1) * Math.sin(lat2) -
    Math.sin(lat1) * Math.cos(lat2) * Math.cos(dLng);
  return (Math.atan2(y, x) * 180) / Math.PI;
}

function offsetPoint(
  origin: GeoPoint,
  eastM: number,
  northM: number,
): [number, number] {
  const metersPerDegreeLat = 111_320;
  const metersPerDegreeLng =
    metersPerDegreeLat * Math.max(0.15, Math.cos((origin.lat * Math.PI) / 180));
  return [
    origin.lng + eastM / metersPerDegreeLng,
    origin.lat + northM / metersPerDegreeLat,
  ];
}

function localToLngLat(
  center: GeoPoint,
  acrossM: number,
  alongM: number,
  headingDeg: number,
): [number, number] {
  const heading = (headingDeg * Math.PI) / 180;
  const eastM = alongM * Math.sin(heading) + acrossM * Math.cos(heading);
  const northM = alongM * Math.cos(heading) - acrossM * Math.sin(heading);
  return offsetPoint(center, eastM, northM);
}

function rectangle(
  id: string,
  center: GeoPoint,
  widthM: number,
  lengthM: number,
  baseM: number,
  heightM: number,
  headingDeg: number,
  color: [number, number, number, number],
  acrossOffsetM = 0,
  alongOffsetM = 0,
): MapBox {
  const halfWidth = widthM / 2;
  const halfLength = lengthM / 2;
  const corners: [number, number][] = [
    [-halfWidth, -halfLength],
    [halfWidth, -halfLength],
    [halfWidth, halfLength],
    [-halfWidth, halfLength],
  ];
  return {
    id,
    polygon: corners.map(([across, along]) => {
      const [lng, lat] = localToLngLat(
        center,
        across + acrossOffsetM,
        along + alongOffsetM,
        headingDeg,
      );
      return [lng, lat, baseM];
    }),
    height: Math.max(0.08, heightM),
    color,
  };
}

function buildMapBoxes(
  spec: ConstructionSpec,
  stage: ConstructionStage,
  start: GeoPoint,
  end: GeoPoint,
  placement: ConstructionMapPlacement,
) {
  const center = {
    lng: (start.lng + end.lng) / 2,
    lat: (start.lat + end.lat) / 2,
  };
  const heading = headingDegrees(start, end) + placement.rotationDeg;
  const siteLength = Math.max(8, spanMeters(start, end));
  const linear = ["bridge", "flyover", "road", "pipeline"].includes(
    spec.project_type,
  );
  const length =
    (linear ? siteLength : spec.length_m) * placement.scale;
  const width = spec.width_m * placement.scale;
  const elevation = placement.elevationM;
  const showFoundation = stage !== "site";
  const showStructure = stage === "structure" || stage === "finish";
  const showFinish = stage === "finish";
  const boxes: MapBox[] = [];
  const add = (box: MapBox) => boxes.push(box);
  const rect = (
    id: string,
    widthM: number,
    lengthM: number,
    baseM: number,
    heightM: number,
    color: [number, number, number, number],
    acrossOffsetM = 0,
    alongOffsetM = 0,
  ) =>
    rectangle(
      id,
      center,
      widthM,
      lengthM,
      baseM + elevation,
      heightM,
      heading,
      color,
      acrossOffsetM + placement.offsetAcrossM,
      alongOffsetM,
    );

  if (spec.project_type === "building") {
    if (showFoundation)
      add(rect("foundation", width + 3, length + 3, 0, 1, COLORS.foundation));
    if (showStructure)
      add(rect("building", width, length, 1, spec.height_m * placement.scale, COLORS.structure));
    if (showFinish)
      add(rect("roof", width + 0.6, length + 0.6, spec.height_m * placement.scale + 1, 0.5, COLORS.detail));
    return boxes;
  }

  if (spec.project_type === "road") {
    if (showFoundation)
      add(rect("road-base", width + 4, length, 0, 0.35, COLORS.foundation));
    if (showStructure)
      add(rect("road-surface", width, length, 0.35, 0.25, COLORS.structure));
    if (showFinish)
      add(rect("road-centerline", 0.24, length * 0.94, 0.61, 0.06, COLORS.detail));
    return boxes;
  }

  if (spec.project_type === "pipeline") {
    if (showFoundation)
      add(rect("pipeline-base", width + 4, length, 0, 0.35, COLORS.foundation));
    if (showStructure)
      add(rect("pipeline", Math.max(1.4, width), length, 0.35, Math.max(1, spec.height_m), COLORS.structure));
    if (showFinish) {
      for (let index = 1; index <= 4; index += 1) {
        add(rect(`access-${index}`, width + 2, 2.4, 0.35, 2.2, COLORS.detail, 0, -length / 2 + (index * length) / 5));
      }
    }
    return boxes;
  }

  if (spec.project_type === "dam") {
    if (showFoundation)
      add(rect("dam-base", length + 16, width + 10, 0, 1.2, COLORS.foundation));
    if (showStructure)
      add(rect("dam-wall", length, width, 1.2, spec.height_m * placement.scale, COLORS.structure));
    if (showFinish)
      add(rect("spillway", length * 0.28, width + 1, spec.height_m * placement.scale + 1.2, 0.8, COLORS.detail));
    return boxes;
  }

  const supportCount = Math.max(2, spec.supports);
  if (showFoundation || showStructure) {
    for (let index = 1; index <= supportCount; index += 1) {
      const along = -length / 2 + (index * length) / (supportCount + 1);
      if (showFoundation)
        add(rect(`footing-${index}`, 4, 4, 0, 1.2, COLORS.foundation, 0, along));
      if (showStructure)
        add(rect(`pier-${index}`, 2, 2, 1.2, spec.height_m * placement.scale, COLORS.detail, 0, along));
    }
  }
  if (showStructure)
    add(rect("deck", width, length, spec.height_m * placement.scale, 0.9, COLORS.structure));
  if (showFinish) {
    add(rect("barrier-left", 0.22, length, spec.height_m * placement.scale + 0.9, 1.1, COLORS.detail, -width / 2));
    add(rect("barrier-right", 0.22, length, spec.height_m * placement.scale + 0.9, 1.1, COLORS.detail, width / 2));
  }
  return boxes;
}

export default function ConstructionMapOverlay({
  map,
  spec,
  stage,
  start,
  end,
  placement,
  visible,
  modelUrl,
}: {
  map: maplibregl.Map | null;
  spec: ConstructionSpec;
  stage: ConstructionStage;
  start: GeoPoint;
  end: GeoPoint;
  placement: ConstructionMapPlacement;
  visible: boolean;
  modelUrl?: string;
}) {
  const overlayRef = useRef<MapboxOverlay | null>(null);
  const layers = useMemo<Layer[]>(() => {
    if (!visible) return [];
    if (
      modelUrl &&
      (spec.project_type === "bridge" || spec.project_type === "flyover") &&
      (stage === "structure" || stage === "finish")
    ) {
      const baseCenter = {
        lng: (start.lng + end.lng) / 2,
        lat: (start.lat + end.lat) / 2,
      };
      const baseHeading = headingDegrees(start, end);
      const [lng, lat] = localToLngLat(
        baseCenter,
        placement.offsetAcrossM,
        0,
        baseHeading,
      );
      const heading = baseHeading + placement.rotationDeg;
      const targetLength = Math.max(8, spanMeters(start, end));
      return [
        new ScenegraphLayer({
          id: "dummy-bridge-scenegraph",
          data: [
            {
              url: modelUrl,
              position: [lng, lat, placement.elevationM] as [
                number,
                number,
                number,
              ],
            },
          ],
          scenegraph: (item: { url: string }) => item.url,
          getPosition: (item: {
            position: [number, number, number];
          }) => item.position,
          getOrientation: () => [0, 90 - heading, 90],
          sizeScale:
            (targetLength / DUMMY_BRIDGE_NATIVE_LENGTH) * placement.scale,
          pickable: false,
          _lighting: "pbr",
        }),
      ];
    }
    const boxes = buildMapBoxes(spec, stage, start, end, placement);
    const footprint = boxes.filter((box) =>
      [
        "deck",
        "building",
        "road-surface",
        "pipeline",
        "dam-wall",
      ].includes(box.id),
    );
    return [
      new PolygonLayer<MapBox>({
        id: "construction-map-footprint",
        data: footprint,
        getPolygon: (item) => item.polygon,
        getFillColor: [45, 212, 191, 42],
        getLineColor: [153, 246, 228, 245],
        getLineWidth: 3,
        lineWidthMinPixels: 2,
        filled: true,
        stroked: true,
        pickable: false,
      }),
      new PolygonLayer<MapBox>({
        id: "construction-map-model",
        data: boxes,
        getPolygon: (item) => item.polygon,
        getElevation: (item) => item.height,
        getFillColor: (item) => item.color,
        getLineColor: [226, 232, 240, 180],
        getLineWidth: 1,
        lineWidthMinPixels: 1,
        extruded: true,
        filled: true,
        stroked: true,
        wireframe: true,
        pickable: false,
        material: {
          ambient: 0.5,
          diffuse: 0.7,
          shininess: 24,
          specularColor: [90, 100, 96],
        },
      }),
    ];
  }, [end, modelUrl, placement, spec, stage, start, visible]);

  useEffect(() => {
    if (!map) return;
    if (!overlayRef.current) {
      overlayRef.current = new MapboxOverlay({
        interleaved: false,
        layers,
      });
      map.addControl(overlayRef.current as unknown as maplibregl.IControl);
    }
    overlayRef.current.setProps({ layers });
  }, [layers, map]);

  useEffect(
    () => () => {
      if (overlayRef.current && map) {
        try {
          map.removeControl(overlayRef.current as unknown as maplibregl.IControl);
        } catch {
          // The map may already be disposed during route teardown.
        }
      }
      overlayRef.current = null;
    },
    [map],
  );

  return null;
}

import type { Feature, FeatureCollection, Geometry, LineString, Point, Polygon, Position } from "geojson";
import type { WorkspaceFeature, WorkspaceFeatureCollection } from "@/components/map/mapTypes";
import type { GeoJSONGeometry } from "@/lib/types";
import { lineLengthM, polygonAreaSqm } from "@/lib/map/measurements";

export function emptyFeatureCollection(): WorkspaceFeatureCollection {
  return { type: "FeatureCollection", features: [] };
}

export function featureId(prefix = "feature") {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

export function closeRing(coords: Position[]) {
  if (!coords.length) return coords;
  const first = coords[0];
  const last = coords[coords.length - 1];
  if (first[0] === last[0] && first[1] === last[1]) return coords;
  return [...coords, first];
}

export function enrichFeature(feature: WorkspaceFeature): WorkspaceFeature {
  if (feature.geometry.type === "LineString") {
    const lengthM = lineLengthM(feature.geometry.coordinates);
    return { ...feature, properties: { ...feature.properties, lengthM } };
  }
  if (feature.geometry.type === "Polygon") {
    const areaSqm = polygonAreaSqm(feature.geometry.coordinates[0] ?? []);
    return { ...feature, properties: { ...feature.properties, areaSqm } };
  }
  return feature;
}

export function pointFeature(coordinate: Position): WorkspaceFeature {
  return {
    type: "Feature",
    geometry: { type: "Point", coordinates: coordinate } satisfies Point,
    properties: {
      id: featureId("point"),
      kind: "point",
      name: "Point marker",
      createdAt: new Date().toISOString(),
    },
  };
}

export function lineFeature(coordinates: Position[]): WorkspaceFeature {
  return enrichFeature({
    type: "Feature",
    geometry: { type: "LineString", coordinates } satisfies LineString,
    properties: {
      id: featureId("road"),
      kind: "road",
      name: "Road centerline",
      createdAt: new Date().toISOString(),
    },
  });
}

export function polygonFeature(coordinates: Position[], kind: "area" | "rectangle" = "area"): WorkspaceFeature {
  return enrichFeature({
    type: "Feature",
    geometry: { type: "Polygon", coordinates: [closeRing(coordinates)] } satisfies Polygon,
    properties: {
      id: featureId(kind),
      kind,
      name: kind === "rectangle" ? "Rectangle area" : "Polygon area",
      createdAt: new Date().toISOString(),
    },
  });
}

export function projectGeometryFeature(
  geometry: GeoJSONGeometry | null | undefined,
  kind: "project-boundary" | "project-alignment",
): WorkspaceFeature | null {
  if (!geometry) return null;
  if (geometry.type === "LineString") {
    return enrichFeature({
      type: "Feature",
      geometry,
      properties: {
        id: kind,
        kind,
        name: "Saved alignment",
        source: "project",
      },
    } as WorkspaceFeature);
  }
  if (geometry.type === "Polygon") {
    return enrichFeature({
      type: "Feature",
      geometry,
      properties: {
        id: kind,
        kind,
        name: "Saved boundary",
        source: "project",
      },
    } as WorkspaceFeature);
  }
  return null;
}

export function mergeProjectFeatures(
  boundary: GeoJSONGeometry | null | undefined,
  alignment: GeoJSONGeometry | null | undefined,
): WorkspaceFeatureCollection {
  return {
    type: "FeatureCollection",
    features: [projectGeometryFeature(boundary, "project-boundary"), projectGeometryFeature(alignment, "project-alignment")].filter(
      Boolean,
    ) as WorkspaceFeature[],
  };
}

export function asFeatureCollection(features: WorkspaceFeature[]): WorkspaceFeatureCollection {
  return { type: "FeatureCollection", features: features.map(enrichFeature) };
}

export function parseFeatureCollection(value: string): WorkspaceFeatureCollection | null {
  try {
    const parsed = JSON.parse(value) as FeatureCollection<Geometry, Record<string, unknown>>;
    if (parsed.type !== "FeatureCollection" || !Array.isArray(parsed.features)) return null;
    const features = parsed.features
      .filter((feature): feature is Feature<Point | LineString | Polygon, Record<string, unknown>> =>
        ["Point", "LineString", "Polygon"].includes(feature.geometry?.type ?? ""),
      )
      .map((feature) =>
        enrichFeature({
          ...feature,
          properties: {
            id: String(feature.properties?.id ?? featureId("imported")),
            kind: (feature.properties?.kind as WorkspaceFeature["properties"]["kind"]) ?? "area",
            ...feature.properties,
          },
        } as WorkspaceFeature),
      );
    return asFeatureCollection(features);
  } catch {
    return null;
  }
}

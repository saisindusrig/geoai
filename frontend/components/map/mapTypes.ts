import type maplibregl from "maplibre-gl";
import type { Feature, FeatureCollection, Geometry, LineString, Point, Polygon } from "geojson";

export type WorkspaceMapStyle = "dark" | "streets" | "satellite" | "hybrid";

export type WorkspaceDrawTool =
  | "select"
  | "point"
  | "road"
  | "polygon"
  | "rectangle"
  | "delete";

export type WorkspaceFeatureGeometry = Point | LineString | Polygon;

export type WorkspaceFeature = Feature<
  WorkspaceFeatureGeometry,
  {
    id: string;
    name?: string;
    kind: "point" | "road" | "area" | "rectangle" | "project-boundary" | "project-alignment";
    lengthM?: number;
    areaSqm?: number;
    createdAt?: string;
    source?: string;
    [key: string]: unknown;
  }
>;

export type WorkspaceFeatureCollection = FeatureCollection<WorkspaceFeatureGeometry, WorkspaceFeature["properties"]>;

export interface WorkspaceMapStatus {
  lngLat: [number, number] | null;
  zoom: number;
  pitch: number;
  bearing: number;
}

export interface ProviderStatus {
  mapboxToken: boolean;
  googleMapsKey: boolean;
  terrainAvailable: boolean;
  mapEngine: "maplibre" | "cesium";
  warnings: string[];
}

export interface MapLibreMapHandle {
  map: maplibregl.Map;
}

export type AnyGeoJsonFeature = Feature<Geometry, Record<string, unknown>>;

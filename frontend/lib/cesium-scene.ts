import { haversineM, lineLengthM, polygonAreaSqm } from "@/lib/geo";
import { corridorFromLine } from "@/lib/map-draw";
import type { GeoJSONFeature, GeoJSONGeometry } from "@/lib/types";
import type { TerrainProvider } from "cesium";

export interface Scene3DObjectInfo {
  id: string;
  name: string;
  type: string;
  material?: string;
  quantity?: string;
  lengthM?: number;
  widthM?: number;
  heightM?: number;
  areaSqm?: number;
  volumeM3?: number;
  properties?: Record<string, unknown>;
}

export type Scene3DLayerKey =
  | "terrain"
  | "roads"
  | "buildings"
  | "flyover"
  | "bridge"
  | "pipeline"
  | "drainage"
  | "excavation"
  | "construction"
  | "water"
  | "trees"
  | "labels";

export const SCENE3D_LAYER_LABELS: Record<Scene3DLayerKey, string> = {
  terrain: "Terrain",
  roads: "Roads (3D)",
  buildings: "Buildings",
  flyover: "Flyover / deck",
  bridge: "Bridge",
  pipeline: "Pipeline (underground)",
  drainage: "Drainage",
  excavation: "Excavation",
  construction: "Construction zone",
  water: "Water bodies",
  trees: "Trees / poles",
  labels: "Measurement labels",
};

export function defaultScene3DLayers(): Record<Scene3DLayerKey, boolean> {
  return {
    terrain: true,
    roads: true,
    buildings: true,
    flyover: true,
    bridge: true,
    pipeline: true,
    drainage: true,
    excavation: true,
    construction: true,
    water: true,
    trees: false,
    labels: true,
  };
}

export function estimateBuildingHeight(props: Record<string, unknown>): number {
  const levels = Number(props["building:levels"] ?? props.levels ?? 0);
  if (levels > 0) return levels * 3.2;
  const h = Number(props.height ?? props["building:height"] ?? 0);
  if (h > 0) return h;
  return 12;
}

export function featureFootprintArea(geom: GeoJSONGeometry): number {
  if (geom.type === "Polygon") {
    const ring = (geom.coordinates as [number, number][][])[0];
    return polygonAreaSqm(ring);
  }
  return 0;
}

export function roadWidthM(props: Record<string, unknown>): number {
  const lanes = Number(props.lanes ?? props["lanes:forward"] ?? 2);
  return Math.max(6, lanes * 3.5);
}

/** Build object metadata from a picked entity id + properties. */
export function objectInfoFromFeature(
  id: string,
  layer: Scene3DLayerKey,
  feature?: GeoJSONFeature,
  extra?: Partial<Scene3DObjectInfo>,
): Scene3DObjectInfo {
  const props = feature?.properties ?? {};
  const name = String(props.name ?? props["addr:street"] ?? id);
  const geom = feature?.geometry;
  let lengthM: number | undefined;
  let areaSqm: number | undefined;
  let heightM: number | undefined;
  let widthM: number | undefined;

  if (geom?.type === "LineString") {
    const coords = geom.coordinates as [number, number][];
    lengthM = lineLengthM(coords);
    widthM = roadWidthM(props);
  } else if (geom?.type === "Polygon") {
    areaSqm = featureFootprintArea(geom);
    heightM = estimateBuildingHeight(props);
    widthM = Math.sqrt(areaSqm);
  }

  const materialMap: Partial<Record<Scene3DLayerKey, string>> = {
    roads: "Asphalt",
    buildings: "Concrete / masonry",
    pipeline: "HDPE / steel pipe",
    drainage: "Concrete drain",
    excavation: "Soil cut",
    water: "Water surface",
    trees: "Vegetation",
    flyover: "Pre-stressed concrete deck",
    terrain: "Mixed terrain",
  };

  return {
    id,
    name,
    type: SCENE3D_LAYER_LABELS[layer] ?? layer,
    material: materialMap[layer],
    lengthM,
    widthM,
    heightM,
    areaSqm,
    volumeM3: areaSqm && heightM ? areaSqm * heightM : undefined,
    quantity: lengthM ? `${lengthM.toFixed(1)} m linear` : areaSqm ? `${areaSqm.toFixed(0)} m²` : undefined,
    properties: props,
    ...extra,
  };
}

export function corridorRing(coords: [number, number][], widthM: number): [number, number][] | null {
  const poly = corridorFromLine(coords, widthM);
  if (!poly || poly.type !== "Polygon") return null;
  return (poly.coordinates as [number, number][][])[0];
}

export function sampleLineAtDistance(
  coords: [number, number][],
  distM: number,
): [number, number] | null {
  if (coords.length < 2) return null;
  let acc = 0;
  for (let i = 1; i < coords.length; i++) {
    const seg = haversineM(coords[i - 1], coords[i]);
    if (acc + seg >= distM) return coords[i];
    acc += seg;
  }
  return coords[coords.length - 1];
}

export function slopePercent(riseM: number, runM: number): number {
  if (runM <= 0) return 0;
  return (riseM / runM) * 100;
}

export const ARCGIS_ELEVATION_URL =
  "https://elevation3d.arcgis.com/arcgis/rest/services/WorldElevation3D/Terrain3D/ImageServer";

type CesiumNamespace = typeof import("cesium");
type CesiumViewerLike = {
  scene?: {
    globe?: {
      terrainProvider?: TerrainProvider;
    };
  };
};

/**
 * Fixed ENU model matrix for Y-up design GLBs (engineering Z-up baked at export).
 */
export function buildDesignModelMatrix(
  Cesium: CesiumNamespace,
  lng: number,
  lat: number,
  bearingRad: number,
  heightM: number,
) {
  const position = Cesium.Cartesian3.fromDegrees(lng, lat, heightM);
  const hpr = new Cesium.HeadingPitchRoll(
    Cesium.Math.PI_OVER_TWO - bearingRad,
    0,
    0,
  );
  return Cesium.Transforms.headingPitchRollToFixedFrame(
    position,
    hpr,
    Cesium.Ellipsoid.WGS84,
    Cesium.Transforms.localFrameToFixedFrameGenerator("east", "north"),
    new Cesium.Matrix4(),
  );
}

/** Unknown elevations remain null, including the neutral ellipsoid fallback. */
export async function sampleTerrainHeightM(
  Cesium: CesiumNamespace,
  terrainProvider: TerrainProvider | null | undefined,
  lng: number,
  lat: number,
): Promise<number | null> {
  if (!terrainProvider || terrainProvider instanceof Cesium.EllipsoidTerrainProvider) {
    return null;
  }
  try {
    const [sample] = await Cesium.sampleTerrainMostDetailed(terrainProvider, [
      Cesium.Cartographic.fromDegrees(lng, lat),
    ]);
    return Number.isFinite(sample?.height) ? sample.height : null;
  } catch {
    return null;
  }
}

/** Ground height for design GLB models — samples real terrain elevation. */
export async function designModelGroundHeightM(
  Cesium: CesiumNamespace,
  viewer: CesiumViewerLike,
  lng: number,
  lat: number,
): Promise<number | null> {
  const provider = viewer.scene?.globe?.terrainProvider;
  const raw = await sampleTerrainHeightM(Cesium, provider, lng, lat);
  return raw;
}

/** Flat globe — no elevation mesh. */
export function createFlatTerrain(Cesium: CesiumNamespace) {
  return new Cesium.Terrain(Promise.resolve(new Cesium.EllipsoidTerrainProvider()));
}

const IS_DEV = process.env.NODE_ENV === "development";

/** Safe dev-only logging for Cesium layer / tile lifecycle. */
export function cesiumDevLog(
  category: "buildings" | "osm" | "tiles-ion" | "tiles-google" | "transparent" | "basemap" | "terrain",
  message: string,
  detail?: unknown,
) {
  if (!IS_DEV) return;
  if (detail !== undefined) {
    console.info(`[cesium:${category}] ${message}`, detail);
  } else {
    console.info(`[cesium:${category}] ${message}`);
  }
}

/** Context building extrusion fill (OSM footprints). */
export const CONTEXT_BUILDING_FILL = "rgba(110, 125, 145, 0.25)";
export const CONTEXT_BUILDING_OUTLINE = "rgba(110, 125, 145, 0.45)";

/** Ion OSM 3D buildings asset — neutral tint so tiles are not bright white blocks. */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function applyIonOsmBuildingTileStyle(Cesium: any, tileset: any) {
  tileset.style = new Cesium.Cesium3DTileStyle({
    color: "color('#B7C2CE', 1.0)",
  });
}

/** Reset globe translucency when transparent / underground mode is off. */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function resetGlobeTranslucency(viewer: any) {
  const globe = viewer?.scene?.globe;
  if (!globe?.translucency) return;
  globe.translucency.enabled = false;
  globe.translucency.frontFaceAlpha = 1;
  globe.translucency.backFaceAlpha = 1;
}

/** Restore full-opacity imagery after transparent mode. */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function resetImageryAlpha(viewer: any) {
  const layers = viewer?.imageryLayers;
  if (!layers) return;
  for (let i = 0; i < layers.length; i++) {
    layers.get(i).alpha = 1;
  }
}

/** Enable underground / survey translucency (Transparent mode only). */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function applyGlobeTranslucency(viewer: any, Cesium: any) {
  const globe = viewer.scene.globe;
  globe.translucency.enabled = true;
  globe.translucency.frontFaceAlpha = 1;
  globe.translucency.backFaceAlpha = 1;
  globe.translucency.frontFaceAlphaByDistance = new Cesium.NearFarScalar(400, 0.35, 8000, 0.95);
}

/** Remove every Cesium3DTileset from the scene (Ion / Google photorealistic city meshes). */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function purgeVendorTilesetsFromScene(viewer: any, Cesium: any) {
  const collection = viewer?.scene?.primitives;
  if (!collection) return;
  for (let i = collection.length - 1; i >= 0; i--) {
    const primitive = collection.get(i);
    if (!(primitive instanceof Cesium.Cesium3DTileset)) continue;
    try {
      primitive.show = false;
      collection.remove(primitive);
      if (!primitive.isDestroyed?.()) primitive.destroy();
    } catch {
      /* viewer shutting down */
    }
  }
  viewer.scene.requestRender?.();
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function createElevationTerrain(Cesium: any, ionToken?: string) {
  if (ionToken) {
    return Cesium.Terrain.fromWorldTerrain({ requestVertexNormals: true });
  }
  // A neutral globe is an intentional, honest fallback when Cesium ion has
  // not been configured. Do not silently source terrain from another vendor.
  return new Cesium.Terrain(Promise.resolve(new Cesium.EllipsoidTerrainProvider()));
}

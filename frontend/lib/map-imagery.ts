import { api, apiUrl } from "@/lib/api";
import type { StyleSpecification } from "maplibre-gl";

export type MapBasemap = "satellite" | "terrain" | "street";

export interface RasterTileConfig {
  provider: "mapbox" | "esri";
  max_zoom: number;
  tile_size: number;
  url_template: string;
  attribution: string;
}

export type SatelliteTileConfig = RasterTileConfig;
export type TerrainTileConfig = RasterTileConfig;

export interface TileProvidersResponse {
  satellite_config: SatelliteTileConfig;
  terrain_config: TerrainTileConfig;
  mapbox_available: boolean;
  cesium_ion_available: boolean;
  google_3d_tiles_available: boolean;
}

export interface MapRuntimeConfig {
  cesium_ion_token: string | null;
  google_maps_api_key: string | null;
}

let cachedProviders: TileProvidersResponse | null = null;
let cachedRuntimeConfig: MapRuntimeConfig | null = null;

export async function fetchTileProviders(): Promise<TileProvidersResponse> {
  if (cachedProviders) return cachedProviders;
  cachedProviders = await api.get<TileProvidersResponse>("/api/geocode/tile-providers");
  return cachedProviders;
}

export async function fetchMapRuntimeConfig(): Promise<MapRuntimeConfig> {
  if (cachedRuntimeConfig) return cachedRuntimeConfig;
  cachedRuntimeConfig = await api.get<MapRuntimeConfig>("/api/geocode/map-runtime-config");
  return cachedRuntimeConfig;
}

/** @deprecated use fetchTileProviders */
export async function fetchSatelliteConfig(): Promise<SatelliteTileConfig> {
  const data = await fetchTileProviders();
  return data.satellite_config;
}

export function resolveTileUrl(template: string): string {
  if (template.startsWith("http://") || template.startsWith("https://")) {
    return template;
  }
  return apiUrl(template);
}

export function rasterTileSource(config: RasterTileConfig) {
  const url = resolveTileUrl(config.url_template);
  return {
    type: "raster" as const,
    tiles: [url],
    tileSize: config.tile_size,
    maxzoom: config.max_zoom,
    attribution: config.attribution,
  };
}

export const satelliteRasterSource = rasterTileSource;
export const terrainRasterSource = rasterTileSource;

/** How far the user can zoom the map (tiles overzoom beyond source maxzoom). */
export const MAP_VIEW_MAX_ZOOM = 20;

export function basemapMaxZoom(basemap: MapBasemap, satelliteMaxZoom = 22): number {
  if (basemap === "satellite") return satelliteMaxZoom;
  return MAP_VIEW_MAX_ZOOM;
}

/** 3D globe never uses topographic imagery — satellite (or streets) only. */
export function basemapFor3d(basemap: MapBasemap): MapBasemap {
  return basemap === "street" ? "street" : "satellite";
}

function cesiumUrlTemplateProvider(
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  Cesium: any,
  config: RasterTileConfig,
  proxyRelative = false,
) {
  const url = proxyRelative ? resolveTileUrl(config.url_template) : config.url_template;
  return new Cesium.UrlTemplateImageryProvider({
    url,
    credit: config.attribution,
    maximumLevel: config.max_zoom,
    tileWidth: config.tile_size,
    tileHeight: config.tile_size,
  });
}

export async function createCesiumBasemapProvider(
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  Cesium: any,
  basemap: MapBasemap,
  providers: TileProvidersResponse,
) {
  const mode = basemapFor3d(basemap);
  if (mode === "satellite") {
    const config = providers.satellite_config;
    return cesiumUrlTemplateProvider(Cesium, config, config.provider === "mapbox");
  }
  if (mode === "street") {
    return new Cesium.UrlTemplateImageryProvider({
      url: "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
      credit: "© OpenStreetMap contributors",
      maximumLevel: 19,
    });
  }
  return cesiumUrlTemplateProvider(Cesium, providers.satellite_config);
}

/** Prefer Ion satellite imagery when configured; otherwise use the app's raster basemap. */
export async function loadCesiumBasemapProvider(
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  Cesium: any,
  basemap: MapBasemap,
  ionToken: string | null,
) {
  if (ionToken && basemapFor3d(basemap) === "satellite") {
    try {
      return await Cesium.IonImageryProvider.fromAssetId(2);
    } catch {
      // An expired or restricted Ion token must not leave the map blank.
    }
  }
  return createCesiumBasemapProvider(Cesium, basemap, await fetchTileProviders());
}

export function buildOsmStyle(
  satelliteSource: ReturnType<typeof rasterTileSource>,
  terrainSource: ReturnType<typeof rasterTileSource>,
): StyleSpecification {
  return {
    version: 8,
    sources: {
      osm: {
        type: "raster",
        tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
        tileSize: 256,
        maxzoom: 19,
        attribution: "© OpenStreetMap contributors",
      },
      satellite: satelliteSource,
      topo: terrainSource,
    },
    layers: [
      {
        id: "osm",
        type: "raster",
        source: "osm",
        layout: { visibility: "none" },
        paint: { "raster-resampling": "linear" },
      },
      {
        id: "satellite",
        type: "raster",
        source: "satellite",
        layout: { visibility: "none" },
        paint: { "raster-resampling": "linear" },
      },
      {
        id: "topo",
        type: "raster",
        source: "topo",
        layout: { visibility: "none" },
        paint: { "raster-resampling": "linear" },
      },
    ],
  };
}

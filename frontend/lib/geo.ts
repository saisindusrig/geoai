// Lightweight geodesic helpers (spherical approximations, fine for site scale)

import type { GeoJSONGeometry } from "@/lib/types";

const R = 6371000;
const rad = (d: number) => (d * Math.PI) / 180;

export function haversineM(a: [number, number], b: [number, number]): number {
  const dLat = rad(b[1] - a[1]);
  const dLng = rad(b[0] - a[0]);
  const h =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(rad(a[1])) * Math.cos(rad(b[1])) * Math.sin(dLng / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(h));
}

export function lineLengthM(coords: [number, number][]): number {
  let total = 0;
  for (let i = 1; i < coords.length; i++) total += haversineM(coords[i - 1], coords[i]);
  return total;
}

/** Spherical polygon area (ring of [lng, lat]) in square meters. */
export function polygonAreaSqm(ring: [number, number][]): number {
  if (ring.length < 3) return 0;
  let sum = 0;
  for (let i = 0; i < ring.length; i++) {
    const p1 = ring[i];
    const p2 = ring[(i + 1) % ring.length];
    sum += rad(p2[0] - p1[0]) * (2 + Math.sin(rad(p1[1])) + Math.sin(rad(p2[1])));
  }
  return Math.abs((sum * R * R) / 2);
}

export function formatDistance(m: number): string {
  return m >= 1000 ? `${(m / 1000).toFixed(2)} km` : `${m.toFixed(1)} m`;
}

export function formatArea(sqm: number): string {
  if (sqm >= 1e6) return `${(sqm / 1e6).toFixed(3)} km²`;
  if (sqm >= 10000) return `${(sqm / 10000).toFixed(2)} ha`;
  return `${sqm.toFixed(0)} m²`;
}

export function formatDistanceForUnit(m: number, unit: "m" | "ft"): string {
  if (unit === "ft") {
    const ft = m * 3.28084;
    return ft >= 5280 ? `${(ft / 5280).toFixed(2)} mi` : `${ft.toFixed(1)} ft`;
  }
  return formatDistance(m);
}

export function formatAreaForUnit(sqm: number, unit: "m" | "ft"): string {
  if (unit === "ft") {
    const sqft = sqm * 10.7639;
    if (sqft >= 43560) return `${(sqft / 43560).toFixed(2)} ac`;
    return `${sqft.toFixed(0)} ft²`;
  }
  return formatArea(sqm);
}

/** Web Mercator scale label at a latitude and zoom level. */
export function mapScaleLabel(lat: number, zoom: number): string {
  const metersPerPixel = (156543.03392 * Math.cos(rad(lat))) / 2 ** zoom;
  const metersPer100px = metersPerPixel * 100;
  if (metersPer100px >= 1000) return `${(metersPer100px / 1000).toFixed(1)} km / 100px`;
  return `${metersPer100px.toFixed(0)} m / 100px`;
}

function collectCoords(geometry: GeoJSONGeometry, out: [number, number][]) {
  if (geometry.type === "Point") {
    out.push(geometry.coordinates as [number, number]);
  } else if (geometry.type === "LineString") {
    out.push(...(geometry.coordinates as [number, number][]));
  } else if (geometry.type === "Polygon") {
    const rings = geometry.coordinates as [number, number][][];
    for (const ring of rings) out.push(...ring);
  } else if (geometry.type === "MultiPolygon") {
    const polys = geometry.coordinates as [number, number][][][];
    for (const poly of polys) {
      for (const ring of poly) out.push(...ring);
    }
  }
}

/** Lng/lat bounds [[west, south], [east, north]] for MapLibre fitBounds. */
export function bboxFromGeometries(
  ...geometries: (GeoJSONGeometry | null | undefined)[]
): [[number, number], [number, number]] | null {
  const coords: [number, number][] = [];
  for (const g of geometries) {
    if (g) collectCoords(g, coords);
  }
  if (!coords.length) return null;
  let minLng = coords[0][0];
  let maxLng = coords[0][0];
  let minLat = coords[0][1];
  let maxLat = coords[0][1];
  for (const [lng, lat] of coords) {
    minLng = Math.min(minLng, lng);
    maxLng = Math.max(maxLng, lng);
    minLat = Math.min(minLat, lat);
    maxLat = Math.max(maxLat, lat);
  }
  if (minLng === maxLng && minLat === maxLat) {
    const pad = 0.002;
    return [
      [minLng - pad, minLat - pad],
      [maxLng + pad, maxLat + pad],
    ];
  }
  return [
    [minLng, minLat],
    [maxLng, maxLat],
  ];
}

export function ringCentroid(ring: [number, number][]): [number, number] {
  const n = ring.length;
  const sx = ring.reduce((s, c) => s + c[0], 0);
  const sy = ring.reduce((s, c) => s + c[1], 0);
  return [sx / n, sy / n];
}

/** Approximate meter offsets to lng/lat delta at a given latitude. */
export function metersToDelta(lat: number, eastM: number, northM: number): [number, number] {
  const cosLat = Math.cos(rad(lat));
  const dLng = eastM / (R * cosLat);
  const dLat = northM / R;
  return [(dLng * 180) / Math.PI, (dLat * 180) / Math.PI];
}

/** Axis-aligned rectangle in meters (width E-W, height N-S) centered at lng/lat. */
export function rectanglePolygon(
  lng: number,
  lat: number,
  widthM: number,
  heightM: number,
): GeoJSONGeometry {
  const [dLng, dLat] = metersToDelta(lat, widthM / 2, heightM / 2);
  const ring: [number, number][] = [
    [lng - dLng, lat - dLat],
    [lng + dLng, lat - dLat],
    [lng + dLng, lat + dLat],
    [lng - dLng, lat + dLat],
    [lng - dLng, lat - dLat],
  ];
  return { type: "Polygon", coordinates: [ring] };
}

/** Corridor polygon: length along bearing (deg from N), width perpendicular. */
export function corridorPolygon(
  lng: number,
  lat: number,
  lengthM: number,
  widthM: number,
  bearingDeg: number,
): GeoJSONGeometry {
  const br = rad(bearingDeg);
  const halfL = lengthM / 2;
  const halfW = widthM / 2;
  const corners: [number, number][] = [];
  for (const [along, perp] of [
    [-halfL, -halfW],
    [halfL, -halfW],
    [halfL, halfW],
    [-halfL, halfW],
    [-halfL, -halfW],
  ]) {
    const north = along * Math.cos(br) - perp * Math.sin(br);
    const east = along * Math.sin(br) + perp * Math.cos(br);
    const [dLng, dLat] = metersToDelta(lat, east, north);
    corners.push([lng + dLng, lat + dLat]);
  }
  return { type: "Polygon", coordinates: [corners] };
}

export function lineFromCenter(
  lng: number,
  lat: number,
  lengthM: number,
  bearingDeg: number,
): GeoJSONGeometry {
  const br = rad(bearingDeg);
  const half = lengthM / 2;
  const [dLngA, dLatA] = metersToDelta(lat, -half * Math.sin(br), -half * Math.cos(br));
  const [dLngB, dLatB] = metersToDelta(lat, half * Math.sin(br), half * Math.cos(br));
  return {
    type: "LineString",
    coordinates: [
      [lng + dLngA, lat + dLatA],
      [lng + dLngB, lat + dLatB],
    ],
  };
}

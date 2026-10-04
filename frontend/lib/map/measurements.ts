import type { Position } from "geojson";

const EARTH_RADIUS_M = 6371008.8;
const SQM_PER_ACRE = 4046.8564224;

function rad(deg: number) {
  return (deg * Math.PI) / 180;
}

export function haversineDistanceM(a: Position, b: Position) {
  const lat1 = rad(a[1]);
  const lat2 = rad(b[1]);
  const dLat = lat2 - lat1;
  const dLng = rad(b[0] - a[0]);
  const h =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(lat1) * Math.cos(lat2) * Math.sin(dLng / 2) ** 2;
  return 2 * EARTH_RADIUS_M * Math.asin(Math.min(1, Math.sqrt(h)));
}

export function lineLengthM(coordinates: Position[]) {
  let total = 0;
  for (let i = 1; i < coordinates.length; i += 1) {
    total += haversineDistanceM(coordinates[i - 1], coordinates[i]);
  }
  return total;
}

export function polygonAreaSqm(ring: Position[]) {
  if (ring.length < 3) return 0;
  let area = 0;
  for (let i = 0; i < ring.length; i += 1) {
    const lower = ring[i];
    const upper = ring[(i + 1) % ring.length];
    area += rad(upper[0] - lower[0]) * (2 + Math.sin(rad(lower[1])) + Math.sin(rad(upper[1])));
  }
  return Math.abs((area * EARTH_RADIUS_M * EARTH_RADIUS_M) / 2);
}

export function formatLength(meters?: number | null) {
  if (meters == null || Number.isNaN(meters)) return "—";
  if (meters < 1000) return `${meters.toFixed(1)} m`;
  return `${(meters / 1000).toFixed(2)} km`;
}

export function formatArea(sqm?: number | null) {
  if (sqm == null || Number.isNaN(sqm)) return "—";
  const hectares = sqm / 10000;
  const acres = sqm / SQM_PER_ACRE;
  return `${sqm.toFixed(0)} sq.m · ${hectares.toFixed(2)} ha · ${acres.toFixed(2)} ac`;
}

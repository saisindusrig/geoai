import type { GeoJSONGeometry } from "./types";
import { geometryToVertices } from "./map-draw";

/** Plan geometry only; does not assert survey accuracy or elevation. */
export function boundaryError(geometry: GeoJSONGeometry): string | null {
  if (geometry.type !== "Polygon") return "Draw a polygon boundary.";
  const points = geometryToVertices(geometry);
  if (points.length < 3 || new Set(points.map(p => p.join(","))).size !== points.length)
    return "Use at least three distinct vertices; remove repeated points.";
  if (points.some(p => p.length !== 2 || !p.every(Number.isFinite) || Math.abs(p[0]) > 180 || Math.abs(p[1]) > 90))
    return "Boundary coordinates are invalid. Redraw the boundary.";
  const cross = (a: number[], b: number[], c: number[]) => (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]);
  const on = (a: number[], b: number[], p: number[]) => cross(a,b,p) === 0 && p.every((v,k) => v >= Math.min(a[k],b[k]) && v <= Math.max(a[k],b[k]));
  for (let i=0; i<points.length; i++) for (let j=i+1; j<points.length; j++) {
    if (j === i+1 || i === 0 && j === points.length-1) continue;
    const a=points[i], b=points[(i+1)%points.length], c=points[j], d=points[(j+1)%points.length];
    if (cross(a,b,c)*cross(a,b,d) < 0 && cross(c,d,a)*cross(c,d,b) < 0 || on(a,b,c) || on(a,b,d) || on(c,d,a) || on(c,d,b))
      return "Boundary edges cross or overlap. Move or undo a vertex.";
  }
  // Translate first to avoid cancellation at large longitude/latitude offsets.
  const area = points.reduce((sum,p,i) => { const q=points[(i+1)%points.length], o=points[0]; return sum+(p[0]-o[0])*(q[1]-o[1])-(q[0]-o[0])*(p[1]-o[1]); },0);
  return Math.abs(area) <= 1e-16 ? "Boundary has no usable area. Move a vertex off the line." : null;
}

import { haversineM } from "./geo";
export type MeasurementPoint = {
  longitude: number; latitude: number; elevation: number | null;
  source: string; dataset: number | null; version: number | null;
  horizontalReference: string; verticalReference: string;
  status: string; classification: "VISUAL_REFERENCE" | "SURVEY_DERIVED" | "ENGINEERING_RESULT" | "UNKNOWN";
};
export function measurementValues(kind: string, points: MeasurementPoint[]) {
  const a = points[0], b = points[1];
  if (!a) return {};
  if (kind === "height") return { elevation_m: a.elevation };
  if (kind === "area") {
    if (points.length < 3) return { area_m2: null };
    const radians = Math.PI / 180, radius = 6371008.8;
    const positions = points.map(point => [(point.longitude - a.longitude) * radians * radius * Math.cos(a.latitude * radians), (point.latitude - a.latitude) * radians * radius]);
    const area = Math.abs(positions.reduce((sum,point,index) => { const next = positions[(index + 1) % positions.length]; return sum + point[0] * next[1] - next[0] * point[1]; },0)) / 2;
    return { area_m2: area };
  }
  if (!b) return {};
  const horizontal = haversineM([a.longitude,a.latitude],[b.longitude,b.latitude]);
  const vertical = a.elevation === null || b.elevation === null || a.verticalReference !== b.verticalReference ? null : b.elevation - a.elevation;
  return { horizontal_m: horizontal, vertical_delta_m: vertical,
    distance_m: vertical === null ? null : Math.hypot(horizontal,vertical),
    grade_percent: vertical === null || horizontal === 0 ? null : vertical / horizontal * 100,
    angle_deg: vertical === null || horizontal === 0 ? null : Math.atan2(vertical,horizontal) * 180 / Math.PI,
    clearance_m: vertical === null ? null : Math.abs(vertical) };
}
export function measurementClassification(points: MeasurementPoint[]) {
  if (!points.length || points.some(point => point.classification === "UNKNOWN" || point.elevation === null)) return "UNKNOWN";
  if (points.some(point => point.classification === "VISUAL_REFERENCE")) return "VISUAL_REFERENCE";
  if (points.some(point => point.classification === "SURVEY_DERIVED")) return "SURVEY_DERIVED";
  return "ENGINEERING_RESULT";
}

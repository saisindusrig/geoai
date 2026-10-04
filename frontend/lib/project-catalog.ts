import { assetDefinition } from "@/lib/asset-types";
import type { ProjectType } from "@/lib/types";

/** Base generator family — maps extended types to existing design pipelines. */
export type ProjectTypeFamily = "flyover" | "building" | "pipeline" | "road";

export interface ProjectTypeOption {
  id: ProjectType;
  label: string;
  desc: string;
  category: "transport" | "structures" | "utilities" | "civil";
}

export interface UnitOption {
  id: string;
  label: string;
  desc: string;
}

export const PROJECT_TYPE_OPTIONS: ProjectTypeOption[] = [
  { id: "flyover", label: "Flyover / Overpass", desc: "Elevated road on piers", category: "transport" },
  { id: "bridge", label: "Bridge / Viaduct", desc: "Span over water or gap", category: "transport" },
  { id: "interchange", label: "Grade Separator", desc: "Multi-level junction / ramp system", category: "transport" },
  { id: "road", label: "Road Segment", desc: "At-grade pavement & shoulders", category: "transport" },
  { id: "railway", label: "Railway / Metro", desc: "Track alignment & embankment", category: "transport" },
  { id: "tunnel", label: "Tunnel / Underpass", desc: "Buried or cut-and-cover corridor", category: "transport" },
  { id: "building", label: "Building Massing", desc: "Multi-floor RCC concept", category: "structures" },
  { id: "dam", label: "Dam / Reservoir", desc: "Embankment or gravity dam concept", category: "structures" },
  { id: "substation", label: "Substation Yard", desc: "Electrical switchyard layout", category: "structures" },
  { id: "retaining_wall", label: "Retaining Wall", desc: "Earth retention along alignment", category: "structures" },
  { id: "pipeline", label: "Pipeline / Drainage", desc: "Trench + pipe alignment", category: "utilities" },
  { id: "culvert", label: "Culvert / Cross-drain", desc: "Short span under road or rail", category: "utilities" },
  { id: "wastewater", label: "Wastewater / STP", desc: "Treatment plant footprint", category: "utilities" },
  { id: "solar_farm", label: "Solar / Renewable", desc: "PV array site layout", category: "civil" },
];

export const UNIT_OPTIONS: UnitOption[] = [
  { id: "metric", label: "Metric", desc: "m, m², m³, kg" },
  { id: "metric_mt", label: "Metric (tonnes)", desc: "m, m³, MT, kg" },
  { id: "si", label: "SI standard", desc: "m, mm, kg, kN" },
  { id: "imperial", label: "Imperial (US)", desc: "ft, ft², yd³, lb" },
  { id: "ft_in", label: "Feet & inches", desc: "ft, in, lb" },
  { id: "us_customary", label: "US customary", desc: "ft, sf, cy, tons" },
  { id: "indian", label: "Indian BOQ", desc: "m, cum, MT, bags" },
];

const TYPE_FAMILY: Record<ProjectType, ProjectTypeFamily> = {
  flyover: "flyover",
  bridge: "flyover",
  interchange: "flyover",
  building: "building",
  dam: "building",
  substation: "building",
  wastewater: "building",
  solar_farm: "building",
  pipeline: "pipeline",
  culvert: "pipeline",
  road: "road",
  railway: "road",
  tunnel: "road",
  retaining_wall: "road",
};

const ALIGNMENT_TYPES = new Set<ProjectType>([
  "flyover",
  "bridge",
  "interchange",
  "pipeline",
  "culvert",
  "road",
  "railway",
  "tunnel",
  "retaining_wall",
]);

export function projectTypeFamily(type: ProjectType): ProjectTypeFamily {
  return TYPE_FAMILY[type];
}

export function projectTypeNeedsAlignment(type: ProjectType): boolean {
  return ALIGNMENT_TYPES.has(type);
}

export function projectTypeLabel(type: ProjectType): string {
  return PROJECT_TYPE_OPTIONS.find((o) => o.id === type)?.label ?? assetDefinition(type)?.name ?? type;
}

export function unitLabel(units: string): string {
  return UNIT_OPTIONS.find((o) => o.id === units)?.label ?? units;
}

export const PROJECT_TYPE_CATEGORIES: { id: ProjectTypeOption["category"]; label: string }[] = [
  { id: "transport", label: "Transport" },
  { id: "structures", label: "Structures" },
  { id: "utilities", label: "Utilities" },
  { id: "civil", label: "Site & civil" },
];

import type {
  EditableModelComponent,
  EditableModelDocument,
  GeometrySpec,
  ModelImpact,
  Project,
} from "@/lib/types";

const COLORS: Record<string, string> = {
  deck: "#B8C0CC",
  road: "#263241",
  asphalt: "#263241",
  barriers: "#E2E8F0",
  piers: "#60A5FA",
  foundations: "#94A3B8",
  excavation: "#F59E0B",
  pipe: "#22D3EE",
};

const vec3 = (value: unknown, fallback: [number, number, number]): [number, number, number] =>
  Array.isArray(value) && value.length === 3
    ? [Number(value[0]), Number(value[1]), Number(value[2])]
    : fallback;

export function documentFromGeometrySpec(
  project: Project,
  scenarioId: number,
  spec: GeometrySpec,
): EditableModelDocument {
  const seen = new Set<string>();
  const components: EditableModelComponent[] = (spec.objects ?? []).map((object, index) => {
    const raw = `${object.layer}-${object.name}`.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
    let id = raw || `component-${index + 1}`;
    let suffix = 2;
    while (seen.has(id)) id = `${raw}-${suffix++}`;
    seen.add(id);
    const isBox = object.kind === "box";
    return {
      id,
      parent_id: null,
      name: object.name,
      category: object.layer,
      visible: true,
      locked: false,
      geometry: isBox
        ? { kind: "box", size: vec3(object.size, [1, 1, 1]) }
        : {
            kind: "cylinder",
            start: vec3(object.start, [0, 0, 0]),
            end: vec3(object.end, [0, 0, 1]),
            radius_m: Number(object.radius_m ?? 0.5),
          },
      transform: {
        position: isBox ? vec3(object.center, [0, 0, 0]) : [0, 0, 0],
        rotation_deg: [0, 0, Number(object.rotation_z_deg ?? 0)],
        scale: [1, 1, 1],
      },
      material: {
        name: "Generated material",
        color: COLORS[object.layer.toLowerCase()] ?? "#94A3B8",
        roughness: 0.75,
        metalness: 0,
      },
      quantity: { included: true },
    };
  });
  return {
    schema_version: 1,
    project_id: project.id,
    scenario_id: scenarioId,
    project_type: project.project_type,
    units: "metric",
    origin: {
      lng: project.center_lng ?? 77.5946,
      lat: project.center_lat ?? 12.9716,
      elevation_m: 0,
      heading_deg: 0,
    },
    generator_parameters: {},
    components,
    metadata: { source: "generated_fallback", frame: "local_enu_meters" },
    structural_layout: { rule_preset: { min_member_spacing_m: 1, max_slope_percent: 12, min_clearance_m: 3, max_dimension_m: 500 }, assumptions: ["Conceptual layout generated from available project data."] },
  };
}

export function estimateDocument(document: EditableModelDocument | null): ModelImpact | null {
  if (!document) return null;
  let concrete = 0;
  let asphalt = 0;
  let excavation = 0;
  let steel = 0;
  for (const component of document.components) {
    if (!component.visible || component.quantity?.included === false) continue;
    let volume = 0;
    if (component.geometry.kind === "box" || component.geometry.kind === "extrusion") {
      volume = component.geometry.size.reduce((total, value, i) => total * value * component.transform.scale[i], 1);
    } else if (component.geometry.kind === "cylinder" || component.geometry.kind === "sweep") {
      const { start, end, radius_m } = component.geometry;
      const length = Math.hypot(end[0] - start[0], end[1] - start[1], end[2] - start[2]);
      volume = Math.PI * radius_m * radius_m * length * component.transform.scale[0] * component.transform.scale[1];
    }
    const layer = component.category.toLowerCase();
    if (layer.includes("excav") || layer.includes("trench")) excavation += volume;
    else if (layer.includes("road") || layer.includes("asphalt")) asphalt += volume;
    else if (layer.includes("steel") || layer.includes("truss") || layer.includes("arch")) steel += volume * 7850;
    else concrete += volume;
  }
  const rebar = concrete * 110;
  const total = concrete * 8500 + asphalt * 11000 + excavation * 250 + (steel + rebar) * 75;
  return {
    quantities: {
      concrete_m3: concrete,
      cement_bags: concrete * 7.2,
      steel_kg: steel,
      rebar_kg: rebar,
      excavation_m3: excavation,
      backfill_m3: 0,
      formwork_sqm: concrete ? concrete ** (2 / 3) * 6 : 0,
      asphalt_m3: asphalt,
      pipe_length_m: 0,
      pipe_diameter_mm: 0,
    },
    total_cost_estimate: total,
    currency: "INR",
  };
}

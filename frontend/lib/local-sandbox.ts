import type { EditableModelDocument, Project, StructuralElementType } from "@/lib/types";
import { CONSTRUCTION_TYPES, type ConstructionType } from "@/lib/construction";

export const LOCAL_SANDBOX_PROJECT_ID = 999999;
export const LOCAL_SANDBOX_PATH = `/projects/${LOCAL_SANDBOX_PROJECT_ID}/workspace?local=1`;

const STORAGE_KEY = "geoai-local-3d-sandbox";
export const SANDBOX_LAYOUT_KEY = `${STORAGE_KEY}-layout`;
export type SandboxView = "grid" | "map";
export type SandboxPayload = {
  version: 1;
  draft: LocalSandboxDraft;
  document: EditableModelDocument;
  view: SandboxView;
  savedAt: string;
};

export const COMPONENT_SIZES: Record<StructuralElementType, [number, number, number]> = {
  column: [0.4, 0.4, 3], beam: [5, 0.3, 0.5], wall: [5, 0.2, 3],
  slab: [5, 5, 0.2], foundation: [2, 2, 0.6], building: [10, 10, 3],
  road: [20, 7.5, 0.3], bridge: [20, 8, 1], retaining_wall: [10, 0.5, 3],
  drainage: [10, 0.5, 0.5], pipeline: [10, 0.3, 0.3], utility: [2, 2, 1],
  zone: [10, 10, 0.05], grid: [10, 10, 0.02], site_boundary: [20, 20, 0.02],
  construction_phase: [10, 10, 0.05],
};

export type LocalSandboxDraft = {
  name: string;
  projectType: ConstructionType;
  crossing: "waterway" | "road" | "terrain" | "unknown";
  start: { lat: number; lng: number };
  end: { lat: number; lng: number };
  updatedAt: string;
};

const DEFAULT_DRAFT: LocalSandboxDraft = {
  name: "Local 3D Sandbox",
  projectType: "flyover",
  crossing: "road",
  start: { lat: 12.971598, lng: 77.594566 },
  end: { lat: 12.97321, lng: 77.60212 },
  updatedAt: "2026-01-01T00:00:00.000Z",
};

function isDraft(value: unknown): value is LocalSandboxDraft {
  if (!value || typeof value !== "object") return false;
  const draft = value as Partial<LocalSandboxDraft>;
  return (
    typeof draft.name === "string" &&
    CONSTRUCTION_TYPES.includes(draft.projectType as ConstructionType) &&
    ["waterway", "road", "terrain", "unknown"].includes(draft.crossing ?? "") &&
    validLocation(draft.start) &&
    validLocation(draft.end) &&
    typeof draft.updatedAt === "string" && Number.isFinite(Date.parse(draft.updatedAt))
  );
}

export function readLocalSandboxDraft(): LocalSandboxDraft {
  if (typeof window === "undefined") return DEFAULT_DRAFT;
  try {
    const saved = window.localStorage.getItem(SANDBOX_LAYOUT_KEY);
    if (saved) {
      const payload = JSON.parse(saved);
      if (isDraft(payload?.draft)) return payload.draft;
    }
  } catch { /* Preserve legacy settings even when the newer layout is unreadable. */ }
  try {
    const value = JSON.parse(window.localStorage.getItem(STORAGE_KEY) ?? "null");
    return isDraft(value) ? value : DEFAULT_DRAFT;
  } catch {
    return DEFAULT_DRAFT;
  }
}

function validLocation(point: unknown): boolean {
  if (!point || typeof point !== "object") return false;
  const p = point as { lat?: number; lng?: number };
  return Number.isFinite(p.lat) && Number.isFinite(p.lng) && Math.abs(p.lat!) <= 90 && Math.abs(p.lng!) <= 180;
}

const record = (value: unknown): value is Record<string, unknown> => Boolean(value && typeof value === "object" && !Array.isArray(value));
const finite = (value: unknown): value is number => typeof value === "number" && Number.isFinite(value);
const vector = (value: unknown, positive = false): boolean => Array.isArray(value) && value.length === 3 && value.every((n) => finite(n) && (!positive || n > 0));

/** Validate the complete backup before it can replace a working layout. */
export function parseSandboxPayload(input: unknown): SandboxPayload {
  if (!record(input) || input.version !== 1) throw new Error("Unsupported sandbox file version. Expected version 1.");
  if (!isDraft(input.draft) || !["grid", "map"].includes(String(input.view)) || typeof input.savedAt !== "string" || !Number.isFinite(Date.parse(input.savedAt))) throw new Error("Invalid sandbox settings.");
  const doc = input.document;
  if (!record(doc) || doc.schema_version !== 1 || doc.project_id !== LOCAL_SANDBOX_PROJECT_ID || doc.scenario_id !== 0 || doc.units !== "metric" || typeof doc.project_type !== "string" || !record(doc.generator_parameters) || !record(doc.metadata) || doc.metadata.frame !== "local_enu_meters" || typeof doc.metadata.source !== "string") throw new Error("Invalid sandbox document.");
  if (!record(doc.origin) || !validLocation(doc.origin) || !finite(doc.origin.elevation_m) || !finite(doc.origin.heading_deg)) throw new Error("Invalid geographic origin.");
  if (!Array.isArray(doc.components) || doc.components.length > 10000) throw new Error("Invalid component list (maximum 10,000 components).");
  const ids = new Set<string>();
  for (const c of doc.components) {
    if (!record(c) || typeof c.id !== "string" || !c.id.trim() || ids.has(c.id) || (c.parent_id !== null && typeof c.parent_id !== "string") || typeof c.name !== "string" || typeof c.category !== "string" || typeof c.visible !== "boolean" || typeof c.locked !== "boolean") throw new Error("Component identifiers or properties are invalid.");
    ids.add(c.id);
    if (!record(c.transform) || !vector(c.transform.position) || !vector(c.transform.rotation_deg) || !vector(c.transform.scale, true)) throw new Error(`Invalid transform for ${c.name}.`);
    if (!record(c.material) || typeof c.material.name !== "string" || typeof c.material.color !== "string" || !/^#[0-9a-f]{6}$/i.test(c.material.color) || !finite(c.material.roughness) || !finite(c.material.metalness) || c.material.roughness < 0 || c.material.roughness > 1 || c.material.metalness < 0 || c.material.metalness > 1) throw new Error(`Invalid material for ${c.name}.`);
    const g = c.geometry;
    if (!record(g)) throw new Error("Missing component geometry.");
    if (g.kind === "asset_instance") throw new Error("External model assets are not supported. Import primitive sandbox components only.");
    if (g.kind === "box" || g.kind === "extrusion") {
      if (!vector(g.size, true)) throw new Error(`Dimensions must be positive for ${c.name}.`);
    } else if (g.kind === "cylinder" || g.kind === "sweep") {
      if (!vector(g.start) || !vector(g.end) || !finite(g.radius_m) || g.radius_m <= 0 || (g.start as number[]).every((n, i) => n === (g.end as number[])[i])) throw new Error(`Invalid cylinder geometry for ${c.name}.`);
    } else throw new Error("Unsupported component geometry.");
    if (c.quantity !== undefined && (!record(c.quantity) || (c.quantity.included !== undefined && typeof c.quantity.included !== "boolean"))) throw new Error("Invalid quantity setting.");
  }
  for (const c of doc.components) if (c.parent_id !== null && (!ids.has(c.parent_id) || c.parent_id === c.id)) throw new Error("Invalid parent identifier.");
  return JSON.parse(JSON.stringify(input)) as SandboxPayload;
}

export function emptySandboxDocument(project: Project): EditableModelDocument {
  return {
    schema_version: 1, project_id: LOCAL_SANDBOX_PROJECT_ID, scenario_id: 0,
    project_type: project.project_type, units: "metric",
    origin: { lng: project.center_lng ?? 77.594566, lat: project.center_lat ?? 12.971598, elevation_m: 0, heading_deg: 0 },
    generator_parameters: {}, components: [], metadata: { source: "local_sandbox", frame: "local_enu_meters" },
  };
}

export function readSandboxLayout(): { payload: SandboxPayload | null; error: string | null } {
  try {
    const raw = window.localStorage.getItem(SANDBOX_LAYOUT_KEY);
    return { payload: raw ? parseSandboxPayload(JSON.parse(raw)) : null, error: null };
  } catch (error) {
    return { payload: null, error: error instanceof Error ? error.message : "Saved layout could not be read." };
  }
}

export function sandboxPayload(document: EditableModelDocument, view: SandboxView, draft = readLocalSandboxDraft()): SandboxPayload {
  return { version: 1, draft, document, view, savedAt: new Date().toISOString() };
}

export function writeSandboxLayout(payload: SandboxPayload): void {
  const validated = parseSandboxPayload(payload);
  window.localStorage.setItem(SANDBOX_LAYOUT_KEY, JSON.stringify(validated));
}

export function localSandboxProject(draft = readLocalSandboxDraft()): Project {
  return {
    id: LOCAL_SANDBOX_PROJECT_ID,
    name: draft.name,
    project_type: draft.projectType,
    status: "local",
    units: "metric",
    location_name: `Local ${draft.crossing} test site`,
    center_lat: Number(((draft.start.lat + draft.end.lat) / 2).toFixed(6)),
    center_lng: Number(((draft.start.lng + draft.end.lng) / 2).toFixed(6)),
    boundary_geojson: null,
    alignment_geojson: {
      type: "LineString",
      coordinates: [
        [draft.start.lng, draft.start.lat],
        [draft.end.lng, draft.end.lat],
      ],
    },
    folder_id: null,
    created_at: "2026-01-01T00:00:00.000Z",
    updated_at: draft.updatedAt,
    disclaimer:
      "Local sandbox only. No data, AI request, or project is sent to the GeoAI backend.",
  };
}

export function saveLocalSandboxDraft(
  changes: Omit<LocalSandboxDraft, "updatedAt">,
): Project {
  const draft: LocalSandboxDraft = {
    ...changes,
    updatedAt: new Date().toISOString(),
  };
  if (typeof window !== "undefined") {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(draft));
  }
  return localSandboxProject(draft);
}

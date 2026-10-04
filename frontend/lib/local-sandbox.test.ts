// @vitest-environment jsdom
import { beforeEach, describe, expect, it, vi } from "vitest";
import {
  LOCAL_SANDBOX_PATH,
  LOCAL_SANDBOX_PROJECT_ID,
  localSandboxProject,
  emptySandboxDocument, parseSandboxPayload, readLocalSandboxDraft, readSandboxLayout,
  sandboxPayload, writeSandboxLayout, SANDBOX_LAYOUT_KEY,
} from "@/lib/local-sandbox";

beforeEach(() => { window.localStorage.clear(); vi.restoreAllMocks(); });

describe("local 3D sandbox", () => {
  it("uses a stable local route and a valid flyover project", () => {
    const project = localSandboxProject();

    expect(LOCAL_SANDBOX_PATH).toBe(
      "/projects/999999/workspace?local=1",
    );
    expect(project.id).toBe(LOCAL_SANDBOX_PROJECT_ID);
    expect(project.project_type).toBe("flyover");
    expect(project.alignment_geojson?.type).toBe("LineString");
  });

  it("starts with an empty metric document and migrates existing project settings", () => {
    window.localStorage.setItem("geoai-local-3d-sandbox", JSON.stringify({ name: "My site", projectType: "road", crossing: "terrain", start: { lat: 12, lng: 77 }, end: { lat: 13, lng: 78 }, updatedAt: "2026-10-02T00:00:00Z" }));
    const project = localSandboxProject();
    const doc = emptySandboxDocument(project);
    expect(project.name).toBe("My site");
    expect(doc.origin).toMatchObject({ lat: 12.5, lng: 77.5 });
    expect(doc.components).toEqual([]);
    expect(doc.scenario_id).toBe(0);
    expect(readSandboxLayout()).toEqual({ payload: null, error: null });
  });

  it("round trips project settings, layout, and preferred view", () => {
    const payload = sandboxPayload(emptySandboxDocument(localSandboxProject()), "map");
    payload.draft.name = "Saved site";
    writeSandboxLayout(payload);
    expect(readSandboxLayout().payload).toEqual(payload);
    expect(readLocalSandboxDraft().name).toBe("Saved site");
    expect(parseSandboxPayload(JSON.parse(JSON.stringify(payload)))).toEqual(payload);
  });

  it("preserves corrupt stored data for recovery", () => {
    window.localStorage.setItem(SANDBOX_LAYOUT_KEY, "{bad json");
    expect(readSandboxLayout().error).toBeTruthy();
    expect(window.localStorage.getItem(SANDBOX_LAYOUT_KEY)).toBe("{bad json");
  });

  it("surfaces storage failures", () => {
    vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => { throw new Error("Quota exceeded"); });
    expect(() => writeSandboxLayout(sandboxPayload(emptySandboxDocument(localSandboxProject()), "grid"))).toThrow("Quota exceeded");
  });

  it("rejects unsupported versions, nonfinite origins, and asset references", () => {
    const payload = sandboxPayload(emptySandboxDocument(localSandboxProject()), "grid");
    expect(() => parseSandboxPayload({ ...payload, version: 2 })).toThrow("version");
    expect(() => parseSandboxPayload({ ...payload, document: { ...payload.document, origin: { ...payload.document.origin, lat: Infinity } } })).toThrow("origin");
    const component = { id: "a", parent_id: null, name: "Asset", category: "building", visible: true, locked: false, geometry: { kind: "asset_instance", asset_url: "https://example.com/model.glb" }, transform: { position: [0, 0, 0], rotation_deg: [0, 0, 0], scale: [1, 1, 1] }, material: { name: "Concrete", color: "#60a5fa", roughness: 0.75, metalness: 0 } };
    expect(() => parseSandboxPayload({ ...payload, document: { ...payload.document, components: [component] } })).toThrow("assets");
  });

  it("rejects duplicate identifiers, zero dimensions, and invalid transforms", () => {
    const payload = sandboxPayload(emptySandboxDocument(localSandboxProject()), "grid");
    const component = { id: "a", parent_id: null, name: "Box", category: "building", visible: true, locked: false, geometry: { kind: "box", size: [1, 1, 1] }, transform: { position: [0, 0, 0], rotation_deg: [0, 0, 0], scale: [1, 1, 1] }, material: { name: "Concrete", color: "#60a5fa", roughness: 0.75, metalness: 0 } };
    const withComponents = (components: unknown[]) => ({ ...payload, document: { ...payload.document, components } });
    expect(() => parseSandboxPayload(withComponents([component, component]))).toThrow("identifiers");
    expect(() => parseSandboxPayload(withComponents([{ ...component, geometry: { kind: "box", size: [0, 1, 1] } }]))).toThrow("positive");
    expect(() => parseSandboxPayload(withComponents([{ ...component, transform: { ...component.transform, position: [NaN, 0, 0] } }]))).toThrow("transform");
  });
});

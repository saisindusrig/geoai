import { describe, expect, it } from "vitest";
import { documentFromGeometrySpec, estimateDocument } from "@/lib/editable-model";
import type { Project } from "@/lib/types";

const project: Project = {
  id: 7,
  name: "Bridge",
  project_type: "bridge",
  status: "designed",
  units: "metric",
  location_name: "Bengaluru",
  center_lat: 12.97,
  center_lng: 77.59,
  boundary_geojson: null,
  alignment_geojson: null,
  folder_id: null,
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
  disclaimer: "Concept only",
};

describe("editable model documents", () => {
  it("keeps excluded visual concept quantities unknown", () => {
    const document = documentFromGeometrySpec(project, 12, {
      objects: [{ kind: "box", name: "Slab", layer: "slab", size: [5, 3, .2], center: [0, 0, 3] }],
    });
    document.components[0].quantity = { included: false };
    expect(estimateDocument(document)).toBeNull();
  });
  it("creates stable semantic components from generated geometry", () => {
    const document = documentFromGeometrySpec(project, 12, {
      frame: "local_meters",
      objects: [
        { kind: "box", name: "Deck", layer: "deck", size: [20, 8, 1], center: [0, 0, 5] },
        { kind: "box", name: "Deck", layer: "deck", size: [20, 1, 1], center: [0, 4, 6] },
      ],
    });
    expect(document.components.map((item) => item.id)).toEqual(["deck-deck", "deck-deck-2"]);
    expect(document.origin).toMatchObject({ lng: 77.59, lat: 12.97 });
  });

  it("previews estimate impacts from component transforms", () => {
    const document = documentFromGeometrySpec(project, 12, {
      objects: [{ kind: "box", name: "Deck", layer: "deck", size: [10, 5, 1], center: [0, 0, 0] }],
    });
    document.components[0].transform.scale = [2, 1, 1];
    const impact = estimateDocument(document);
    expect(impact?.quantities.concrete_m3).toBe(100);
    expect(impact?.total_cost_estimate).toBeGreaterThan(0);
  });
});

it('retains XYZ box rotations in a geometry spec instead of silently reducing tilt to yaw',()=>{
 const doc=documentFromGeometrySpec(project,12,{objects:[{kind:'box',name:'Tilted beam',layer:'beam',size:[5,.3,.45],center:[0,0,3],rotation_z_deg:30,rotation_deg:[10,20,30]}]});
 expect(doc.components[0].transform.rotation_deg).toEqual([10,20,30]);
});

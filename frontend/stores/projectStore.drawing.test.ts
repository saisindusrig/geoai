import { beforeEach, expect, it } from "vitest";
import { useProjectStore } from "./projectStore";
import type { GeoJSONGeometry, Project } from "@/lib/types";

const line: GeoJSONGeometry = { type: "LineString", coordinates: [[77, 12], [77.001, 12.001]] };
const polygon: GeoJSONGeometry = { type: "Polygon", coordinates: [[[77, 12], [77.001, 12], [77.001, 12.001], [77, 12]]] };
beforeEach(() => useProjectStore.setState({ project: null, activeTool: "select", drawnBoundary: null, drawnAlignment: null, pendingSave: null, drawVertices: [] }));

it("finishes alignment drawing atomically, keeping the draft available for editing and saving", () => {
  const store = useProjectStore.getState();
  store.activateTool("draw-line");
  store.finishDrawing({ kind: "alignment", geometry: line });
  expect(useProjectStore.getState()).toMatchObject({ activeTool: "select", drawnAlignment: line, pendingSave: { kind: "alignment", geometry: line } });
  store.activateTool("edit-alignment");
  expect(useProjectStore.getState().pendingSave?.geometry).toEqual(line);
  store.setActiveTool("select");
  expect(useProjectStore.getState().pendingSave?.geometry).toEqual(line);
});

it("retains boundary and alignment drafts independently in the displayed geometry", () => {
  const store = useProjectStore.getState();
  store.finishDrawing({ kind: "boundary", geometry: polygon });
  store.finishDrawing({ kind: "alignment", geometry: line });
  expect(useProjectStore.getState().drawnBoundary).toEqual(polygon);
  expect(useProjectStore.getState().drawnAlignment).toEqual(line);
});

it("clears draft geometry when opening a different project", () => {
  const store = useProjectStore.getState();
  store.setProject({ id: 5 } as Project);
  store.finishDrawing({ kind: "alignment", geometry: line });
  store.setProject({ id: 6 } as Project);
  expect(useProjectStore.getState()).toMatchObject({ pendingSave: null, drawnAlignment: null, drawnBoundary: null, activeTool: "select" });
});

it("cancels edited boundary drafts without changing saved site data", () => {
  const store=useProjectStore.getState();
  store.setProject({id:5,boundary_geojson:polygon} as Project);
  store.finishDrawing({kind:"boundary",geometry:{...polygon,coordinates:[[[0,0],[1,0],[1,1],[0,0]]]}});
  store.activateTool("edit-boundary"); store.cancelDrawing();
  expect(useProjectStore.getState()).toMatchObject({pendingSave:null,drawnBoundary:null,activeTool:"select"});
  expect(useProjectStore.getState().project?.boundary_geojson).toEqual(polygon);
});

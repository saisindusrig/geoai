import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import MapViewerArea from "./MapViewerArea";
import { useProjectStore } from "@/stores/projectStore";
import { verticesToPolygon } from "@/lib/map-draw";
import type { Project } from "@/lib/types";
import type { EditableModelEditor } from "@/hooks/useEditableModelEditor";

const mocks = vi.hoisted(() => ({ put: vi.fn() }));
vi.mock("next/dynamic", () => ({ default: () => () => <div>Cesium canvas</div> }));
vi.mock("@/lib/api", () => ({ api: mocks, formatApiErrorMessage: (e: Error) => e.message }));
vi.mock("@/lib/toast", () => ({ toast: vi.fn() }));
vi.mock("@/components/layout/WorkspaceMapContext", () => ({ useWorkspaceMap: () => ({}) }));
vi.mock("@/components/layout/CommandPalette", () => ({ default: () => null }));
vi.mock("./Scene3DOverlay", () => ({ default: () => null }));
const boundary = verticesToPolygon([[77,12],[77.001,12],[77.001,12.001]]);
const project = { id: 7, status: "local", boundary_geojson: boundary } as Project;
beforeEach(() => { vi.clearAllMocks(); useProjectStore.setState({ project, activeTool: "select", pendingSave: {kind:"boundary",geometry:boundary}, drawnBoundary:boundary, drawnAlignment:null, geometrySaving:false, drawingError:null }); });
afterEach(cleanup);
it("preserves unsaved model edits when a site boundary is confirmed", async () => {
  const save=vi.fn();
  render(<MapViewerArea project={project} showToolbar={false} editor={{dirty:true} as EditableModelEditor} onBoundaryDrawn={save} />);
  fireEvent.click(screen.getByRole("button",{name:"Save boundary"}));
  expect(await screen.findByRole("alert")).toHaveTextContent("Both drafts are retained");
  expect(save).not.toHaveBeenCalled(); expect(useProjectStore.getState().pendingSave).not.toBeNull();
});
it("retains failed boundary saves for retry and persists once through the refresh callback", async () => {
  const save = vi.fn().mockRejectedValueOnce(new Error("Network unavailable")).mockResolvedValueOnce(undefined);
  render(<MapViewerArea project={project} showToolbar={false} onBoundaryDrawn={save} />);
  fireEvent.click(screen.getByRole("button",{name:"Save boundary"}));
  expect(await screen.findByRole("alert")).toHaveTextContent("Network unavailable");
  expect(useProjectStore.getState().drawnBoundary).toEqual(boundary);
  expect(useProjectStore.getState().pendingSave).not.toBeNull();
  fireEvent.click(screen.getByRole("button",{name:"Save boundary"}));
  await waitFor(() => expect(useProjectStore.getState().pendingSave).toBeNull());
  expect(save).toHaveBeenCalledTimes(2);
  expect(mocks.put).not.toHaveBeenCalled();
});
it("rejects crossing boundaries without replacing saved geometry", async () => {
  const save = vi.fn();
  useProjectStore.setState({ drawnBoundary: verticesToPolygon([[0,0],[1,1],[0,1],[1,0]]) });
  render(<MapViewerArea project={project} showToolbar={false} onBoundaryDrawn={save} />);
  fireEvent.click(screen.getByRole("button",{name:"Save boundary"}));
  expect(await screen.findByRole("alert")).toHaveTextContent("edges cross");
  expect(save).not.toHaveBeenCalled();
  expect(useProjectStore.getState().project?.boundary_geojson).toEqual(boundary);
});
it("discards a pending boundary and restores saved geometry without persistence", () => {
  const save = vi.fn();
  render(<MapViewerArea project={project} showToolbar={false} onBoundaryDrawn={save} />);
  fireEvent.click(screen.getByRole("button",{name:"Discard draft"}));
  expect(useProjectStore.getState()).toMatchObject({pendingSave:null,drawnBoundary:null});
  expect(useProjectStore.getState().project?.boundary_geojson).toEqual(boundary);
  expect(save).not.toHaveBeenCalled();
});

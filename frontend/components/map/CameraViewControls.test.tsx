import React from "react";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import CameraViewControls from "./CameraViewControls";
import { api } from "@/lib/api";
vi.mock("@/lib/api", () => ({ api: { get: vi.fn(), post: vi.fn() }, formatApiErrorMessage: (e: Error) => e.message }));
afterEach(() => { cleanup(); vi.clearAllMocks(); });
function setup(projectId?: number) {
  const fromDegrees = vi.fn((lng, lat, height) => ({ lng, lat, height }));
  const viewer = { isDestroyed: () => false, scene: { globe: { getHeight: () => 920 }, requestRender: vi.fn() }, camera: { flyToBoundingSphere: vi.fn(), positionWC: { x: 1, y: 2, z: 3 }, heading: 1, pitch: 2, roll: 0, frustum: {} } };
  const Cesium = { Cartesian3: { fromDegrees }, Cartographic: { fromDegrees: () => ({}) }, BoundingSphere: class { constructor(public center: unknown, public radius: number) {} }, HeadingPitchRange: class {}, Math: { toRadians: (n: number) => n * Math.PI / 180 }, OrthographicFrustum: class {} };
  render(<CameraViewControls viewer={viewer as unknown as import("cesium").Viewer} Cesium={Cesium as unknown as typeof import("cesium")} longitude={77} latitude={12} projectId={projectId} />);
  return { viewer, fromDegrees };
}
it("targets camera presets at the terrain surface rather than sea level", () => {
  const { viewer, fromDegrees } = setup();
  fireEvent.click(screen.getByRole("button", { name: "TOP" }));
  expect(fromDegrees).toHaveBeenCalledWith(77, 12, 920);
  expect(viewer.camera.flyToBoundingSphere).toHaveBeenCalled();
});
it("saves a trimmed camera name and reports completion", async () => {
  vi.mocked(api.get).mockResolvedValue([]);
  vi.mocked(api.post).mockResolvedValue({ id: 1 });
  setup(5);
  fireEvent.change(screen.getByRole("textbox", { name: "Camera view name" }), { target: { value: "  North view  " } });
  fireEvent.click(screen.getByRole("button", { name: "Save current camera" }));
  await waitFor(() => expect(screen.getByRole("status")).toHaveTextContent("Viewpoint saved"));
  expect(api.post).toHaveBeenCalledWith(expect.stringContaining("camera-views"), expect.objectContaining({ name: "North view", position: [1, 2, 3] }));
});

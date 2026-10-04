import React from "react";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import EngineeringEvidencePanel from "./EngineeringEvidencePanel";
import SunStudyControls from "./SunStudyControls";
import { api } from "@/lib/api";

vi.mock("@/lib/api", () => ({ api: { get: vi.fn(), post: vi.fn(), put: vi.fn() }, formatApiErrorMessage: (error: Error) => error.message }));
vi.mock("@/components/layout/WorkspaceMapControl", () => ({ default: ({ children }: { children: React.ReactNode }) => <div>{children}</div> }));
vi.mock("@/components/map/CameraViewControls", () => ({ default: () => <div>Camera controls</div> }));
const keys = ["horizontal_crs", "vertical_reference", "units", "terrain", "coverage", "spatial_backend", "authoritative_raster"];
const evidence = (status: string) => ({ readiness: "VISUAL_REFERENCE", measurement_class: "VISUAL", evidence: Object.fromEntries(keys.map((key) => [key, { status }])) });
const origin = { lng: 77, lat: 12, elevation_m: 0, heading_deg: 20 };
beforeEach(() => { vi.clearAllMocks(); });
afterEach(cleanup);

describe("site data panel", () => {
  it("explains missing evidence and prevents unsupported placement requests", async () => {
    vi.mocked(api.get).mockImplementation(async (path) => path.endsWith("/evidence") ? evidence("MISSING") : { placement: null });
    render(<EngineeringEvidencePanel projectId={5} revisionId={2} origin={origin} onPlacement={vi.fn()} />);
    fireEvent(window, new Event("geoai:open-site-data"));
    await waitFor(() => expect(screen.queryByText("Checking project evidence…")).not.toBeInTheDocument());
    fireEvent.click(screen.getByRole("tab", { name: "Placement" }));
    expect(screen.getByRole("button", { name: "Place model on ground" })).toBeDisabled();
    expect(screen.getByText(/Ground placement needs/)).toBeInTheDocument();
    expect(api.post).not.toHaveBeenCalled();
  });

  it("resamples the accepted anchor, preserves its offset and uses the saved elevation", async () => {
    const saved = { longitude: 78, latitude: 13, elevation: 500, heading: 45, offset: 2, status: "VALID" };
    vi.mocked(api.get).mockImplementation(async (path) => path.endsWith("/evidence") ? evidence("VALID") : { placement: saved });
    vi.mocked(api.post).mockResolvedValue({ id: 10, status: "VALID", elevation: 510, vertical_reference: { type: "ELLIPSOIDAL" }, terrain_version_id: 4 });
    vi.mocked(api.put).mockResolvedValue({ status: "VALID", anchor_elevation: 511 });
    const onPlacement = vi.fn();
    render(<EngineeringEvidencePanel projectId={5} revisionId={2} origin={origin} onPlacement={onPlacement} />);
    fireEvent(window, new Event("geoai:open-site-data"));
    fireEvent.click(screen.getByRole("tab", { name: "Placement" }));
    await waitFor(() => expect(screen.getByRole("button", { name: "Resample ground & update" })).toBeEnabled());
    fireEvent.click(screen.getByRole("button", { name: "Resample ground & update" }));
    await waitFor(() => expect(onPlacement).toHaveBeenCalledWith({ ...saved, elevation: 511,vertical_reference:{type:"ELLIPSOIDAL"},terrain_version_id:4 }));
    expect(api.post).toHaveBeenCalledWith(expect.stringContaining("ground-samples"), { longitude: 78, latitude: 13 });
    expect(api.put).toHaveBeenCalledWith(expect.stringContaining("placements/2"), expect.objectContaining({ elevation_offset: 2, heading_deg: 45 }));
  });

  it("shows failed sampling without moving the model", async () => {
    vi.mocked(api.get).mockImplementation(async (path) => path.endsWith("/evidence") ? evidence("VALID") : { placement: null });
    vi.mocked(api.post).mockResolvedValue({ id: 11, status: "OUTSIDE_COVERAGE", elevation: null, failure_reason: "Outside accepted survey coverage" });
    const onPlacement = vi.fn();
    render(<EngineeringEvidencePanel projectId={5} revisionId={2} origin={origin} onPlacement={onPlacement} />);
    fireEvent(window, new Event("geoai:open-site-data"));
    fireEvent.click(screen.getByRole("tab", { name: "Placement" }));
    await waitFor(() => expect(screen.getByRole("button", { name: "Place model on ground" })).toBeEnabled());
    fireEvent.click(screen.getByRole("button", { name: "Place model on ground" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Outside accepted survey coverage");
    expect(onPlacement).not.toHaveBeenCalled();
    expect(api.put).not.toHaveBeenCalled();
  });
});

function scene() {
  const viewer = { isDestroyed: () => false, clock: { currentTime: "", shouldAnimate: false, multiplier: 1 }, scene: { globe: {}, verticalExaggeration: 2, requestRender: vi.fn() }, shadowMap: {} };
  const Cesium = { JulianDate: { fromIso8601: (value: string) => value, toIso8601: () => "2026-10-03T09:30:00.000Z" }, ClockStep: { SYSTEM_CLOCK_MULTIPLIER: 1 }, ShadowMode: { DISABLED: 0, ENABLED: 1 }, Simon1994PlanetaryPositions: { computeSunPositionInEarthInertialFrame: () => ({}) }, Transforms: { computeIcrfToCentralBodyFixedMatrix: () => undefined } };
  return { viewer, Cesium };
}
describe("scene and sunlight panel", () => {
  it("enables lighting and shadows with the sun preset without resetting terrain scale", () => {
    const { viewer, Cesium } = scene();
    render(<SunStudyControls viewer={viewer as unknown as import("cesium").Viewer} Cesium={Cesium as unknown as typeof import("cesium")} longitude={77} latitude={12} buildingsAvailable terrainAvailable />);
    fireEvent.click(screen.getByRole("button", { name: "Scene / Sun study" }));
    fireEvent.click(screen.getByRole("button", { name: /Sun study.*Track/ }));
    expect(viewer.scene.globe).toMatchObject({ enableLighting: true });
    expect(viewer).toMatchObject({ shadows: true });
    expect(viewer.scene.verticalExaggeration).toBe(2);
    fireEvent.click(screen.getByRole("button", { name: "Play day" }));
    expect(viewer.clock.shouldAnimate).toBe(true);
    fireEvent.click(screen.getByRole("button", { name: "Pause" }));
    expect(viewer.clock.shouldAnimate).toBe(false);
    expect(viewer.clock.currentTime).toBe("2026-10-03T09:30:00.000Z");
  });

  it("makes loading failures visible on the Scene tab and supports retry", async () => {
    vi.mocked(api.get).mockRejectedValueOnce(new Error("Connection lost")).mockResolvedValue({ preferences: null });
    const { viewer, Cesium } = scene();
    render(<SunStudyControls viewer={viewer as unknown as import("cesium").Viewer} Cesium={Cesium as unknown as typeof import("cesium")} longitude={77} latitude={12} projectId={5} buildingsAvailable terrainAvailable />);
    fireEvent.click(screen.getByRole("button", { name: "Scene / Sun study" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Connection lost");
    fireEvent.click(screen.getByRole("button", { name: "Retry settings" }));
    await waitFor(() => expect(screen.getByRole("status")).toHaveTextContent("Project settings loaded"));
  });
});


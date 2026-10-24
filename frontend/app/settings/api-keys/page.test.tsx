import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
vi.mock("@/lib/api", () => ({ api: { get: vi.fn() } }));
import { api } from "@/lib/api";
import ProviderStatusPage from "./page";
afterEach(() => { cleanup(); vi.clearAllMocks(); });

it("offers guarded retry after failed provider reads and keeps unknown status explicit", async () => {
  vi.mocked(api.get).mockRejectedValue(new Error("Offline"));
  render(<ProviderStatusPage />);
  expect(await screen.findByRole("alert")).toHaveTextContent("could not be loaded");
  const retry = screen.getByRole("button", { name: "Retry provider status" });
  let finish!: (value: unknown) => void;
  vi.mocked(api.get).mockImplementation(() => new Promise(resolve => { finish = resolve; }));
  fireEvent.click(retry); fireEvent.click(retry);
  expect(api.get).toHaveBeenCalledTimes(4);
  expect(retry).toBeDisabled();
  // Two independent reads remain in flight; unmount must ignore late results.
  cleanup(); finish(null);
  await waitFor(() => expect(screen.queryByRole("alert")).not.toBeInTheDocument());
});

it("replaces the error with authoritative provider status after a successful retry", async () => {
  vi.mocked(api.get).mockRejectedValue(new Error("Offline"));
  render(<ProviderStatusPage />);
  const retry = await screen.findByRole("button", { name: "Retry provider status" });
  vi.mocked(api.get).mockImplementation(async path => path.includes("tile-providers")
    ? { cesium_ion_available: true, google_3d_tiles_available: false, mapbox_available: false, satellite_config: { provider: "esri" }, terrain_config: { max_zoom: 17 } }
    : { database_mode_label: "Local database", postgis_available: false, job_store: "in_memory", storage_mode: "local", redis_available: false, ai: { active_provider: "mock", mock_mode: true } });
  fireEvent.click(retry);
  expect(await screen.findByText("Local database")).toBeInTheDocument();
  expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  expect(screen.queryByRole("button", { name: "Retry provider status" })).not.toBeInTheDocument();
});

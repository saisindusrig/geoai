import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { api } from "@/lib/api";
import EmptyProjectStarter from "./EmptyProjectStarter";

vi.mock("@/lib/api", () => ({ api: { get: vi.fn() } }));
afterEach(() => { cleanup(); vi.resetAllMocks(); });
it("offers optional actions for an empty project without blocking the workspace", async () => {
  vi.mocked(api.get).mockResolvedValue({ isEmpty: true });
  const ask=vi.fn(),draw=vi.fn();window.addEventListener("geoai:open-copilot",ask);window.addEventListener("geoai:open-drawing",draw);
  render(<EmptyProjectStarter projectId={1} active hasSite={false}><p>Existing model tools</p></EmptyProjectStarter>);
  expect(await screen.findByText("Start anywhere.")).toBeInTheDocument();
  expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole("button",{name:"Ask GeoAI"}));fireEvent.click(screen.getByRole("button",{name:"Draw / select site"}));
  expect(ask).toHaveBeenCalledTimes(1);expect(draw).toHaveBeenCalledTimes(1);
  window.removeEventListener("geoai:open-copilot",ask);window.removeEventListener("geoai:open-drawing",draw);
});
it("preserves populated workspace content", async () => {
  vi.mocked(api.get).mockResolvedValue({ isEmpty:false });
  render(<EmptyProjectStarter projectId={1} active hasSite={false}><p>Existing model tools</p></EmptyProjectStarter>);
  await waitFor(()=>expect(api.get).toHaveBeenCalled());
  expect(screen.getByText("Existing model tools")).toBeInTheDocument();expect(screen.queryByText("Start anywhere.")).not.toBeInTheDocument();
});
it("disappears immediately after site data is saved", async () => {
  vi.mocked(api.get).mockResolvedValue({isEmpty:true});
  const view=render(<EmptyProjectStarter projectId={1} active hasSite={false}><p>Existing tools</p></EmptyProjectStarter>);
  await screen.findByText("Start anywhere.");
  view.rerender(<EmptyProjectStarter projectId={1} active hasSite><p>Existing tools</p></EmptyProjectStarter>);
  expect(screen.queryByText("Start anywhere.")).not.toBeInTheDocument();expect(screen.getByText("Existing tools")).toBeInTheDocument();
});

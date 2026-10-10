import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { api } from "@/lib/api";
import EmptyProjectStarter from "./EmptyProjectStarter";

vi.mock("@/lib/api", () => ({ api: { get: vi.fn() } }));
afterEach(() => { cleanup(); vi.resetAllMocks(); });
it.each([["Ask GeoAI", "geoai:open-copilot"], ["Draw / select site", "geoai:open-drawing"]])("opens %s without blocking the workspace", async (label, event) => {
  vi.mocked(api.get).mockResolvedValue({ isEmpty: true });
  const action=vi.fn();window.addEventListener(event,action);
  render(<EmptyProjectStarter projectId={1} active hasSite={false}><p>Existing model tools</p></EmptyProjectStarter>);
  expect(await screen.findByText("Start anywhere.")).toBeInTheDocument();
  expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  expect(screen.getByText("Existing model tools")).toBeInTheDocument();
  fireEvent.click(screen.getByRole("button",{name:label}));
  expect(action).toHaveBeenCalledTimes(1);
  expect(screen.queryByRole("region", { name: "Empty project starter" })).not.toBeInTheDocument();
  window.removeEventListener(event,action);
});

it("hides first-run actions while a map tool is active and allows dismissal", async () => {
  vi.mocked(api.get).mockResolvedValue({isEmpty:true});
  const view=render(<EmptyProjectStarter projectId={1} active hasSite={false}><p>Existing tools</p></EmptyProjectStarter>);
  await screen.findByText("Start anywhere.");
  view.rerender(<EmptyProjectStarter projectId={1} active={false} hasSite={false}><p>Existing tools</p></EmptyProjectStarter>);
  expect(screen.queryByText("Start anywhere.")).not.toBeInTheDocument();
  view.rerender(<EmptyProjectStarter projectId={1} active hasSite={false}><p>Existing tools</p></EmptyProjectStarter>);
  await screen.findByText("Start anywhere.");
  fireEvent.click(screen.getByRole("button", {name:"Dismiss first-run actions"}));
  expect(screen.queryByText("Start anywhere.")).not.toBeInTheDocument();
  expect(screen.getByText("Existing tools")).toBeInTheDocument();
});

it("does not reuse an empty result for another project", async () => {
  vi.mocked(api.get).mockResolvedValueOnce({isEmpty:true}).mockImplementationOnce(() => new Promise(() => {}));
  const view=render(<EmptyProjectStarter projectId={1} active hasSite={false}>{null}</EmptyProjectStarter>);
  await screen.findByText("Start anywhere.");
  view.rerender(<EmptyProjectStarter projectId={2} active hasSite={false}>{null}</EmptyProjectStarter>);
  expect(screen.queryByText("Start anywhere.")).not.toBeInTheDocument();
});

it("keeps tools available if eligibility cannot be loaded", async () => {
  vi.mocked(api.get).mockRejectedValue(new Error("Unavailable"));
  render(<EmptyProjectStarter projectId={1} active hasSite={false}><p>Existing tools</p></EmptyProjectStarter>);
  await waitFor(()=>expect(api.get).toHaveBeenCalled());
  expect(screen.queryByText("Start anywhere.")).not.toBeInTheDocument();
  expect(screen.getByText("Existing tools")).toBeInTheDocument();
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

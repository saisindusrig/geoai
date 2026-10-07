import React from "react";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import BuildingAssistant from "./BuildingAssistant";
import { api } from "@/lib/api";

vi.mock("@/lib/api", () => ({ api: { get: vi.fn(), post: vi.fn() }, formatApiErrorMessage: (e: Error) => e.message }));
const proposal = {
  id: 1, prompt: "Build a house", base_revision_id: null, job_id: null, stale: false,
  model: "test-model", elevation_known: false,
  spec: { summary: "A two-room house", floors: 1, floor_height: 3,
    footprint: { x: 0, y: 0, width: 10, depth: 8 },
    rooms: [{ id: "living", name: "Living", floor: 0, x: 0, y: 0, width: 5, depth: 8 }],
    walls: [], openings: [], columns: [], beams: [], slab_thickness: .15,
    foundation_width: 1, foundation_depth: 1, assumptions: ["Concept only"] },
};
const props = { projectId: 801, boundaryKey: "polygon", revisionId: null, dirty: false, generating: false, onStarted: vi.fn(), onClose: vi.fn() };
beforeEach(() => { vi.resetAllMocks(); vi.mocked(api.get).mockResolvedValue({ plans: [] }); props.onStarted.mockResolvedValue(undefined); });
afterEach(cleanup);

it("requires a saved boundary and saved model edits", async () => {
  const view = render(<BuildingAssistant {...props} boundaryKey="null" />);
  await waitFor(() => expect(screen.queryByText("Loading saved plans…")).not.toBeInTheDocument());
  fireEvent.change(screen.getByLabelText("Describe your building"), { target: { value: "Build a house" } });
  expect(screen.getByRole("button", { name: "Create plan" })).toBeDisabled();
  view.rerender(<BuildingAssistant {...props} dirty />);
  expect(screen.getByText(/Save your model edits/)).toBeInTheDocument();
  expect(api.post).not.toHaveBeenCalled();
});

it("reviews and revises a plan before explicitly approving generation", async () => {
  vi.mocked(api.post).mockResolvedValueOnce(proposal).mockResolvedValueOnce({ ...proposal, id: 2 }).mockResolvedValueOnce({ job_id: "job-1", scenario_id: 20 });
  render(<BuildingAssistant {...props} />);
  await waitFor(() => expect(screen.queryByText("Loading saved plans…")).not.toBeInTheDocument());
  fireEvent.change(screen.getByLabelText("Describe your building"), { target: { value: "Build a house" } });
  fireEvent.click(screen.getByRole("button", { name: "Create plan" }));
  await screen.findByText("Review plan 1");
  expect(api.post).toHaveBeenCalledTimes(1);
  expect(props.onStarted).not.toHaveBeenCalled();
  fireEvent.change(screen.getByRole("textbox"), { target: { value: "Make the kitchen larger" } });
  expect(screen.getByRole("button", { name: "Approve and build" })).toBeDisabled();
  fireEvent.click(screen.getByRole("button", { name: "Request changes" }));
  await screen.findByText("Review plan 2");
  expect(api.post).toHaveBeenNthCalledWith(2, "/api/projects/801/ai/building-plans/1/revisions", { prompt: "Make the kitchen larger", base_revision_id: null });
  fireEvent.click(screen.getByRole("button", { name: "Approve and build" }));
  await waitFor(() => expect(props.onStarted).toHaveBeenCalledWith("job-1", 20));
  expect(api.post).toHaveBeenLastCalledWith("/api/projects/801/ai/building-plans/2/build", { approve: true });
  expect(screen.getByRole("button", { name: "Build submitted" })).toBeDisabled();
});

it("restores saved plans and blocks stale approval", async () => {
  vi.mocked(api.get).mockResolvedValue({ plans: [{ ...proposal, stale: true }] });
  render(<BuildingAssistant {...props} />);
  await screen.findByText("Review plan 1");
  expect(screen.getByRole("button", { name: "Approve and build" })).toBeDisabled();
  expect(screen.getByText(/plot or saved model changed/)).toBeInTheDocument();
});

it("shows provider errors without generating a model", async () => {
  vi.mocked(api.post).mockRejectedValue(new Error("Nebius timed out"));
  render(<BuildingAssistant {...props} />);
  await waitFor(() => expect(screen.queryByText("Loading saved plans…")).not.toBeInTheDocument());
  fireEvent.change(screen.getByRole("textbox"), { target: { value: "Build a house" } });
  fireEvent.click(screen.getByRole("button", { name: "Create plan" }));
  expect(await screen.findByRole("alert")).toHaveTextContent("Nebius timed out");
  expect(props.onStarted).not.toHaveBeenCalled();
});

import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import PersistentAssistant from "./PersistentAssistant";
import { api } from "@/lib/api";

vi.mock("@/lib/api", () => ({ api: { get: vi.fn(), post: vi.fn() } }));
const props = { projectId: 1, selectedIds: ["pier-a"], revisionId: 7, dirty: false };
let messages: object[];
let items: object[];
let failSend: boolean;
let postBodies: unknown[];
let messagePostGate: Promise<void> | undefined;
afterEach(cleanup);

beforeEach(() => {
  vi.resetAllMocks(); messages = []; items = []; failSend = false; postBodies = []; messagePostGate = undefined;
  vi.mocked(api.get).mockImplementation(async path => {
    if (path.endsWith("/conversations")) return { conversations: [{ id: "c1", title: "Project discussion" }] };
    if (path.includes("/messages")) return { messages, nextBefore: null };
    if (path.endsWith("/memory")) return { items };
    if (path.endsWith("/site-profiles")) return { profiles: [{ id: "p1" }] };
    if (path.endsWith("/readiness")) return { siteDataState: "UNCONFIGURED", databaseMode: "DEMO", current: true, operations: [] };
    return { id: "p1", current: true, refreshState: "IDLE", version: { id: "pv1", version: 2, selectionVersion: { id: "sv1" }, relief: { minElevation: { sourceKind: "UNKNOWN", value: null } } } };
  });
  vi.mocked(api.post).mockImplementation(async (path, body) => {
    if (path.endsWith("/messages")) {
      postBodies.push(body);
      if (failSend) throw new Error("Network unavailable");
      await messagePostGate;
      const sent = body as { parts: object[]; context: { selectedObjectIds: string[]; modelRevisionId: string } };
      messages = [{ id: "m1", role: "USER", parts: sent.parts, context: { ...sent.context, selection: sent.context.selectedObjectIds.map(objectId => ({ objectId })) }, run: { status: "WAITING_FOR_INPUT", errorCode: "ORCHESTRATION_NOT_ENABLED" } }];
      return { messageId: "m1", runId: "r1" };
    }
    if (path.endsWith("/accept") || path.endsWith("/reject")) {
      items = items.map(item => ({ ...item, status: path.endsWith("/accept") ? "ACCEPTED" : "REJECTED" }));
    }
    return {};
  });
});

async function ready() {
  await screen.findByText("Site profile v2 · Current");
  await waitFor(() => expect(screen.getByRole("button", { name: "Refresh site" })).toBeEnabled());
}

describe("persistent project Assistant", () => {
  it("keeps the saved selection/profile pair without creating a selection on send", async () => {
    const geometry = { type: "Polygon" as const, coordinates: [[[77,12],[77.002,12],[77.002,12.001],[77,12]]] };
    const originalGet = vi.mocked(api.get).getMockImplementation()!;
    // Object key order is not geometric identity; coordinates and type are.
    vi.mocked(api.get).mockImplementation(async path => path.includes("/site-selections/") ? { id: "sv1", canonicalGeometry: { coordinates: geometry.coordinates, type: geometry.type } } : originalGet(path));
    render(<PersistentAssistant {...props} siteGeometry={geometry} />); await ready();
    fireEvent.change(screen.getByRole("textbox", { name: "Project message" }), { target: { value: "Create a 5 m x 3 m industrial maintenance platform" } });
    fireEvent.click(screen.getByRole("button", { name: "Send message" }));
    await screen.findByRole("article");
    expect(api.post).toHaveBeenCalledTimes(1);
    expect(postBodies[0]).toMatchObject({ context: { siteSelectionVersionId: "sv1", siteProfileVersionId: "pv1" } });
  });

  it("blocks changed geometry and explains refreshing the saved site", async () => {
    const originalGet = vi.mocked(api.get).getMockImplementation()!;
    vi.mocked(api.get).mockImplementation(async path => path.includes("/site-selections/") ? { id: "sv1", canonicalGeometry: { type: "Point", coordinates: [77,12] } } : originalGet(path));
    render(<PersistentAssistant {...props} siteGeometry={{ type: "Point", coordinates: [78,12] }} />); await ready();
    fireEvent.change(screen.getByRole("textbox", { name: "Project message" }), { target: { value: "Create a platform" } });
    fireEvent.click(screen.getByRole("button", { name: "Send message" }));
    await screen.findByText("Site changed. Save the boundary and Refresh site before sending a new request.");
    expect(api.post).not.toHaveBeenCalled();
  });

  it("labels the opt-in offline template and supplies the example", async () => {
    const originalGet = vi.mocked(api.get).getMockImplementation()!;
    vi.mocked(api.get).mockImplementation(async path => path.endsWith("/assistant/offline-platform") ? { enabled: true, label: "Offline demo · supported platform template", example: "Create a 5 m × 3 m industrial maintenance platform" } : originalGet(path));
    render(<PersistentAssistant {...props} />); await ready();
    expect(screen.getByText("Offline demo · supported platform template")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Use platform example" }));
    expect(screen.getByRole("textbox", { name: "Project message" })).toHaveValue("Create a 5 m × 3 m industrial maintenance platform");
    expect(api.post).not.toHaveBeenCalled();
  });
  it("requires a fresh message for stale model context instead of retrying", async () => {
    messages = [{ id: "m", role: "USER", context: { selection: [], modelRevisionId: "6" }, parts: [{ kind: "TEXT", text: "Create a walkway" }],
      run: { id: "r", status: "FAILED", errorCode: "CONTEXT_REFRESH_REQUIRED" } }];
    render(<PersistentAssistant {...props} />); await ready();
    expect(screen.getByRole("alert")).toHaveTextContent("Refresh your selection and send a new message");
    expect(screen.queryByRole("button", { name: "Retry assistant" })).not.toBeInTheDocument();
    expect(api.post).not.toHaveBeenCalled();
  });
  it("loads an assistant reply and clarification after reload", async () => {
    messages = [{ id: "reply", role: "ASSISTANT", context: { selection: [] }, parts: [{ kind: "TEXT", text: "I can help plan a retaining wall concept." }, { kind: "QUESTION", questionId: "q", text: "Which side is retained?", options: ["East side"] }], run: null }];
    const view = render(<PersistentAssistant {...props} />); await ready();
    fireEvent.click(screen.getByRole("button", { name: "East side" }));
    expect(screen.getByRole("textbox", { name: "Project message" })).toHaveValue("East side");
    view.unmount(); render(<PersistentAssistant {...props} />);
    expect(await screen.findByText("I can help plan a retaining wall concept.")).toBeInTheDocument();
    expect(api.post).not.toHaveBeenCalled();
  });

  it("retries the persisted run and displays capability limitations", async () => {
    messages = [{ id: "m", role: "USER", context: { selection: [{ objectId: "old-pier" }], modelRevisionId: "6" }, parts: [{ kind: "TEXT", text: "Raise this pier" }],
      run: { id: "r", status: "FAILED", errorCode: "TIMEOUT", capabilities: [{ assetType: "BRIDGE", discussionSupport: "FULL", planningSupport: "CONCEPT_ONLY", generationSupport: "UNSUPPORTED", engineeringAnalysisSupport: "UNSUPPORTED" }] } }];
    render(<PersistentAssistant {...props} />); await ready();
    expect(screen.getByText(/generation unsupported/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Retry assistant" }));
    await waitFor(() => expect(api.post).toHaveBeenCalledWith("/api/projects/1/assistant/runs/r/retry", { clientRequestId: expect.any(String) }));
    expect(screen.getByText("Captured: old-pier · revision 6")).toBeInTheDocument();
  });
  it("persists a message and reloads it from the server", async () => {
    let releasePost!: () => void;
    messagePostGate = new Promise<void>(resolve => { releasePost = resolve; });
    const view = render(<PersistentAssistant {...props} />); await ready();
    fireEvent.change(screen.getByRole("textbox", { name: "Project message" }), { target: { value: "Could the road move west?" } });
    fireEvent.click(screen.getByRole("button", { name: "Send message" }));
    // The draft already contains this text; it must not count as persistence.
    expect(await screen.findByText("Could the road move west?")).toBe(screen.getByRole("textbox", { name: "Project message" }));
    expect(screen.getByRole("button", { name: "Saving…" })).toBeDisabled();
    expect(screen.queryByRole("article")).not.toBeInTheDocument();
    releasePost();
    const savedArticle = await screen.findByRole("article");
    expect(within(savedArticle).getByText("Could the road move west?")).toBeInTheDocument();
    expect(await within(savedArticle).findByText("Saved before AI processing was enabled")).toBeInTheDocument();
    view.unmount(); render(<PersistentAssistant {...props} />);
    const reloadedArticle = await screen.findByRole("article");
    expect(within(reloadedArticle).getByText("Could the road move west?")).toBeInTheDocument();
    expect(await within(reloadedArticle).findByText("Saved before AI processing was enabled")).toBeInTheDocument();
    expect(api.post).toHaveBeenCalledTimes(1);
    expect(api.post).not.toHaveBeenCalledWith(expect.stringContaining("/ai/chat"), expect.anything());
  });

  it("shows current selection and unknown site readiness without claiming zero elevation", async () => {
    render(<PersistentAssistant {...props} dirty />); await ready();
    expect(screen.getByLabelText("Selected object context")).toHaveTextContent("Selected: pier-a · revision 7 · unsaved edits");
    expect(screen.getByLabelText("Site readiness")).toHaveTextContent("UNCONFIGURED · Demo storage");
    expect(screen.getByText("Elevation: Unknown")).toBeInTheDocument();
  });

  it("retries exactly the original message context after selection changes", async () => {
    failSend = true;
    const view = render(<PersistentAssistant {...props} />); await ready();
    fireEvent.change(screen.getByRole("textbox", { name: "Project message" }), { target: { value: "Discuss this pier" } });
    fireEvent.click(screen.getByRole("button", { name: "Send message" }));
    await screen.findByText("Network unavailable");
    view.rerender(<PersistentAssistant {...props} selectedIds={["pier-b"]} revisionId={8} />);
    failSend = false; fireEvent.click(screen.getByRole("button", { name: "Retry" }));
    await screen.findByText("Discuss this pier");
    expect(postBodies[1]).toEqual(postBodies[0]);
    expect(screen.getByText("Captured: pier-a · revision 7")).toBeInTheDocument();
  });

  it.each(["Accept", "Reject"])("requires the explicit %s action for proposed memory", async action => {
    items = [{ id: "requirement", versionId: "v1", version: 1, status: "PROPOSED", assetId: null,
      content: { kind: "REQUIREMENT", key: "width", constraint: { operator: "EQ", value: 7, unit: "m" } } }];
    render(<PersistentAssistant {...props} />); await ready();
    const card = screen.getByRole("article", { name: "proposed memory" });
    expect(api.post).not.toHaveBeenCalled();
    fireEvent.click(within(card).getByRole("button", { name: action }));
    await waitFor(() => expect(api.post).toHaveBeenCalledWith(`/api/projects/1/memory/requirement/versions/1/${action.toLowerCase()}`, { expectedStatus: "PROPOSED" }));
  });

  it("offers a retry when loading conversation history fails", async () => {
    vi.mocked(api.get).mockRejectedValueOnce(new Error("History unavailable"));
    render(<PersistentAssistant {...props} />);
    await screen.findByText("History unavailable");
    fireEvent.click(screen.getByRole("button", { name: "Retry" }));
    await ready();
    expect(screen.queryByText("History unavailable")).not.toBeInTheDocument();
  });
});

import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";

vi.mock("next/navigation", () => ({ useParams: () => ({ id: "805" }) }));
vi.mock("next/link", () => ({ default: ({ children }: { children: React.ReactNode }) => <span>{children}</span> }));
vi.mock("@/components/project-results/ProjectResultShell", () => ({ default: ({ children }: { children: React.ReactNode }) => <div>{children}</div> }));
vi.mock("@/hooks/useProjectData", () => ({ useProjectData: vi.fn() }));
vi.mock("@/lib/api", () => ({ api: { getOptional: vi.fn(), post: vi.fn() }, apiUrl: (path: string) => path }));
import { useProjectData } from "@/hooks/useProjectData";
import { api } from "@/lib/api";
import TimelinePage from "./[id]/timeline/page";
import EstimatePage from "./[id]/estimate/page";
import ScenarioPage from "./[id]/scenarios/page";

beforeEach(() => {
  vi.mocked(useProjectData).mockReturnValue({ project: { id: 805, name: "Review" }, design: {}, scenarios: [], scenarioSummaries: [], loading: false, error: null, load: vi.fn(), summaryStats: {}, selectScenario: vi.fn() } as unknown as ReturnType<typeof useProjectData>);
  vi.mocked(api.getOptional).mockResolvedValue(null);
});
afterEach(() => { cleanup(); vi.clearAllMocks(); });

it("renders incomplete timeline evidence without crashing or implying approval", () => {
  render(<TimelinePage />);
  expect(screen.getByRole("heading", { name: "Construction Timeline" })).toBeInTheDocument();
  expect(screen.getByRole("status")).toHaveTextContent("permissions and surveys have not been supplied");
  expect(screen.queryByText("Gantt preview")).not.toBeInTheDocument();
});

it("replaces BOQ loading with a meaningful empty state", async () => {
  render(<EstimatePage />);
  expect(await screen.findByText("No BOQ available yet")).toBeInTheDocument();
  expect(screen.queryByText("Loading BOQ…")).not.toBeInTheDocument();
});

it("offers retry after a BOQ fetch fails", async () => {
  vi.mocked(api.getOptional).mockRejectedValueOnce(new Error("Offline"));
  render(<EstimatePage />);
  await screen.findByText("Offline");
  fireEvent.click(screen.getByRole("button", { name: "Retry BOQ" }));
  expect(await screen.findByText(/This scenario has no saved quantity estimate/)).toBeInTheDocument();
  expect(api.getOptional).toHaveBeenCalledTimes(2);
});

it("announces comparison failure and retains scenario selections", async () => {
  vi.mocked(useProjectData).mockReturnValue({ project: { id: 805, name: "Review" }, scenarioSummaries: [1, 2].map(id => ({ scenario_id: id, name: `Option ${id}`, status: "completed" })), loading: false, error: null, load: vi.fn(), summaryStats: {}, selectScenario: vi.fn() } as unknown as ReturnType<typeof useProjectData>);
  vi.mocked(api.post).mockRejectedValue(new Error("Connection lost"));
  render(<ScenarioPage />);
  for (const checkbox of screen.getAllByRole("checkbox")) fireEvent.click(checkbox);
  fireEvent.click(screen.getByRole("button", { name: /Compare/ }));
  expect(await screen.findByRole("alert")).toHaveTextContent("Connection lost");
  await waitFor(() => expect(screen.getByRole("button", { name: /Compare/ })).toBeEnabled());
  for (const checkbox of screen.getAllByRole("checkbox")) expect(checkbox).toBeChecked();
});

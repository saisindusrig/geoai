import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
vi.mock("next/navigation", () => ({ useParams: () => ({ id: "999998" }) }));
vi.mock("next/link", () => ({ default: ({ children }: { children: React.ReactNode }) => <span>{children}</span> }));
vi.mock("@/components/project-results/ProjectResultShell", () => ({ default: ({ children }: { children: React.ReactNode }) => <div>{children}</div> }));
vi.mock("@/components/project/ProjectValidationPanel", () => ({ default: () => null }));
vi.mock("@/hooks/useWorkspaceDevice", () => ({ useWorkspaceDevice: () => "desktop" }));
vi.mock("@/hooks/useProjectData", () => ({ useProjectData: () => ({ project: { id: 999998 }, design: { summary: "Fixture", risks: [] }, scenario: { id: 1, assumptions_json: ["Original"] }, summaryStats: {}, load: vi.fn() }) }));
vi.mock("@/lib/api", () => ({ api: { getOptional: vi.fn().mockResolvedValue(null), put: vi.fn() }, apiUrl: (path: string) => path }));
vi.mock("@/lib/toast", () => ({ toast: vi.fn() }));
import { api } from "@/lib/api";
import { toast } from "@/lib/toast";
import Report from "./page";
afterEach(() => { cleanup(); vi.clearAllMocks(); });

it("guards concurrent assumption saves and retains the failed draft for retry", async () => {
  let reject!: (reason: Error) => void;
  vi.mocked(api.put).mockImplementationOnce(() => new Promise((_, no) => { reject = no; }));
  render(<Report />);
  fireEvent.click(screen.getByRole("button", { name: "Edit" }));
  fireEvent.change(screen.getByLabelText("Assumption 1"), { target: { value: "Retained draft" } });
  fireEvent.click(screen.getByRole("button", { name: "Save" }));
  fireEvent.click(screen.getByRole("button", { name: "Saving…" }));
  expect(api.put).toHaveBeenCalledTimes(1);
  reject(new Error("Offline"));
  await waitFor(() => expect(screen.getByRole("button", { name: "Save" })).toBeEnabled());
  expect(screen.getByLabelText("Assumption 1")).toHaveValue("Retained draft");
  expect(toast).toHaveBeenCalledWith("Offline", { variant: "error" });
  vi.mocked(api.put).mockResolvedValueOnce({});
  fireEvent.click(screen.getByRole("button", { name: "Save" }));
  await waitFor(() => expect(screen.getByRole("button", { name: "Edit" })).toBeEnabled());
  expect(api.put).toHaveBeenCalledTimes(2);
});


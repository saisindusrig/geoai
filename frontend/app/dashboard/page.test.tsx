import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const { push, redirect } = vi.hoisted(() => ({ push: vi.fn(), redirect: vi.fn() }));
vi.mock("next/navigation", () => ({ useRouter: () => ({ push }), redirect }));
vi.mock("next/link", () => ({ default: ({ href, children, ...rest }: { href: string; children: React.ReactNode }) => <a href={href} {...rest}>{children}</a> }));
vi.mock("@/components/dashboard/ConstructionPreview", () => ({ default: () => <div /> }));
vi.mock("@/lib/api", () => ({ api: { get: vi.fn(), post: vi.fn(), put: vi.fn(), delete: vi.fn() }, authRequired: () => false, getAuthToken: () => null, ApiError: class extends Error {} }));
import DashboardPage from "@/app/dashboard/page";
import NewProjectPage from "@/app/projects/new/page";
import { api } from "@/lib/api";

afterEach(() => { cleanup(); vi.clearAllMocks(); window.history.replaceState({}, "", "/dashboard"); });
beforeEach(() => { vi.mocked(api.get).mockResolvedValue([]); vi.mocked(api.post).mockResolvedValue({ id: 42 }); });
async function openDialog() {
  render(<DashboardPage />);
  await screen.findByText("No projects yet");
  const trigger = screen.getAllByRole("button", { name: "New Project" })[0];
  await userEvent.click(trigger);
  return { trigger, dialog: screen.getByRole("dialog", { name: "New project" }) };
}

it("validates and trims folder names and prevents duplicate folder requests", async () => {
  let resolve!: (value: unknown) => void;
  vi.mocked(api.post).mockImplementation(() => new Promise(r => { resolve = r; }));
  render(<DashboardPage />);
  await screen.findByText("No projects yet");
  await userEvent.click(screen.getByRole("button", { name: "New folder" }));
  const dialog = screen.getByRole("dialog", { name: "Create folder" });
  const input = within(dialog).getByRole("textbox", { name: "Folder name" });
  fireEvent.change(input, { target: { value: "   " } });
  fireEvent.submit(input.closest("form")!);
  expect(api.post).not.toHaveBeenCalled();
  fireEvent.change(input, { target: { value: "  Planning  " } });
  fireEvent.submit(input.closest("form")!); fireEvent.submit(input.closest("form")!);
  expect(api.post).toHaveBeenCalledTimes(1);
  expect(api.post).toHaveBeenCalledWith("/api/project-folders", { name: "Planning" });
  expect(within(dialog).getByRole("button", { name: "Close folder dialog" })).toBeDisabled();
  resolve({ id: 7, name: "Planning" });
  await waitFor(() => expect(screen.queryByRole("dialog")).not.toBeInTheDocument());
});

it("restores focus to the folder trigger when Escape closes the dialog", async () => {
  render(<DashboardPage />); await screen.findByText("No projects yet");
  const trigger = screen.getByRole("button", { name: "New folder" });
  await userEvent.click(trigger); await userEvent.keyboard("{Escape}");
  expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  expect(trigger).toHaveFocus();
});
describe("name-only project entry", () => {
  it("opens a compact dialog with only a project name", async () => {
    const { dialog } = await openDialog();
    expect(within(dialog).getAllByRole("textbox")).toHaveLength(1);
    expect(within(dialog).getByRole("textbox", { name: "Project name" })).toHaveFocus();
    expect(within(dialog).queryByRole("combobox")).not.toBeInTheDocument();
    expect(screen.queryByText("Infrastructure templates")).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /More assets/i })).not.toBeInTheDocument();
    expect(within(dialog).getByRole("button", { name: "Create Project" })).toBeDisabled();
  });
  it("trims the name and Enter opens the workspace directly", async () => {
    const { dialog } = await openDialog();
    await userEvent.type(within(dialog).getByRole("textbox"), "  River junction  {Enter}");
    await waitFor(() => expect(push).toHaveBeenCalledWith("/projects/42/workspace"));
    expect(api.post).toHaveBeenCalledWith("/api/projects", { name: "River junction" });
    expect(api.post).toHaveBeenCalledTimes(1);
  });
  it("requires a non-whitespace name and keeps the length limit", async () => {
    const { dialog } = await openDialog();
    const input = within(dialog).getByRole("textbox");
    expect(input).toHaveAttribute("maxlength", "255");
    await userEvent.type(input, "   ");
    expect(within(dialog).getByRole("button", { name: "Create Project" })).toBeDisabled();
    fireEvent.submit(dialog); expect(api.post).not.toHaveBeenCalled();
  });
  it("Escape closes and returns focus to the primary action", async () => {
    const { trigger } = await openDialog();
    await userEvent.keyboard("{Escape}");
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument(); expect(trigger).toHaveFocus();
  });
  it("keeps the project name focused when global search is requested inside the dialog", async () => {
    const { dialog } = await openDialog();
    await userEvent.keyboard("{Control>}k{/Control}");
    expect(within(dialog).getByRole("textbox", { name: "Project name" })).toHaveFocus();
  });
  it("Cancel closes without creating a project", async () => {
    const { dialog, trigger } = await openDialog();
    await userEvent.click(within(dialog).getByRole("button", { name: "Cancel" }));
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument(); expect(trigger).toHaveFocus(); expect(api.post).not.toHaveBeenCalled();
  });
  it("preserves entered name and displays failed requests in the dialog", async () => {
    vi.mocked(api.post).mockRejectedValueOnce(new Error("Backend unavailable"));
    const { dialog } = await openDialog();
    await userEvent.type(within(dialog).getByRole("textbox"), "Bridge study{Enter}");
    expect(await screen.findByRole("alert")).toHaveTextContent("Backend unavailable");
    expect(within(dialog).getByRole("textbox")).toHaveValue("Bridge study"); expect(push).not.toHaveBeenCalled();
  });
  it("prevents duplicate submissions while the API request is pending", async () => {
    let resolve!: (value: unknown) => void;
    vi.mocked(api.post).mockImplementation(() => new Promise(r => { resolve = r; }));
    const { dialog } = await openDialog();
    fireEvent.change(within(dialog).getByRole("textbox"), { target: { value: "Study" } });
    fireEvent.submit(dialog); fireEvent.submit(dialog);
    expect(api.post).toHaveBeenCalledTimes(1); expect(within(dialog).getByRole("button", { name: "Creating…" })).toBeDisabled();
    resolve({ id: 42 }); await waitFor(() => expect(push).toHaveBeenCalled());
  });
  it("keeps Tab within the dialog", async () => {
    const { dialog } = await openDialog();
    const input = within(dialog).getByRole("textbox");
    await userEvent.keyboard("{Shift>}{Tab}{/Shift}");
    expect(within(dialog).getByRole("button", { name: "Cancel" })).toHaveFocus();
    await userEvent.keyboard("{Tab}"); expect(input).toHaveFocus();
  });
  it("uses the same dialog for the compatibility creation URL", async () => {
    NewProjectPage(); expect(redirect).toHaveBeenCalledWith("/dashboard?newProject=1");
    window.history.replaceState({}, "", "/dashboard?newProject=1&template=bridge");
    render(<DashboardPage />);
    expect(await screen.findByRole("dialog", { name: "New project" })).toBeInTheDocument();
    expect(screen.queryByLabelText(/asset type/i)).not.toBeInTheDocument();
  });
});

describe("compact project dashboard", () => {
  const projects = [
    { id: 1, name: "Old road", project_type: "road", location_name: "Town", folder_id: null, updated_at: "2026-09-01T00:00:00Z" },
    { id: 2, name: "Latest study", project_type: "unclassified", location_name: "River", folder_id: 7, updated_at: "2026-10-01T00:00:00Z" },
  ];
  it("continues the latest project and preserves workspace links", async () => {
    vi.mocked(api.get).mockImplementation(async url => url === "/api/projects" ? projects : []);
    render(<DashboardPage />);
    const continued = within(screen.getByRole("region", { name: "Continue working" }));
    expect(await continued.findByText("Latest study")).toBeInTheDocument();
    expect(continued.getByRole("link", { name: "Open workspace" })).toHaveAttribute("href", "/projects/2/workspace");
    expect(screen.getByRole("heading", { name: "Recent projects" })).toBeInTheDocument();
  });
  it("preserves project search and folder filtering", async () => {
    vi.mocked(api.get).mockImplementation(async url => url === "/api/projects" ? projects : [{ id: 7, name: "Water studies" }]);
    render(<DashboardPage />);
    await screen.findByRole("button", { name: "Project options for Old road" });
    await userEvent.click(screen.getByRole("button", { name: "Water studies" }));
    expect(screen.queryByRole("button", { name: "Project options for Old road" })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Project options for Latest study" })).toBeInTheDocument();
    await userEvent.type(screen.getByRole("searchbox", { name: "Search projects" }), "missing-project");
    expect(screen.getByText("No matching projects")).toBeInTheDocument();
    await userEvent.click(within(screen.getByRole("navigation", { name: "Dashboard navigation" })).getByRole("button", { name: "Overview" }));
    expect(screen.getByRole("searchbox", { name: "Search projects" })).toHaveValue("");
    expect(screen.getByRole("button", { name: "Project options for Old road" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Project options for Latest study" })).toBeInTheDocument();
  });
  it("reports load errors without showing a false empty state", async () => {
    vi.mocked(api.get).mockRejectedValue(new Error("Offline")); render(<DashboardPage />);
    expect(await screen.findByText(/Saved projects are unavailable/)).toBeInTheDocument();
    expect(screen.queryByText("No projects yet")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "New Project" })).toBeInTheDocument();
  });
});

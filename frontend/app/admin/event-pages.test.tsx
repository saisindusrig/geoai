import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
vi.mock("@/lib/useAuthUser", () => ({ useAuthUser: () => ({ isAdmin: true, loading: false }) }));
vi.mock("next/link", () => ({ default: ({ children }: { children: React.ReactNode }) => <span>{children}</span> }));
vi.mock("@/lib/api", () => ({ api: { get: vi.fn() }, ApiError: class extends Error {} }));
import { api } from "@/lib/api";
import UsagePage from "./usage/page";
import AuditPage from "./audit/page";
afterEach(() => { cleanup(); vi.clearAllMocks(); });

for (const [name, Page] of [["usage", UsagePage], ["audit", AuditPage]] as const) {
  it(`${name}: distinguishes loading from empty and pages using the existing offset contract`, async () => {
    vi.mocked(api.get).mockResolvedValueOnce({ total: 201, limit: 100, offset: 0, entries: [] }).mockResolvedValueOnce({ total: 201, limit: 100, offset: 100, entries: [] });
    render(<Page />);
    expect(screen.queryByText(name === "usage" ? "No usage events recorded." : "No audit entries yet.")).not.toBeInTheDocument();
    const next = await screen.findByRole("button", { name: "Next" });
    fireEvent.click(next);
    expect(api.get).toHaveBeenLastCalledWith(`/api/admin/${name}?limit=100&offset=100`);
    expect(await screen.findByRole("button", { name: "Previous" })).toBeInTheDocument();
  });
}

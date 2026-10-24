import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
vi.mock("@/lib/useAuthUser", () => ({ useAuthUser: () => ({ isAdmin: true, loading: false }) }));
vi.mock("@/lib/api", () => ({ api: { get: vi.fn() } }));
import { api } from "@/lib/api";
import RatesPage from "./rates/page";
import TemplatesPage from "./templates/page";
afterEach(() => { cleanup(); vi.clearAllMocks(); });

for (const [name, Page] of [["rates", RatesPage], ["templates", TemplatesPage]] as const) {
  it(`${name}: exits loading on failure, retries, then reports a known empty list`, async () => {
    vi.mocked(api.get).mockRejectedValueOnce(new Error("Offline")).mockResolvedValueOnce([]);
    render(<Page />);
    expect(screen.getByRole("status")).toHaveTextContent(`Loading ${name}`);
    expect(await screen.findByRole("alert")).toHaveTextContent("Offline");
    expect(screen.queryByText(`No ${name} recorded yet.`)).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: `Retry ${name}` }));
    expect(await screen.findByText(`No ${name} recorded yet.`)).toBeInTheDocument();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });
}

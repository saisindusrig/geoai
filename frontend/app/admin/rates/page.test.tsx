import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
vi.mock("@/lib/useAuthUser", () => ({ useAuthUser: () => ({ isAdmin: true, loading: false }) }));
vi.mock("@/lib/api", () => ({ api: { get: vi.fn(), delete: vi.fn() } }));
import { api } from "@/lib/api";
import RatesPage from "./page";

afterEach(() => { cleanup(); vi.restoreAllMocks(); vi.clearAllMocks(); });
it("cancels deletion without sending a mutation", async () => {
  vi.mocked(api.get).mockResolvedValue([{ id: 1, item_name: "Concrete", rate: 100 }]);
  const confirm = vi.spyOn(window, "confirm").mockReturnValue(false);
  render(<RatesPage />);
  fireEvent.click(await screen.findByRole("button", { name: "Delete rate for Concrete" }));
  expect(confirm).toHaveBeenCalledWith(expect.stringContaining("Future cost estimates"));
  expect(api.delete).not.toHaveBeenCalled();
});
it("prevents duplicate deletion and restores controls on failure", async () => {
  vi.mocked(api.get).mockResolvedValue([{ id: 1, item_name: "Concrete", rate: 100 }]);
  vi.spyOn(window, "confirm").mockReturnValue(true);
  let reject!: (error: Error) => void;
  vi.mocked(api.delete).mockImplementation(() => new Promise((_resolve, fail) => { reject = fail; }));
  render(<RatesPage />);
  const button = await screen.findByRole("button", { name: "Delete rate for Concrete" });
  fireEvent.click(button); fireEvent.click(button);
  expect(api.delete).toHaveBeenCalledTimes(1);
  expect(button).toBeDisabled();
  reject(new Error("Offline"));
  expect(await screen.findByRole("alert")).toHaveTextContent("could not be deleted");
  await waitFor(() => expect(button).toBeEnabled());
});

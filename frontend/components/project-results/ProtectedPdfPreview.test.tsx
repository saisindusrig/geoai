import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
vi.mock("@/lib/api", () => ({ fetchBinary: vi.fn() }));
import { fetchBinary } from "@/lib/api";
import Preview from "./ProtectedPdfPreview";
afterEach(() => { cleanup(); vi.restoreAllMocks(); });
it("loads only a protected PDF Blob and releases it on unmount", async () => {
  vi.mocked(fetchBinary).mockResolvedValue(new Response("%PDF-fixture", { headers: { "Content-Type": "application/pdf" } }));
  URL.createObjectURL = vi.fn(() => "blob:protected-preview"); URL.revokeObjectURL = vi.fn();
  const view = render(<Preview path="/api/projects/1/exports/pdf" />);
  await waitFor(() => expect(screen.getByTitle("PDF preview")).toHaveAttribute("src", "blob:protected-preview"));
  view.unmount(); expect(URL.revokeObjectURL).toHaveBeenCalledWith("blob:protected-preview");
});
it("rejects an HTML/login response instead of embedding it as a PDF", async () => {
  vi.mocked(fetchBinary).mockResolvedValue(new Response("login", { headers: { "Content-Type": "text/html" } }));
  render(<Preview path="/api/projects/1/exports/pdf" />);
  expect(await screen.findByRole("alert")).toHaveTextContent("did not return a PDF");
  expect(screen.queryByTitle("PDF preview")).toBeNull();
});

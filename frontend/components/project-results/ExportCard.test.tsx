import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { FileText } from "lucide-react";
import ExportCard from "./ExportCard";
afterEach(cleanup);
it("keeps preview separate from the named download link", () => {
  const preview = vi.fn();
  const { container } = render(<ExportCard title="PDF report" description="Preliminary" fileType="PDF" icon={FileText} href="/fixture.pdf" onPreview={preview} />);
  expect(screen.getByRole("button", { name: "PDF report (PDF)" })).toBeEnabled();
  expect(container.querySelector("a button")).toBeNull();
  fireEvent.click(screen.getByRole("button", { name: "Preview" }));
  expect(preview).toHaveBeenCalledOnce();
});
it("keeps unavailable explanatory text readable without making a download action", () => {
  const { container } = render(<ExportCard title="DXF" description="Unavailable" fileType="DXF" icon={FileText} available={false} />);
  expect(screen.queryByRole("link")).not.toBeInTheDocument();
  expect(container.querySelector('.opacity-55')).toBeNull();
});

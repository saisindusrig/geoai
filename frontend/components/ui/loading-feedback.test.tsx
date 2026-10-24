import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, expect, it } from "vitest";
import { ContentSkeleton, OperationProgress } from "./loading-feedback";

afterEach(cleanup);
it("omits a numeric value for indeterminate work", () => {
  render(<OperationProgress label="Generating layout" />);
  expect(screen.getByRole("progressbar")).not.toHaveAttribute("aria-valuenow");
  expect(screen.getByRole("status")).toHaveTextContent("In progress");
});
it("exposes a measured value when supplied", () => {
  render(<OperationProgress label="Uploading" value={42} />);
  expect(screen.getByRole("progressbar")).toHaveAttribute("aria-valuenow", "42");
});
it("announces a single loading status and hides decorative placeholders", () => {
  const { container } = render(<ContentSkeleton label="Loading projects" />);
  expect(screen.getByRole("status")).toHaveAttribute("aria-busy", "true");
  expect(container.querySelectorAll('[aria-hidden="true"]')).toHaveLength(5);
});

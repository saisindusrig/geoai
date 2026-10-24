import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, expect, it } from "vitest";
import RiskList from "./RiskList";

afterEach(cleanup);
it("keeps missing risk evidence distinct from an empty checklist", () => {
  render(<RiskList />);
  expect(screen.getByRole("status")).toHaveTextContent("Risk information is unavailable");
  expect(screen.queryByText("No critical issues detected yet.")).not.toBeInTheDocument();
});
it("preserves the supplied empty message for a known empty checklist", () => {
  render(<RiskList items={[]} emptyMessage="No recorded risks" />);
  expect(screen.getByText("No recorded risks")).toBeInTheDocument();
});

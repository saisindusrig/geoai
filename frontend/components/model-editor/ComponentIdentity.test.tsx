import { render, screen, cleanup } from "@testing-library/react";
import { afterEach, expect, it } from "vitest";
import ComponentIdentity from "./ComponentIdentity";
import type { EditableModelComponent } from "@/lib/types";
afterEach(cleanup);
it("shows semantic identity including floor zero without dumping metadata", () => {
  render(<ComponentIdentity component={{ id: "office:wall", metadata: {
    componentKind: "WALL", buildingId: "office", floor: 0, specificationId: "spec-1",
    proposalVersionId: "proposal-1", sourceComponentId: "wall", privatePayload: "hidden",
  }} as unknown as EditableModelComponent} />);
  expect(screen.getByText("office:wall")).toBeDefined();
  expect(screen.getByText("0")).toBeDefined();
  expect(screen.getByText("spec-1")).toBeDefined();
  expect(screen.queryByText("hidden")).toBeNull();
});
it("supports ordinary components without specialist metadata", () => {
  render(<ComponentIdentity component={{ id: "legacy" } as EditableModelComponent} />);
  expect(screen.getByText("legacy")).toBeDefined();
  expect(screen.queryByText("Building ID")).toBeNull();
});

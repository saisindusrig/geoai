import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { EditableModelEditor } from "@/hooks/useEditableModelEditor";
import { useProjectStore } from "@/stores/projectStore";
import WorkspaceToolRail from "./WorkspaceToolRail";

function makeEditor(locked = false) {
  return {
    document: { components: [{ id: "deck", locked }] }, selectedIds: ["deck"], tool: "select",
    setTool: vi.fn(), undo: vi.fn(), redo: vi.fn(), duplicateSelected: vi.fn(), deleteSelected: vi.fn(),
    canUndo: true, canRedo: false,
  } as unknown as EditableModelEditor;
}

beforeEach(() => useProjectStore.setState({ activeTool: "select", scene3dMeasureTool: "none", project: null, drawnBoundary: null, drawnAlignment: null, drawVertices: [] }));
afterEach(() => { cleanup(); vi.restoreAllMocks(); });

it("starts site drawing from the first-run action and leaves measurement mode", () => {
  const editor = makeEditor();
  render(<WorkspaceToolRail editor={editor} />);
  fireEvent.click(screen.getByRole("button", {name:"Measure"}));
  act(() => window.dispatchEvent(new CustomEvent("geoai:open-drawing")));
  expect(useProjectStore.getState().activeTool).toBe("draw-polygon");
  expect(useProjectStore.getState().scene3dMeasureTool).toBe("none");
  expect(screen.getByLabelText("Drawing tool options")).toBeInTheDocument();
  expect(screen.queryByLabelText("Measurement tools")).not.toBeInTheDocument();
  expect(editor.setTool).toHaveBeenLastCalledWith("select");
});

it("draws an alignment as a line rather than replacing the site boundary", () => {
  render(<WorkspaceToolRail editor={makeEditor()} />);
  fireEvent.click(screen.getByRole("button", { name: "Draw alignment" }));
  expect(useProjectStore.getState().activeTool).toBe("draw-line");
  expect(screen.getByRole("button", { name: "Edit site boundary" })).toBeDisabled();
  expect(screen.getByRole("button", { name: "Edit alignment" })).toBeDisabled();
});

it("cancels drawing with Escape while a drawing option has focus", () => {
  render(<WorkspaceToolRail editor={makeEditor()} />);
  fireEvent.click(screen.getByRole("button", {name:"Draw alignment"}));
  const smoothing = screen.getByRole("checkbox", {name:"Smooth curve through points"});
  smoothing.focus();
  fireEvent.keyDown(smoothing, {key:"Escape"});
  expect(useProjectStore.getState().activeTool).toBe("select");
  expect(screen.queryByLabelText("Drawing tool options")).not.toBeInTheDocument();
});

it("prevents editing locked selections through buttons and keyboard shortcuts", () => {
  const editor = makeEditor(true);
  render(<WorkspaceToolRail editor={editor} />);
  for (const name of ["Move selection", "Rotate selection", "Scale selection", "Duplicate selection", "Delete selection"]) {
    expect(screen.getByRole("button", { name })).toBeDisabled();
  }
  fireEvent.keyDown(window, { key: "g" });
  fireEvent.keyDown(window, { key: "Delete" });
  expect(editor.setTool).not.toHaveBeenCalled();
  expect(editor.deleteSelected).not.toHaveBeenCalled();
});

it("provides area measurement in the shared measurement menu and resets modes on selection", () => {
  render(<WorkspaceToolRail editor={makeEditor()} />);
  fireEvent.click(screen.getByRole("button", { name: "Measure" }));
  expect(screen.getByRole("button", { name: "Select object" })).toHaveAttribute("aria-pressed", "false");
  fireEvent.click(screen.getByRole("button", { name: /Area/ }));
  expect(useProjectStore.getState().scene3dMeasureTool).toBe("area");
  fireEvent.click(screen.getByRole("button", { name: "Select object" }));
  expect(useProjectStore.getState().scene3dMeasureTool).toBe("none");
  expect(screen.queryByLabelText("Measurement tools")).not.toBeInTheDocument();
});

it("preserves text-field undo and uses drawing undo for vertices instead of object history", () => {
  const editor = makeEditor();
  render(<><input aria-label="Project name" /><WorkspaceToolRail editor={editor} /></>);
  fireEvent.keyDown(screen.getByRole("textbox"), { key: "z", ctrlKey: true });
  expect(editor.undo).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole("button", { name: "Draw alignment" }));
  fireEvent.click(screen.getByRole("button", { name: "Cancel drawing · Esc" }));
  expect(useProjectStore.getState().activeTool).toBe("select");
  fireEvent.click(screen.getByRole("button", { name: "Draw alignment" }));
  act(() => useProjectStore.getState().setDrawVertices([[1, 2], [3, 4]]));
  fireEvent.keyDown(window, { key: "z", ctrlKey: true });
  expect(useProjectStore.getState().drawVertices).toEqual([[1, 2]]);
  expect(editor.undo).not.toHaveBeenCalled();
});

it("frames the selection and fits the project when nothing is selected", () => {
  const editor = makeEditor();
  const dispatch = vi.spyOn(window, "dispatchEvent");
  const view = render(<WorkspaceToolRail editor={editor} />);
  fireEvent.click(screen.getByRole("button", { name: "Frame selection" }));
  expect(dispatch).toHaveBeenLastCalledWith(expect.objectContaining({ type: "geoai:locate-component", detail: "deck" }));
  view.rerender(<WorkspaceToolRail editor={{ ...editor, selectedIds: [] }} />);
  fireEvent.click(screen.getByRole("button", { name: "Fit project" }));
  expect(dispatch).toHaveBeenLastCalledWith(expect.objectContaining({ type: "geoai:fit-project" }));
});

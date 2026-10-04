import { StrictMode, type ReactNode } from "react";
import { act, renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useEditableModelEditor } from "./useEditableModelEditor";
import { documentFromGeometrySpec } from "@/lib/editable-model";
import type { DesignScenario, Project } from "@/lib/types";
import { localSandboxProject, SANDBOX_LAYOUT_KEY } from "@/lib/local-sandbox";

const mocks = vi.hoisted(() => ({ get: vi.fn(), getOptional: vi.fn(), post: vi.fn() }));
vi.mock("@/lib/api", () => ({ api: mocks }));

const project = { id: 7, project_type: "building", center_lat: 13, center_lng: 77 } as Project;
const scenario = { id: 12 } as DesignScenario;
const initial = documentFromGeometrySpec(project, scenario.id, { objects: [{ kind: "box", name: "Column", layer: "column", size: [1, 1, 3], center: [0, 0, 1.5] }] });
const onSaved = vi.fn();
const wrapper = ({ children }: { children: ReactNode }) => <StrictMode>{children}</StrictMode>;

beforeEach(() => {
  window.localStorage.clear();
  vi.clearAllMocks();
  mocks.getOptional.mockResolvedValue({ id: 1, revision_number: 1, document: initial });
  mocks.get.mockResolvedValue({ revisions: [] });
});

describe("local sandbox editor", () => {
  const sandbox = localSandboxProject();
  const open = () => renderHook(() => useEditableModelEditor({ project: sandbox, scenario: null, localSandbox: true, onSaved }), { wrapper });

  it("initializes empty without backend calls and preserves edits on metadata refresh", async () => {
    const { result, rerender } = renderHook(({ project }) => useEditableModelEditor({ project, scenario: null, localSandbox: true, onSaved }), { initialProps: { project: sandbox }, wrapper });
    await waitFor(() => expect(result.current.document?.components).toEqual([]));
    act(() => result.current.addStructuralComponent("building", [10, 20, 1.5]));
    expect(result.current.selected?.transform.position).toEqual([10, 20, 1.5]);
    rerender({ project: { ...sandbox, name: "Changed metadata" } });
    expect(result.current.document?.components).toHaveLength(1);
    expect(result.current.canUndo).toBe(true);
    expect(mocks.get).not.toHaveBeenCalled();
    expect(mocks.getOptional).not.toHaveBeenCalled();
    expect(mocks.post).not.toHaveBeenCalled();
  });

  it("commits a batch transform as one undo step and keeps history across view changes", async () => {
    const { result } = open();
    await waitFor(() => expect(result.current.document).not.toBeNull());
    act(() => result.current.addStructuralComponent("building"));
    act(() => result.current.addStructuralComponent("road"));
    const before = result.current.document!;
    act(() => result.current.commitTransforms(before.components.map((c) => ({ id: c.id, transform: { ...c.transform, position: [5, 10, c.transform.position[2]] } }))));
    act(() => result.current.setSandboxView("map"));
    act(() => result.current.undo());
    expect(result.current.document).toEqual(before);
    act(() => result.current.redo());
    expect(result.current.document?.components.every((c) => c.transform.position[0] === 5)).toBe(true);
    expect(result.current.sandboxView).toBe("map");
  });

  it("supports duplicate/delete and protects locked objects", async () => {
    const { result } = open();
    await waitFor(() => expect(result.current.document).not.toBeNull());
    act(() => result.current.addStructuralComponent("column"));
    act(() => result.current.duplicateSelected());
    expect(result.current.document?.components).toHaveLength(2);
    act(() => result.current.deleteSelected());
    expect(result.current.document?.components).toHaveLength(1);
    const id = result.current.document!.components[0].id;
    act(() => { result.current.select(id); result.current.updateComponent(id, { locked: true }); });
    const locked = result.current.document;
    act(() => result.current.commitTransforms([{ id, transform: { position: [20, 20, 20], rotation_deg: [0, 0, 0], scale: [1, 1, 1] } }]));
    act(() => result.current.duplicateSelected());
    act(() => result.current.deleteSelected());
    expect(result.current.document).toEqual(locked);
  });

  it("autosaves and restores the layout and view without backend calls", async () => {
    const first = open();
    await waitFor(() => expect(first.result.current.document).not.toBeNull());
    act(() => first.result.current.addStructuralComponent("road"));
    act(() => first.result.current.setSandboxView("map"));
    await waitFor(() => expect(first.result.current.localSaveStatus).toBe("saved"), { timeout: 2000 });
    expect(window.localStorage.getItem(SANDBOX_LAYOUT_KEY)).toContain("road");
    first.unmount();
    const second = open();
    await waitFor(() => expect(second.result.current.document?.components).toHaveLength(1));
    expect(second.result.current.sandboxView).toBe("map");
    expect(second.result.current.canUndo).toBe(false);
    expect(mocks.post).not.toHaveBeenCalled();
  });

  it("manual save flushes immediately without discarding undo history", async () => {
    const { result } = open();
    await waitFor(() => expect(result.current.document).not.toBeNull());
    act(() => result.current.addStructuralComponent("beam"));
    await act(async () => { await result.current.save(); });
    expect(result.current.localSaveStatus).toBe("saved");
    expect(result.current.canUndo).toBe(true);
    expect(window.localStorage.getItem(SANDBOX_LAYOUT_KEY)).toContain("beam");
  });

  it("flushes on client-side navigation before the autosave delay", async () => {
    const { result, unmount } = open();
    await waitFor(() => expect(result.current.document).not.toBeNull());
    act(() => result.current.addStructuralComponent("bridge"));
    unmount();
    expect(window.localStorage.getItem(SANDBOX_LAYOUT_KEY)).toContain("bridge");
  });

  it("does not overwrite unreadable saved data until explicit replacement", async () => {
    window.localStorage.setItem(SANDBOX_LAYOUT_KEY, "broken backup");
    const { result } = open();
    await waitFor(() => expect(result.current.restoreError).toBeTruthy());
    act(() => result.current.addStructuralComponent("building"));
    await act(async () => { await expect(result.current.save()).rejects.toThrow("Recover"); });
    expect(window.localStorage.getItem(SANDBOX_LAYOUT_KEY)).toBe("broken backup");
    act(() => result.current.replaceDocument(result.current.document!));
    await act(async () => { await result.current.save(); });
    expect(result.current.restoreError).toBeNull();
    expect(window.localStorage.getItem(SANDBOX_LAYOUT_KEY)).toContain("building");
  });

  it("preserves the in-memory document when storage fails", async () => {
    const { result } = open();
    await waitFor(() => expect(result.current.document).not.toBeNull());
    act(() => result.current.addStructuralComponent("building"));
    const spy = vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => { throw new Error("Storage full"); });
    await act(async () => { await expect(result.current.save()).rejects.toThrow("Storage full"); });
    expect(result.current.localSaveStatus).toBe("failed");
    expect(result.current.document?.components).toHaveLength(1);
    spy.mockRestore();
  });
});

describe("model editor history and validation", () => {
  it("keeps proposals read-only until Apply, with one reversible undo action", async () => {
    const candidate=structuredClone(initial); candidate.components[0].transform.position[2]+=2;
    mocks.post.mockResolvedValue({base_revision_id:1,candidate_document:candidate,patch:[{component_id:candidate.components[0].id,changes:{transform:candidate.components[0].transform}}],warnings:[],validation_errors:[],impact_preview:null});
    const {result}=renderHook(()=>useEditableModelEditor({project,scenario,localSandbox:false,onSaved}));
    await waitFor(()=>expect(result.current.document).not.toBeNull());
    await act(async()=>{await result.current.previewAiEdit("raise deck 2 metres");});
    expect(result.current.document).toEqual(initial);expect(result.current.canUndo).toBe(false);
    act(()=>result.current.rejectAiPreview());expect(result.current.document).toEqual(initial);
    await act(async()=>{await result.current.previewAiEdit("raise deck 2 metres");});
    act(()=>result.current.acceptAiPreview());expect(result.current.document).toEqual(candidate);
    act(()=>result.current.undo());expect(result.current.document).toEqual(initial);expect(result.current.canUndo).toBe(false);
  });
  it("blocks numeric lock bypasses even when visibility is included",async()=>{
    const {result}=renderHook(()=>useEditableModelEditor({project,scenario,localSandbox:false,onSaved}));await waitFor(()=>expect(result.current.document).not.toBeNull());
    const id=initial.components[0].id;act(()=>result.current.updateComponent(id,{locked:true}));const locked=result.current.document;
    act(()=>result.current.updateComponent(id,{visible:false,transform:{position:[50,50,50],rotation_deg:[0,0,0],scale:[1,1,1]}}));expect(result.current.document).toEqual(locked);expect(result.current.editError).toContain("LOCKED");
  });
  it("records one history entry per edit in StrictMode and restores selection on undo", async () => {
    const { result } = renderHook(() => useEditableModelEditor({ project, scenario, localSandbox: false, onSaved }), { wrapper });
    await waitFor(() => expect(result.current.document).not.toBeNull());
    act(() => result.current.addStructuralComponent("beam"));
    expect(result.current.document?.components).toHaveLength(2);
    expect(result.current.canUndo).toBe(true);
    act(() => result.current.undo());
    expect(result.current.document?.components).toHaveLength(1);
    expect(result.current.selectedIds).toEqual([]);
    expect(result.current.canUndo).toBe(false);
    expect(result.current.canRedo).toBe(true);
    act(() => result.current.redo());
    expect(result.current.document?.components).toHaveLength(2);
    expect(result.current.canRedo).toBe(false);
  });

  it("discards a validation response when the draft changes during the request", async () => {
    let resolve!: (value: unknown) => void;
    mocks.post.mockReturnValue(new Promise((done) => { resolve = done; }));
    const { result } = renderHook(() => useEditableModelEditor({ project, scenario, localSandbox: false, onSaved }));
    await waitFor(() => expect(result.current.document).not.toBeNull());
    let pending!: Promise<unknown>;
    act(() => { pending = result.current.validateDraft(); });
    act(() => result.current.updateRulePreset("max_dimension_m", 2));
    await act(async () => { resolve({ passed: true, violations: [] }); await pending; });
    expect(result.current.layoutValidation).toBeNull();
    expect(result.current.dirty).toBe(true);
  });
});

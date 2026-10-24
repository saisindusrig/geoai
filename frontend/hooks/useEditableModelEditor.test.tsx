import { StrictMode, type ReactNode } from "react";
import { act, cleanup, renderHook, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useEditableModelEditor } from "./useEditableModelEditor";
import { documentFromGeometrySpec } from "@/lib/editable-model";
import type { DesignScenario, Project } from "@/lib/types";
import { localSandboxProject, SANDBOX_LAYOUT_KEY } from "@/lib/local-sandbox";
import platformFixture from "@/lib/__fixtures__/maintenance-platform.json";
import { previewAttachment, ATTACHMENT_DEFAULTS, attachmentOf } from "@/lib/platform-attachments";
import type { EditableModelDocument } from "@/lib/types";
import primitiveFixture from '@/lib/__fixtures__/supervised-column.json';
import beamFixture from '@/lib/__fixtures__/supervised-beam.json';
import type {WorkspaceCommand} from '@/lib/workspace-assistant';

const mocks = vi.hoisted(() => ({ get: vi.fn(), getOptional: vi.fn(), post: vi.fn() }));
afterEach(cleanup);
vi.mock("@/lib/api", () => ({ api: mocks }));

const project = { id: 7, project_type: "building", center_lat: 13, center_lng: 77 } as Project;
const scenario = { id: 12 } as DesignScenario;
const initial = documentFromGeometrySpec(project, scenario.id, { objects: [{ kind: "box", name: "Column", layer: "column", size: [1, 1, 3], center: [0, 0, 1.5] }] });
const onSaved = vi.fn();
const wrapper = ({ children }: { children: ReactNode }) => <StrictMode>{children}</StrictMode>;

beforeEach(() => {
  window.localStorage.clear();
  window.sessionStorage.clear();
  vi.clearAllMocks();
  mocks.getOptional.mockResolvedValue({ id: 1, revision_number: 1, document: initial });
  mocks.get.mockResolvedValue({ revisions: [] });
});

describe("local sandbox editor", () => {
  it("keeps parameter previews separate, blocks saving and discards stale previews", async () => {
    const {result}=renderHook(()=>useEditableModelEditor({project,scenario,localSandbox:false,onSaved}));
    await waitFor(()=>expect(result.current.document).not.toBeNull());
    const source=result.current.document!, candidate=structuredClone(source);candidate.components[0].name="Preview";
    act(()=>result.current.setPlatformPreview({source,document:candidate}));
    expect(result.current.document).toEqual(source);expect(result.current.dirty).toBe(false);expect(result.current.canUndo).toBe(false);
    await expect(result.current.save()).rejects.toThrow("Apply or cancel");expect(mocks.post).not.toHaveBeenCalled();
    act(()=>result.current.commit(candidate));expect(result.current.platformPreview).toBeNull();expect(result.current.canUndo).toBe(true);
    act(()=>result.current.undo());expect(result.current.document).toEqual(source);expect(result.current.platformPreview).toBeNull();
  });
  it("ignores hidden/unknown picks and keeps site-save events separate from model saves", async () => {
    const { result } = renderHook(() => useEditableModelEditor({ project, scenario, localSandbox:false,onSaved }));
    await waitFor(() => expect(result.current.document).not.toBeNull());
    const id=initial.components[0].id;
    act(()=>result.current.select(id));
    act(()=>result.current.updateComponent(id,{visible:false}));
    act(()=>result.current.select(id)); act(()=>result.current.select("unknown",true));
    expect(result.current.selectedIds).toEqual([]);
    await act(async()=>{window.dispatchEvent(new CustomEvent("geoai:save-project"));});
    expect(mocks.post).not.toHaveBeenCalled();
    expect(result.current.dirty).toBe(true);
  });
  it("clears selection when a commit hides or removes an object", async () => {
    const { result } = renderHook(() => useEditableModelEditor({ project, scenario, localSandbox: false, onSaved }));
    await waitFor(() => expect(result.current.document).not.toBeNull());
    const id = initial.components[0].id;
    act(() => result.current.select(id));
    act(() => result.current.updateComponent(id, { visible: false }));
    expect(result.current.selectedIds).toEqual([]);
    act(() => result.current.undo());
    act(() => result.current.select(id));
    act(() => result.current.commit({ ...result.current.document!, components: [] }));
    expect(result.current.selectedIds).toEqual([]);
  });

  it("keeps the draft and source revision intact when a remote save fails", async () => {
    const { result } = renderHook(() => useEditableModelEditor({ project, scenario, localSandbox: false, onSaved }));
    await waitFor(() => expect(result.current.document).not.toBeNull());
    act(() => result.current.updateComponent(initial.components[0].id, { name: "Edited column" }));
    const draft = result.current.document;
    mocks.post.mockRejectedValue(new Error("Save unavailable"));
    await act(async () => { await expect(result.current.save()).rejects.toThrow("Save unavailable"); });
    expect(result.current.document).toEqual(draft);
    expect(result.current.baseRevision?.id).toBe(1);
    expect(result.current.dirty).toBe(true);
    expect(result.current.saveError).toBe("Save unavailable");
  });
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
  it("previews whole-assembly deletion from a selected tread and restores it with undo/redo", async () => {
    const source=previewAttachment(platformFixture as unknown as EditableModelDocument,{id:"stairs",kind:"stairs",refs:["industrial-platform-5x3:platform-deck"],parameters:ATTACHMENT_DEFAULTS.stairs});
    mocks.getOptional.mockResolvedValue({id:1,revision_number:1,document:source});
    const {result}=renderHook(()=>useEditableModelEditor({project,scenario,localSandbox:false,onSaved}));await waitFor(()=>expect(result.current.document).not.toBeNull());
    const id=source.components.find(c=>attachmentOf(c)==="stairs")!.id;
    act(()=>result.current.select(id));act(()=>result.current.deleteSelected());expect(result.current.document).toEqual(source);expect(result.current.canUndo).toBe(false);
    expect(result.current.platformPreview?.document.components).toHaveLength(9);expect(result.current.platformPreview?.label).toBe("Delete attached assembly");
    act(()=>result.current.commit(result.current.platformPreview!.document));expect(result.current.document?.components).toHaveLength(9);expect(result.current.selectedIds).toEqual([]);
    act(()=>result.current.undo());expect(result.current.document).toEqual(source);act(()=>result.current.redo());expect(result.current.document?.components).toHaveLength(9);
  });
  it("blocks reference deletion and free transforms that detach generated geometry",async()=>{
    const source=previewAttachment(platformFixture as unknown as EditableModelDocument,{id:"support",kind:"foundation",refs:["industrial-platform-5x3:column-sw"],parameters:ATTACHMENT_DEFAULTS.foundation});
    mocks.getOptional.mockResolvedValue({id:1,revision_number:1,document:source});
    const {result}=renderHook(()=>useEditableModelEditor({project,scenario,localSandbox:false,onSaved}));await waitFor(()=>expect(result.current.document).not.toBeNull());
    act(()=>result.current.select("industrial-platform-5x3:column-sw"));act(()=>result.current.deleteSelected());expect(result.current.document).toEqual(source);expect(result.current.editError).toContain("complete");
    act(()=>result.current.select(source.components.find(c=>attachmentOf(c)==="support")!.id));act(()=>result.current.nudgeSelected(0,1));expect(result.current.document).toEqual(source);expect(result.current.editError).toContain("disconnected");
    act(()=>result.current.duplicateSelected());expect(result.current.document).toEqual(source);expect(result.current.editError).toContain("references");
    act(()=>result.current.updateComponent(result.current.selected!.id,{visible:false}));expect(result.current.document?.components.find(c=>attachmentOf(c)==="support")?.visible).toBe(false);
  });
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

it("exposes saved-model loading failures and retries reads without writes",async()=>{
 mocks.getOptional.mockRejectedValueOnce(new Error('Saved revision unavailable'));
 const {result}=renderHook(()=>useEditableModelEditor({project,scenario,localSandbox:false,onSaved}));
 await waitFor(()=>expect(result.current.loadError).toBe('Saved revision unavailable'));
 expect(result.current.baseRevision).toBeNull();expect(result.current.document).toBeNull();
 act(()=>result.current.retryModelLoad());
 await waitFor(()=>expect(result.current.baseRevision?.id).toBe(1));
 expect(result.current.loadError).toBeNull();expect(mocks.post).not.toHaveBeenCalled();
});


describe('supervised primitive creation in the existing editor',()=>{
 const proposal=()=>({...structuredClone(primitiveFixture),expiresAt:Date.now()+120000}) as unknown as WorkspaceCommand;
 it('previews and cancels without mutation, undo entries or save, and rejects replay',async()=>{
  const {result}=renderHook(()=>useEditableModelEditor({project,scenario,localSandbox:false,onSaved}));
  await waitFor(()=>expect(result.current.baseRevision?.id).toBe(1));const before=structuredClone(result.current.document),c=proposal();
  act(()=>result.current.stagePrimitivePreview(c));
  expect(result.current.platformPreview?.document.components).toHaveLength(2);expect(result.current.document).toEqual(before);expect(result.current.dirty).toBe(false);expect(result.current.canUndo).toBe(false);
  await expect(result.current.save()).rejects.toThrow('Apply or cancel');expect(mocks.post).not.toHaveBeenCalled();
  act(()=>result.current.setPlatformPreview(null));expect(result.current.document).toEqual(before);
  expect(()=>result.current.stagePrimitivePreview(c)).toThrow('Duplicate');
 });
 it('applies exactly one undoable addition and saves only through the existing explicit save',async()=>{
  const {result}=renderHook(()=>useEditableModelEditor({project,scenario,localSandbox:false,onSaved}));
  await waitFor(()=>expect(result.current.baseRevision?.id).toBe(1));const before=structuredClone(result.current.document),c=proposal();
  act(()=>result.current.stagePrimitivePreview(c));act(()=>result.current.applyPrimitivePreview(c.actionId));
  expect(result.current.document?.components).toHaveLength(2);expect(result.current.document?.components[0]).toEqual(before?.components[0]);expect(result.current.dirty).toBe(true);expect(result.current.platformPreview).toBeNull();expect(mocks.post).not.toHaveBeenCalled();
  act(()=>result.current.undo());expect(result.current.document).toEqual(before);
  act(()=>result.current.redo());expect(result.current.document?.components).toHaveLength(2);
  const draft=structuredClone(result.current.document);mocks.post.mockResolvedValue({id:2,document:draft,impact:null});
  await act(async()=>{await result.current.save();});
  expect(mocks.post).toHaveBeenCalledExactlyOnceWith('/api/projects/7/scenarios/12/model-revisions',{base_revision_id:1,document:draft,source:'manual_edit'});
  expect(result.current.baseRevision?.id).toBe(2);expect(result.current.dirty).toBe(false);
  expect(()=>result.current.stagePrimitivePreview(c)).toThrow();
 });
 it('rejects expired, protected and conflicting previews and does not apply after source edits',async()=>{
  const {result}=renderHook(()=>useEditableModelEditor({project,scenario,localSandbox:false,onSaved}));
  await waitFor(()=>expect(result.current.baseRevision?.id).toBe(1));const c=proposal();
  expect(()=>result.current.stagePrimitivePreview({...c,expiresAt:Date.now()-1})).toThrow('expired');
  act(()=>result.current.stagePrimitivePreview(c));expect(()=>result.current.stagePrimitivePreview({...c,actionId:'b'.repeat(64)})).toThrow('resolve');
  act(()=>result.current.updateComponent(initial.components[0].id,{name:'User edit'}));
  expect(()=>result.current.applyPrimitivePreview(c.actionId)).toThrow('no longer current');
 });
});


it('stages and applies an endpoint beam through the same undoable transaction and explicit save',async()=>{
 const {result}=renderHook(()=>useEditableModelEditor({project,scenario,localSandbox:false,onSaved}));
 await waitFor(()=>expect(result.current.baseRevision?.id).toBe(1));const before=structuredClone(result.current.document);
 const c={...structuredClone(beamFixture),expiresAt:Date.now()+120000} as unknown as WorkspaceCommand;
 act(()=>result.current.stagePrimitivePreview(c));expect(result.current.document).toEqual(before);expect(result.current.dirty).toBe(false);expect(mocks.post).not.toHaveBeenCalled();
 act(()=>result.current.applyPrimitivePreview(c.actionId));expect(result.current.document?.components[1]).toEqual(c.candidate);expect(result.current.dirty).toBe(true);
 act(()=>result.current.undo());expect(result.current.document).toEqual(before);act(()=>result.current.redo());expect(result.current.document?.components[1]).toEqual(c.candidate);
 const draft=structuredClone(result.current.document);mocks.post.mockResolvedValue({id:2,document:draft,impact:null});await act(async()=>{await result.current.save();});
 expect(result.current.baseRevision?.id).toBe(2);expect(result.current.dirty).toBe(false);expect(mocks.post).toHaveBeenCalledOnce();
});

it('never substitutes generated geometry or quantities when a saved source cannot be read',async()=>{
 mocks.getOptional.mockRejectedValueOnce(Error('Saved revision unavailable'));
 const savedScenario={...scenario,design_output_json:{editable_model_revision_id:1,geometry_spec:{objects:[{kind:'box',name:'Beam',layer:'beam',size:[5,.3,.45],center:[0,0,3],rotation_deg:[15,20,30]}]}}} as unknown as DesignScenario;
 const {result}=renderHook(()=>useEditableModelEditor({project,scenario:savedScenario,localSandbox:false,onSaved}));
 await waitFor(()=>expect(result.current.loadError).toBe('Saved revision unavailable'));
 expect(result.current.document).toBeNull();expect(result.current.baseRevision).toBeNull();expect(result.current.dirty).toBe(false);expect(mocks.post).not.toHaveBeenCalled();
});

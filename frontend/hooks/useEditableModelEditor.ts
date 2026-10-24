"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { attachmentOf, previewAttachment, validateAttachments } from "@/lib/platform-attachments";
import { api } from "@/lib/api";
import {boxComponent,primitiveDocument} from '@/lib/supervised-primitive';
import type {WorkspaceCommand} from '@/lib/workspace-assistant';
import { documentFromGeometrySpec, estimateDocument } from "@/lib/editable-model";
import { defaultTransformSettings, type TransformSettings } from "@/lib/editor-transform";
import { COMPONENT_SIZES, emptySandboxDocument, readSandboxLayout, sandboxPayload, writeSandboxLayout, type SandboxView, type LocalSandboxDraft } from "@/lib/local-sandbox";
import type {
  DesignScenario,
  EditableModelComponent,
  EditableModelDocument,
  ModelImpact,
  ModelRevision,
  Project,
  StructuralAlternative,
  StructuralLayoutValidation,
  StructuralElementType,
  StructuralAnalysisResult,
} from "@/lib/types";

type Tool = "select" | "translate" | "rotate" | "scale";
type RevisionList = { revisions: ModelRevision[] };
type SaveResult = ModelRevision & { document: EditableModelDocument; impact: ModelImpact; model_url: string };
type AiPreview = {
  patch: { component_id: string; changes: Partial<EditableModelComponent> }[];
  warnings: string[];
  base_revision_id: number;
  candidate_document: EditableModelDocument;
  validation_errors: string[];
  impact_preview: ModelImpact;
};

const clone = <T,>(value: T): T => JSON.parse(JSON.stringify(value)) as T;

export function useEditableModelEditor({
  project,
  scenario,
  localSandbox,
  onSaved,
}: {
  project: Project | null;
  scenario: DesignScenario | null;
  localSandbox: boolean;
  onSaved: () => void | Promise<void>;
}) {
  const [document, setDocument] = useState<EditableModelDocument | null>(null);
  const [baseRevision, setBaseRevision] = useState<ModelRevision | null>(null);
  const [revisions, setRevisions] = useState<ModelRevision[]>([]);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [tool, setTool] = useState<Tool>("select");
  const [snapMeters, setSnapMeters] = useState(0.5);
  const [coordinateMode, setCoordinateMode] = useState<TransformSettings["coordinates"]>("local");
  const [pivotMode, setPivotMode] = useState<TransformSettings["pivot"]>("active");
  const [rotationSnap, setRotationSnap] = useState(defaultTransformSettings.rotationSnap);
  const [scaleSnap, setScaleSnap] = useState(defaultTransformSettings.scaleSnap);
  const [editError, setEditError] = useState<string | null>(null);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [comparison, setComparison] = useState<{ previous: EditableModelDocument; current: EditableModelDocument; mode: "previous" | "current" | "overlay" } | null>(null);
  const [dirty, setDirty] = useState(false);
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(false);
  const [loadError,setLoadError]=useState<string|null>(null);
  const [modelReadVersion,setModelReadVersion]=useState(0);
  const [aiPreview, setAiPreview] = useState<AiPreview | null>(null);
  const [lastImpact, setLastImpact] = useState<ModelImpact | null>(null);
  const [layoutValidation, setLayoutValidation] = useState<StructuralLayoutValidation | null>(null);
  const [alternatives, setAlternatives] = useState<StructuralAlternative[]>([]);
  const [analysisResults, setAnalysisResults] = useState<StructuralAnalysisResult[]>([]);
  const validationSequence = useRef(0);
  const aiSequence = useRef(0);
  const [historyState, setHistoryState] = useState({ canUndo: false, canRedo: false });
  const undoRef = useRef<EditableModelDocument[]>([]);
  const redoRef = useRef<EditableModelDocument[]>([]);
  const localInitialized = useRef(false);
  const saveBlocked = useRef(false);
  const [sandboxView, setSandboxViewState] = useState<SandboxView>("grid");
  const [localDraft, setLocalDraft] = useState<LocalSandboxDraft | undefined>();
  const [localSaveStatus, setLocalSaveStatus] = useState<"saved" | "saving" | "failed">("saved");
  const [localSaveError, setLocalSaveError] = useState<string | null>(null);
  const [restoreError, setRestoreError] = useState<string | null>(null);
  const setSandboxView = useCallback((view: SandboxView) => {
    if (view === sandboxView) return;
    setSandboxViewState(view);
    if (!saveBlocked.current) setLocalSaveStatus("saving");
  }, [sandboxView]);

  const [platformPreviewState, setPlatformPreview] = useState<{source: EditableModelDocument; document: EditableModelDocument; label?: string; proposal?:WorkspaceCommand} | null>(null);
  const platformPreview = platformPreviewState?.source === document ? platformPreviewState : null;
  const scenarioId = scenario?.id ?? null;

  useEffect(() => {
    if (localSandbox) return;
    let cancelled = false;
    undoRef.current = [];
    redoRef.current = [];
    queueMicrotask(() => {
      if (cancelled) return;
      setSelectedIds([]);
      setAiPreview(null);
      setComparison(null);
      setLayoutValidation(null);
      setAlternatives([]);
      setAnalysisResults([]);
      setLastImpact(null);
      setHistoryState({ canUndo: false, canRedo: false });
    });
    if (!project || !scenarioId || localSandbox) {
      queueMicrotask(() => {
        if (cancelled) return;
        setDocument(null);
        setBaseRevision(null);
        setRevisions([]);
        setDirty(false);
      });
      return;
    }
    queueMicrotask(() => {
      if (!cancelled) {setLoading(true);setLoadError(null);}
    });
    void Promise.all([
      api.getOptional<ModelRevision>(`/api/projects/${project.id}/scenarios/${scenarioId}/model-revisions/latest`),
      api.get<RevisionList>(`/api/projects/${project.id}/scenarios/${scenarioId}/model-revisions`),
    ]).then(([latest, list]) => {
      if (cancelled) return;
      if(!latest&&scenario?.design_output_json?.editable_model_revision_id)throw Error('Saved revision is unavailable. No generated geometry substitute was loaded.');
      const fallback = scenario?.design_output_json?.geometry_spec
        ? documentFromGeometrySpec(project, scenarioId, scenario.design_output_json.geometry_spec)
        : null;
      setBaseRevision(latest);
      setDocument(latest?.document ?? fallback);
      setRevisions(list.revisions);
      setDirty(Boolean(!latest && fallback));
      setLoading(false);
    }).catch((failure) => {
      if (cancelled) return;
      setBaseRevision(null);setLoadError(failure instanceof Error ? failure.message : "Saved revision request failed.");
      const fallback = !scenario?.design_output_json?.editable_model_revision_id&&scenario?.design_output_json?.geometry_spec
        ? documentFromGeometrySpec(project, scenarioId, scenario.design_output_json.geometry_spec)
        : null;
      setDocument(fallback);
      setDirty(Boolean(fallback));
      setLoading(false);
    });
    return () => { cancelled = true; };
  }, [project, scenario, scenarioId, localSandbox,modelReadVersion]);

  useEffect(() => {
    if (!localSandbox || !project || localInitialized.current) return;
    let cancelled = false;
    queueMicrotask(() => {
      if (cancelled || localInitialized.current) return;
      localInitialized.current = true;
      const restored = readSandboxLayout();
      saveBlocked.current = Boolean(restored.error);
      setDocument(restored.payload?.document ?? emptySandboxDocument(project));
      setSandboxViewState(restored.payload?.view ?? "grid");
      setLocalDraft(restored.payload?.draft);
      setRestoreError(restored.error);
      if (restored.error) {
        setLocalSaveStatus("failed");
        setLocalSaveError("Saved data could not be restored. Download the saved data before replacing it.");
      }
    });
    return () => { cancelled = true; };
  }, [localSandbox, project]);

  const saveLocal = useCallback(() => {
    if (!document) return;
    if (saveBlocked.current) throw new Error("Recover or explicitly replace the unreadable saved layout first.");
    setLocalSaveStatus("saving");
    try {
      writeSandboxLayout(sandboxPayload(document, sandboxView, localDraft));
      setDirty(false);
      setLocalSaveStatus("saved");
      setLocalSaveError(null);
    } catch (error) {
      setLocalSaveStatus("failed");
      setLocalSaveError(error instanceof Error ? error.message : "Local storage is unavailable.");
      throw error;
    }
  }, [document, sandboxView, localDraft]);

  const previousView = useRef<SandboxView>("grid");
  const localSnapshot = useRef<ReturnType<typeof sandboxPayload> | null>(null);
  useEffect(() => {
    if (localSandbox && document) localSnapshot.current = sandboxPayload(document, sandboxView, localDraft);
  }, [localSandbox, document, sandboxView, localDraft]);

  useEffect(() => {
    if (!localSandbox) return;
    return () => {
      // Client-side navigation does not fire pagehide. Flush the latest committed layout.
      if (!saveBlocked.current && localSnapshot.current) {
        try { writeSandboxLayout(localSnapshot.current); } catch { /* Existing save failures remain visible until navigation. */ }
      }
    };
  }, [localSandbox]);

  useEffect(() => {
    if (!localSandbox || !document || saveBlocked.current) return;
    const viewChanged = previousView.current !== sandboxView;
    previousView.current = sandboxView;
    if (!dirty && !viewChanged) return;
    const timer = window.setTimeout(() => { try { saveLocal(); } catch { /* Error is shown in the workspace. */ } }, 750);
    return () => window.clearTimeout(timer);
  }, [localSandbox, document, dirty, sandboxView, saveLocal]);

  useEffect(() => {
    if (!localSandbox || !document) return;
    const flush = () => { try { saveLocal(); } catch { /* Keep the in-memory layout available for export. */ } };
    const hidden = () => { if (window.document.visibilityState === "hidden") flush(); };
    window.addEventListener("geoai:save-project", flush);
    window.addEventListener("pagehide", flush);
    window.document.addEventListener("visibilitychange", hidden);
    return () => {
      window.removeEventListener("geoai:save-project", flush);
      window.removeEventListener("pagehide", flush);
      window.document.removeEventListener("visibilitychange", hidden);
    };
  }, [localSandbox, document, saveLocal]);

  useEffect(() => {
    if (!dirty) return;
    const beforeUnload = (event: BeforeUnloadEvent) => {
      event.preventDefault();
      event.returnValue = "";
    };
    window.addEventListener("beforeunload", beforeUnload);
    return () => window.removeEventListener("beforeunload", beforeUnload);
  }, [dirty]);

  const commit = useCallback((next: EditableModelDocument) => {
    const errors = validateAttachments(next);
    if (errors.length) { setEditError(errors.join(" ")); return false; }
    setEditError(null);
    setPlatformPreview(null);
    aiSequence.current += 1;
    validationSequence.current += 1;
    setLayoutValidation(null);
    setLastImpact(null);
    if (next.structural_layout?.approval) {
      next = clone(next);
      delete next.structural_layout!.approval;
    }
    if (document) undoRef.current.push(clone(document));
    if (undoRef.current.length > 60) undoRef.current.shift();
    setDocument(next);
    setSelectedIds(ids => ids.filter(id => next.components.some(component => component.id === id && component.visible)));
    redoRef.current = [];
    setDirty(true);
    if (localSandbox && !saveBlocked.current) setLocalSaveStatus("saving");
    setHistoryState({ canUndo: undoRef.current.length > 0, canRedo: redoRef.current.length > 0 });
    setAiPreview(null);
    return true;
  }, [document, localSandbox]);

  const stagedActions=useRef(new Set<string>());
  const stagePrimitivePreview=useCallback((command:WorkspaceCommand)=>{
    if(!document||!baseRevision||localSandbox||loading||loadError||saving||dirty||aiPreview||comparison||platformPreview||JSON.stringify(document)!==JSON.stringify(baseRevision.document))throw Error('Open a clean saved primitive model and resolve other previews first.');
    const next=primitiveDocument(command,document,baseRevision.id);
    const key=`geoai:primitive:${command.actionId}`;
    if(stagedActions.current.has(key)||sessionStorage.getItem(key))throw Error('Duplicate proposal replay rejected. Request a new proposal.');
    const errors=validateAttachments(next);if(errors.length)throw Error(errors.join(' '));
    sessionStorage.setItem(key,'reviewed');stagedActions.current.add(key);
    setPlatformPreview({source:document,document:next,label:`Proposed ${command.candidate?.category} · temporary · not applied or saved`,proposal:command});
  },[document,baseRevision,localSandbox,loading,loadError,saving,dirty,aiPreview,comparison,platformPreview]);
  const applyPrimitivePreview=useCallback((actionId:string)=>{
    const p=platformPreview;
    if(!p?.proposal||p.proposal.actionId!==actionId||p.source!==document||dirty||saving||loading||loadError||aiPreview||comparison||!baseRevision)throw Error('Preview is no longer current. Nothing applied.');
    const next=primitiveDocument(p.proposal,document,baseRevision.id);
    if(!commit(next))throw Error('The existing editor rejected this addition.');
    setSelectedIds([p.proposal.candidate!.id]);
  },[platformPreview,document,dirty,saving,loading,loadError,aiPreview,comparison,baseRevision,commit]);

  const updateComponent = useCallback((id: string, changes: Partial<EditableModelComponent>) => {
    if (!document) return;
    const next = clone(document);
    const component = next.components.find((item) => item.id === id);
    if (!component) return;
    if (component.geometry.kind === "cad_mesh" && (changes.geometry || changes.metadata || changes.material || (changes.transform && changes.transform.scale.some(v => v !== 1)))) { setEditError("CAD supports rigid transforms only. Parameter/material edits require reviewed regeneration."); return; }
    if (component.locked && Object.keys(changes).some(key => key !== "locked" && key !== "visible")) { setEditError("OBJECT LOCKED · Unlock to edit."); return; }
    if (changes.transform && (!changes.transform.position.every(Number.isFinite) || !changes.transform.rotation_deg.every(Number.isFinite) || !changes.transform.scale.every(value => Number.isFinite(value) && value > 0))) { setEditError("Transform values must be finite; scale must be greater than zero."); return; }
    setEditError(null);
    Object.assign(component, changes);
    commit(next);
  }, [commit, document]);

  const commitTransforms = useCallback((changes: { id: string; transform: EditableModelComponent["transform"] }[]) => {
    if (!document) return;
    const next = clone(document);
    let changed = false;
    for (const patch of changes) {
      const component = next.components.find((c) => c.id === patch.id);
      if (!component || component.locked || !component.visible || component.geometry.kind === "asset_instance") continue;
      if (component.geometry.kind === "cad_mesh" && patch.transform.scale.some(v => v !== 1)) { setEditError("CAD scaling requires reviewed parametric regeneration."); return; }
      if (!patch.transform.position.every(Number.isFinite) || !patch.transform.rotation_deg.every(Number.isFinite) || !patch.transform.scale.every((n) => Number.isFinite(n) && n > 0)) continue;
      if (JSON.stringify(component.transform) !== JSON.stringify(patch.transform)) { component.transform = clone(patch.transform); changed = true; }
    }
    if (changed) commit(next);
  }, [commit, document]);

  const replaceDocument = useCallback((next: EditableModelDocument, view: SandboxView = "grid", draft?: LocalSandboxDraft) => {
    saveBlocked.current = false;
    setRestoreError(null);
    setLocalSaveError(null);
    setSandboxViewState(view);
    if (draft) setLocalDraft(draft);
    setSelectedIds([]);
    commit(clone(next));
  }, [commit]);

  const nudgeSelected = useCallback((axis: 0 | 1 | 2, amount: number) => {
    if (!document || !selectedIds.length) return;
    const next = clone(document);
    for (const component of next.components) {
      if (!selectedIds.includes(component.id) || component.locked || !component.visible || component.geometry.kind === "asset_instance") continue;
      const position = component.transform.position[axis] + amount;
      const snapped = snapMeters > 0 ? Math.round(position / snapMeters) * snapMeters : position;
      component.transform.position[axis] = Number(snapped.toFixed(3));
    }
    commit(next);
  }, [commit, document, selectedIds, snapMeters]);

  const transformSelected = useCallback((kind: "rotate" | "scale", amount: number) => {
    if (!document || !selectedIds.length) return;
    if (kind === "scale" && document.components.some(c => selectedIds.includes(c.id) && c.geometry.kind === "cad_mesh")) { setEditError("CAD scaling requires reviewed parametric regeneration."); return; }
    const next = clone(document);
    for (const component of next.components) {
      if (!selectedIds.includes(component.id) || component.locked || !component.visible || component.geometry.kind === "asset_instance") continue;
      if (kind === "rotate") component.transform.rotation_deg[2] += amount;
      else component.transform.scale = component.transform.scale.map((v) => Math.max(0.05, Number((v * amount).toFixed(3)))) as [number, number, number];
    }
    commit(next);
  }, [commit, document, selectedIds]);

  const undo = useCallback(() => {
    aiSequence.current += 1;
    const previous = undoRef.current.pop();
    if (!previous) return;
    validationSequence.current += 1;
    setLayoutValidation(null);
    setLastImpact(null);
    setAiPreview(null);
    if (document) redoRef.current.push(clone(document));
    setDocument(previous);
    setSelectedIds((ids) => ids.filter((id) => previous.components.some((c) => c.id === id)));
    setDirty(!baseRevision?.document || JSON.stringify(previous) !== JSON.stringify(baseRevision.document));
    if (localSandbox && !saveBlocked.current) setLocalSaveStatus("saving");
    setHistoryState({ canUndo: undoRef.current.length > 0, canRedo: redoRef.current.length > 0 });
  }, [document, localSandbox, baseRevision]);

  const redo = useCallback(() => {
    aiSequence.current += 1;
    const next = redoRef.current.pop();
    if (!next) return;
    validationSequence.current += 1;
    setLayoutValidation(null);
    setLastImpact(null);
    setAiPreview(null);
    if (document) undoRef.current.push(clone(document));
    setDocument(next);
    setDirty(!baseRevision?.document || JSON.stringify(next) !== JSON.stringify(baseRevision.document));
    if (localSandbox && !saveBlocked.current) setLocalSaveStatus("saving");
    setHistoryState({ canUndo: undoRef.current.length > 0, canRedo: redoRef.current.length > 0 });
  }, [document, localSandbox, baseRevision]);

  const duplicateSelected = useCallback(() => {
    if (!document || !selectedIds.length) return;
    if (document.components.some(c => selectedIds.includes(c.id) && attachmentOf(c))) { setEditError("Add attached assemblies using the attachment controls so their references remain valid."); return; }
    if (document.components.some(c => selectedIds.includes(c.id) && c.geometry.kind === "cad_mesh")) { setEditError("CAD duplication requires a reviewed BIM assembly proposal."); return; }
    const next = clone(document);
    const copies = next.components.filter((c) => selectedIds.includes(c.id) && !c.locked).map((component) => ({
      ...clone(component),
      id: crypto.randomUUID(),
      name: `${component.name} copy`,
      transform: { ...component.transform, position: [component.transform.position[0] + snapMeters, component.transform.position[1] + snapMeters, component.transform.position[2]] as [number, number, number] },
    }));
    if (!copies.length) return;
    next.components.push(...copies);
    commit(next);
    setSelectedIds(copies.map((item) => item.id));
  }, [commit, document, selectedIds, snapMeters]);

  const deleteSelected = useCallback(() => {
    if (!document || !selectedIds.length) return;
    const managed = document.components.filter(c => selectedIds.includes(c.id) && attachmentOf(c));
    if (managed.length) {
      if (managed.length !== selectedIds.length) { setEditError("Select attached assemblies separately from other objects for a deletion preview."); return; }
      try {
        let candidate=document;
        for(const id of new Set(managed.map(c=>attachmentOf(c)!))) candidate=previewAttachment(candidate,null,id);
        setComparison(null);setPlatformPreview({source:document,document:candidate,label:"Delete attached assembly"});setEditError(null);
        window.dispatchEvent(new Event("geoai:inspect-component"));
      } catch(e) { setEditError((e as Error).message); }
      return;
    }
    if (document.components.some(c => selectedIds.includes(c.id) && c.geometry.kind === "cad_mesh")) { setEditError("CAD deletion requires a reviewed BIM assembly proposal; hide components instead."); return; }
    const next = clone(document);
    next.components = next.components.filter((item) => !selectedIds.includes(item.id) || item.locked);
    if (next.components.length === document.components.length) return;
    commit(next);
    setSelectedIds([]);
  }, [commit, document, selectedIds]);

  const save = useCallback(async () => {
    if (platformPreview) throw new Error("Apply or cancel the platform preview before saving.");
    if (document) { const errors=validateAttachments(document); if(errors.length) throw new Error(errors.join(" ")); }
    if (localSandbox) { saveLocal(); return null; }
    if (!project || !document || !scenarioId || localSandbox) return null;
    setSaving(true);
    setSaveError(null);
    try {
      const result = await api.post<SaveResult>(
        `/api/projects/${project.id}/scenarios/${scenarioId}/model-revisions`,
        {
          base_revision_id: baseRevision?.id ?? null,
          document,
          source: aiPreview ? "ai_edit" : "manual_edit",
        },
      );
      setBaseRevision(result);
      setRevisions((current) => [result, ...current]);
      setDocument(result.document);
      setLastImpact(result.impact);
      setDirty(false);
      setAiPreview(null);
      undoRef.current = [];
      redoRef.current = [];
      setHistoryState({ canUndo: false, canRedo: false });
      await onSaved();
      return result;
    } catch (error) {
      setSaveError(error instanceof Error ? error.message : "Save failed");
      throw error;
    } finally {
      setSaving(false);
    }
  }, [aiPreview, baseRevision, document, localSandbox, onSaved, project, scenarioId, saveLocal, platformPreview]);
  useEffect(()=>{
    if(localSandbox)return;
    const flush=()=>{void save().catch(()=>undefined);};
    window.addEventListener("geoai:save-model-revision",flush);
    return()=>window.removeEventListener("geoai:save-model-revision",flush);
  },[save,localSandbox]);

  const previewAiEdit = useCallback(async (prompt: string) => {
    if (!project || !baseRevision || !scenarioId) return null;
    if(dirty) throw new Error("Save the current draft before preparing a proposal.");
    const sequence=++aiSequence.current;
    const preview = await api.post<AiPreview>(
      `/api/projects/${project.id}/scenarios/${scenarioId}/model-revisions/${baseRevision.id}/ai-edit`,
      { prompt },
    );
    if(sequence!==aiSequence.current)throw new Error("The model changed while the proposal was being prepared. Request a new proposal.");
    setAiPreview(preview);
    return preview;
  }, [baseRevision, project, scenarioId, dirty]);

  const acceptAiPreview = useCallback(() => {
    if (!aiPreview || aiPreview.validation_errors.length || dirty || aiPreview.base_revision_id!==baseRevision?.id || !aiPreview.patch.length) return;
    commit(aiPreview.candidate_document);
    setLastImpact(aiPreview.impact_preview);
  }, [aiPreview, commit, dirty, baseRevision]);

  const select = useCallback((id: string | null, additive = false) => {
    if (!id) return setSelectedIds([]);
    if (!document?.components.some(c => c.id === id && c.visible)) return;
    setSelectedIds((current) => additive
      ? current.includes(id) ? current.filter((item) => item !== id) : [...current, id]
      : [id]);
  }, [document]);

  const loadLayoutIntelligence = useCallback(async () => {
    if (!project || !scenarioId || !baseRevision) return null;
    const base = `/api/projects/${project.id}/scenarios/${scenarioId}/structural-layout/${baseRevision.id}`;
    const sequence = ++validationSequence.current;
    const [validation, options, imported] = await Promise.all([
      api.get<StructuralLayoutValidation>(`${base}/validation`),
      api.get<{ alternatives: StructuralAlternative[] }>(`${base}/alternatives`),
      api.get<{ results: StructuralAnalysisResult[] }>(`${base}/analysis-results`),
    ]);
    if (sequence !== validationSequence.current) return null;
    if (!dirty) setLayoutValidation(validation);
    setAlternatives(options.alternatives);
    setAnalysisResults(imported.results);
    return validation;
  }, [baseRevision, dirty, project, scenarioId]);

  const validateDraft = useCallback(async () => {
    if (!project || !scenarioId || !document) throw new Error("Generate or open a layout first.");
    const sequence = ++validationSequence.current;
    const result = await api.post<StructuralLayoutValidation>(`/api/projects/${project.id}/scenarios/${scenarioId}/structural-layout/validate`, { document });
    if (sequence === validationSequence.current) setLayoutValidation(result);
    return result;
  }, [document, project, scenarioId]);

  const updateRulePreset = useCallback((key: string, value: number) => {
    if (!document || !Number.isFinite(value) || value < 0) return;
    const next = clone(document);
    next.structural_layout = { ...next.structural_layout, rule_preset: { ...next.structural_layout?.rule_preset, [key]: value } };
    commit(next);
  }, [commit, document]);

  const importAnalysisResults = useCallback(async (file: File) => {
    if (!project || !scenarioId || !baseRevision || dirty) throw new Error("Open a saved revision before importing results.");
    if (file.size > 5 * 1024 * 1024) throw new Error("Analysis result must be smaller than 5 MB.");
    const payload: unknown = JSON.parse(await file.text());
    const result = await api.post<StructuralAnalysisResult>(`/api/projects/${project.id}/scenarios/${scenarioId}/structural-layout/${baseRevision.id}/analysis-results`, payload);
    setAnalysisResults((current) => [result, ...current]);
  }, [baseRevision, dirty, project, scenarioId]);

  const approveLayout = useCallback(async () => {
    if (!project || !scenarioId || !baseRevision || dirty) throw new Error("Save the current layout before approving it.");
    const result = await api.post<{ validation: StructuralLayoutValidation }>(`/api/projects/${project.id}/scenarios/${scenarioId}/structural-layout/${baseRevision.id}/approve`);
    setLayoutValidation(result.validation);
    return result;
  }, [baseRevision, dirty, project, scenarioId]);

  const exportAnalysisPackage = useCallback(async () => {
    if (!project || !scenarioId || !baseRevision || dirty) throw new Error("Save and approve the current revision before export.");
    const result = await api.get(`/api/projects/${project.id}/scenarios/${scenarioId}/structural-layout/${baseRevision.id}/analysis-package`);
    const url = URL.createObjectURL(new Blob([JSON.stringify(result, null, 2)], { type: "application/json" }));
    const link = window.document.createElement("a");
    link.href = url;
    link.download = `structural-analysis-revision-${baseRevision.id}.json`;
    link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }, [baseRevision, dirty, project, scenarioId]);

  const addStructuralComponent = useCallback((category: StructuralElementType, position?: [number, number, number]) => {
    if (!document) return;
    const next = clone(document);
    const size = COMPONENT_SIZES[category] ?? [1, 1, 1];
    const id = crypto.randomUUID();
    next.components.push({...boxComponent(category,id,size,position??[0,0,size[2]/2]),name:`${category.replaceAll('_',' ')} ${next.components.length+1}`});
    commit(next);
    setSelectedIds([id]);
  }, [commit, document]);

  const impact = useMemo(() => {
    if (document?.components.length && document.components.every(component => component.quantity?.included === false)) return null;
    return lastImpact ?? estimateDocument(document);
  }, [document, lastImpact]);
  const selected = document?.components.find((item) => item.id === selectedIds[0]) ?? null;
  const revisionDocument = useCallback(async (id: number) => {
    if (!project || !scenarioId) throw new Error("Open a saved project revision first.");
    const result = await api.get<ModelRevision>(`/api/projects/${project.id}/scenarios/${scenarioId}/model-revisions/${id}`);
    if (!result.document) throw new Error("Revision document is unavailable.");
    const {placement} = await api.get<{placement:{longitude:number;latitude:number;elevation:number|null;offset:number;heading:number}|null}>(`/api/projects/${project.id}/engineering/placements/${id}`);
    return placement && placement.elevation !== null ? { ...result.document, origin:{lng:placement.longitude,lat:placement.latitude,elevation_m:placement.elevation+placement.offset,heading_deg:placement.heading} } : result.document;
  },[project,scenarioId]);

  return {
    document, baseRevision, revisions, selected, selectedIds, select, selectMany: (ids: string[]) => setSelectedIds([...new Set(ids)].filter(id => document?.components.some(component => component.id === id))), tool, setTool,
    comparison, setComparison, revisionDocument, platformPreview, setPlatformPreview,
    coordinateMode, setCoordinateMode, pivotMode, setPivotMode, rotationSnap, setRotationSnap, scaleSnap, setScaleSnap, editError, setEditError, saveError,
    snapMeters, setSnapMeters, dirty, saving, loading, loadError,retryModelLoad:()=>setModelReadVersion(v=>v+1), aiPreview, impact,
    updateComponent, nudgeSelected, transformSelected, duplicateSelected, deleteSelected,
    commitTransforms, replaceDocument, commit, sandboxView, setSandboxView, localSaveStatus, localSaveError, restoreError, localDraft,
    undo, redo, canUndo: historyState.canUndo, canRedo: historyState.canRedo,
    save, previewAiEdit, acceptAiPreview, rejectAiPreview: () => { aiSequence.current++; setAiPreview(null); },
    layoutValidation, alternatives, loadLayoutIntelligence, approveLayout,
    addStructuralComponent,
    stagePrimitivePreview,applyPrimitivePreview,
    exportAnalysisPackage,
    validateDraft, updateRulePreset, importAnalysisResults, analysisResults,
    canPersist: Boolean(scenarioId && !localSandbox),
  };
}

export type EditableModelEditor = ReturnType<typeof useEditableModelEditor>;

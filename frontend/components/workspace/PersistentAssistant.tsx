"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import ProposalReview from "./ProposalReview";
import type { ConversationView, MessageView, MessageInput, MemoryView, MemoryInput, ProfileView, ReadinessView, SelectionVersion, SelectionInput } from "@/lib/generated/stage1";

type Props = { projectId: number; selectedIds: string[]; revisionId: number | null; dirty: boolean; siteGeometry?: import("@/lib/types").GeoJSONGeometry | null };
type Messages = { messages: MessageView[]; nextBefore: number | null };

function memoryLabel(item: MemoryView) {
  const content = item.content;
  if (content.kind === "REQUIREMENT") return `${content.key}: ${content.constraint.operator} ${String(content.constraint.value)} ${content.constraint.unit ?? ""}`;
  if (content.kind === "PREFERENCE") return `${content.key}: ${content.value}`;
  return content.statement;
}

export default function PersistentAssistant({ projectId, selectedIds, revisionId, dirty, siteGeometry }: Props) {
  const base = `/api/projects/${projectId}`;
  const [conversation, setConversation] = useState<ConversationView | null>(null);
  const [messages, setMessages] = useState<MessageView[]>([]);
  const [before, setBefore] = useState<number | null>(null);
  const [memory, setMemory] = useState<MemoryView[]>([]);
  const [profile, setProfile] = useState<ProfileView | null>(null);
  const [readiness, setReadiness] = useState<ReadinessView | null>(null);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pendingSend, setPendingSend] = useState(false);
  const [memoryKey, setMemoryKey] = useState("");
  const [memoryValue, setMemoryValue] = useState("");
  const [memoryUnit, setMemoryUnit] = useState("");
  const [source, setSource] = useState<{ evidence: { sourceType: string; status: string; retrievedAt: string; source: { kind: string; sourceUrl?: string; reason?: string } } } | null>(null);
  const retry = useRef<(() => Promise<void>) | null>(null);
  const frozenSend = useRef<MessageInput | null>(null);
  const frozenSite = useRef<Props["siteGeometry"]>(null);
  const siteKey = JSON.stringify(siteGeometry ?? null);
  const activeRun = messages.find(m => m.run && ["QUEUED", "CLASSIFYING", "READING_CONTEXT", "RUNNING", "PROPOSING", "VALIDATING"].includes(m.run.status))?.run;
  const activeProposal = messages.flatMap(m => m.parts).filter(p => p.kind === "PROPOSAL").at(-1)?.proposalVersionId ?? null;
  const mounted = useRef(true);

  const loadProfile = useCallback(async (id: string) => {
    const p = await api.get<ProfileView>(`${base}/site-profiles/${id}`);
    const r = await api.get<ReadinessView>(`${base}/site-profiles/${id}/readiness`);
    if (mounted.current) { setProfile(p); setReadiness(r); }
  }, [base]);

  const loadMessages = useCallback(async (id: string) => {
    const result = await api.get<Messages>(`${base}/conversations/${id}/messages`);
    if (mounted.current) { setMessages(result.messages); setBefore(result.nextBefore); }
  }, [base]);

  const loadMemory = useCallback(async () => {
    const result = await api.get<{ items: MemoryView[] }>(`${base}/memory`);
    if (mounted.current) setMemory(result.items);
  }, [base]);

  const load = useCallback(async () => {
    const list = await api.get<{ conversations: ConversationView[] }>(`${base}/conversations`);
    const c = list.conversations[0] ?? await api.post<ConversationView>(`${base}/conversations`, { clientRequestId: "workspace-primary", title: "Project discussion" });
    if (!mounted.current) return;
    setConversation(c);
    await loadMessages(c.id);
    await loadMemory();
    const profiles = await api.get<{ profiles: ProfileView[] }>(`${base}/site-profiles`);
    if (profiles.profiles[0]) await loadProfile(profiles.profiles[0].id);
  }, [base, loadMemory, loadMessages, loadProfile]);

  const execute = useCallback(async (action: () => Promise<void>) => {
    retry.current = action; setBusy(true); setError(null);
    try { await action(); if (mounted.current) retry.current = null; }
    catch (e) { if (mounted.current) setError(e instanceof Error ? e.message : "Could not save. Please retry."); }
    finally { if (mounted.current) setBusy(false); }
  }, []);

  useEffect(() => {
    mounted.current = true;
    let cancelled = false;
    queueMicrotask(() => { if (!cancelled) void execute(load); });
    return () => { cancelled = true; mounted.current = false; };
  }, [execute, load]);

  useEffect(() => {
    if (!activeRun || !conversation) return;
    const timer = window.setInterval(() => {
      void api.get(`${base}/assistant/runs/${activeRun.id}`).then(() => loadMessages(conversation.id)).catch(e => setError(e.message));
    }, 1500);
    return () => window.clearInterval(timer);
  }, [activeRun, conversation, base, loadMessages]);

  useEffect(() => {
    if (!profile || !["QUEUED", "RUNNING"].includes(profile.refreshState)) return;
    const timer = window.setInterval(() => {
      void loadProfile(profile.id).catch(e => {
        setError(e instanceof Error ? e.message : "Profile status unavailable.");
        retry.current = () => loadProfile(profile.id);
      });
    }, 1500);
    return () => window.clearInterval(timer);
  }, [profile, loadProfile]);

  useEffect(() => {
    if (profile?.id) void loadProfile(profile.id).catch(e => {
      setError(e instanceof Error ? e.message : "Site readiness could not be refreshed.");
      setReadiness(null);
      setProfile(current => current ? { ...current, current: false } : current);
      retry.current = () => loadProfile(profile.id);
    });
  }, [revisionId, siteKey, profile?.id, loadProfile]);

  const send = () => {
    if (!conversation || busy || (!input.trim() && !frozenSend.current)) return;
    // Capture synchronously at click time; a failed submission retries this exact body.
    const body: MessageInput = frozenSend.current ?? {
      clientRequestId: crypto.randomUUID(), parts: [{ kind: "TEXT", text: input.trim() }],
      context: { selectedObjectIds: [...selectedIds], modelRevisionId: revisionId === null ? null : String(revisionId),
        siteSelectionVersionId: profile?.version?.selectionVersion.id ?? null,
        siteProfileVersionId: profile?.version?.id ?? null, scenarioId: null, proposalVersionId: activeProposal, editorDirty: dirty },
    };
    if (!frozenSend.current) frozenSite.current = siteGeometry ? structuredClone(siteGeometry) : null;
    frozenSend.current = body; setPendingSend(true);
    void execute(async () => {
      if (frozenSite.current) {
        const kind = frozenSite.current.type === "Point" ? "POINT" : frozenSite.current.type === "LineString" ? "ROUTE" : "AREA";
        const selectionInput: SelectionInput = { selection: { kind, geometry: frozenSite.current } as SelectionInput["selection"], originalCrs: { status: "RESOLVED", definition: "EPSG:4326", axisOrder: "XY", unit: "DEGREE", transformId: null } };
        const selected = await api.post<SelectionVersion>(`${base}/site-selections`, selectionInput);
        if (body.context.siteSelectionVersionId !== selected.id) body.context.siteProfileVersionId = null;
        body.context.siteSelectionVersionId = selected.id;
      }
      await api.post(`${base}/conversations/${conversation.id}/messages`, body);
      await loadMessages(conversation.id);
      frozenSend.current = null; setPendingSend(false); setInput("");
    });
  };

  const refresh = () => void execute(async () => {
    const selection = await api.post<SelectionVersion>(`${base}/site-selections/from-project`);
    const queued = await api.post<{ id: string }>(`${base}/site-profiles`, { selectionVersionId: selection.id });
    await loadProfile(queued.id);
  });

  const proposeMemory = () => {
    if (!memoryKey.trim() || !memoryValue.trim()) return;
    const value = Number.isFinite(Number(memoryValue)) ? Number(memoryValue) : memoryValue.trim();
    const body: MemoryInput = { clientRequestId: crypto.randomUUID(), assetId: null, content: { kind: "REQUIREMENT", key: memoryKey.trim(),
      constraint: { operator: "EQ", value, unit: memoryUnit.trim() || null }, hardness: "HARD" }, sourceMessageIds: [], evidenceIds: [] };
    void execute(async () => {
      await api.post(`${base}/memory`, body); await loadMemory(); setMemoryKey(""); setMemoryValue(""); setMemoryUnit("");
    });
  };

  const decide = (item: MemoryView, action: "accept" | "reject") => void execute(async () => {
    await api.post(`${base}/memory/${item.id}/versions/${item.version}/${action}`, { expectedStatus: "PROPOSED" });
    await loadMemory();
  });

  return <section aria-label="Project assistant" className="flex h-full min-h-0 flex-col text-xs">
    <div className="space-y-2 border-b border-border p-3">
      <p className="font-semibold">GeoAI Assistant</p>
      <p className="text-muted-foreground">Discuss any civil asset. Messages and reviewed requirements stay with this project.</p>
      <p role="status" className="text-[11px] text-muted-foreground">{activeRun?.progress ?? "Site-aware discussion and concept proposals. Geometry changes require a separate supported workflow."}</p>
      <div aria-label="Selected object context" className="break-words rounded border border-border px-2 py-1">
        {selectedIds.length ? `Selected: ${selectedIds.join(", ")}` : "No objects selected"}
        {revisionId !== null && ` · revision ${revisionId}`}{dirty && " · unsaved edits"}
      </div>
      <div className="flex items-start justify-between gap-2">
        <div aria-label="Site readiness"><p>{profile?.version ? `Site profile v${profile.version.version} · ${profile.current ? "Current" : "Stale"}` : "No site profile yet"}</p>
          <p className="text-[10px] text-muted-foreground">{readiness?.siteDataState ?? "Unknown site readiness"}{readiness?.databaseMode === "DEMO" && " · Demo storage"}</p>
          {profile?.version && <p className="text-[10px] text-muted-foreground">Elevation: {profile.version.relief.minElevation.sourceKind === "UNKNOWN" ? "Unknown" : `${profile.version.relief.minElevation.value.value} m`}</p>}
          {profile?.errorCode && <p role="alert">Profile: {profile.errorCode.replaceAll("_", " ").toLowerCase()}</p>}
        </div>
        <Button size="sm" variant="secondary" onClick={refresh} disabled={busy || !!profile && ["QUEUED", "RUNNING"].includes(profile.refreshState)}>
          {profile && ["QUEUED", "RUNNING"].includes(profile.refreshState) ? "Creating profile…" : "Refresh site"}
        </Button>
      </div>
    </div>
    <div className="min-h-0 flex-1 space-y-3 overflow-y-auto p-3">
      {before !== null && conversation && <Button size="sm" variant="ghost" disabled={busy} onClick={() => void execute(async () => {
        const result = await api.get<Messages>(`${base}/conversations/${conversation.id}/messages?before=${before}`);
        setMessages(current => [...result.messages, ...current]); setBefore(result.nextBefore);
      })}>Load older messages</Button>}
      {messages.map(message => <article key={message.id} className="space-y-1 rounded border border-border bg-muted/30 p-3">
        <p className="text-[10px] text-muted-foreground">{message.role === "USER" ? "You" : message.role === "ASSISTANT" ? "Assistant" : "Project event"}</p>
        {message.parts.map((part, i) => part.kind === "PROPOSAL" ? <ProposalReview key={i} projectId={projectId} versionId={part.proposalVersionId} /> : part.kind === "EVIDENCE" ? <div key={i}>{part.evidenceIds.map(id => <button key={id} className="block underline" onClick={() => void execute(async () => {
          setSource(await api.get(`${base}/site-evidence/${id}`));
        })}>View source {id}</button>)}</div> : <div key={i} className="whitespace-pre-wrap break-words">{part.kind === "TEXT" || part.kind === "QUESTION" ? part.text : part.kind === "ATTACHMENT" ? `Attachment: ${part.attachmentId}` : `Assumption: ${part.assumptionVersionId}`}
          {part.kind === "QUESTION" && part.options.map(option => <Button key={option} size="sm" variant="secondary" onClick={() => setInput(option)}>{option}</Button>)}
        </div>)}
        {!!message.context.selection?.length && <p className="text-[10px] text-muted-foreground">Captured: {message.context.selection.map(o => o.objectId).join(", ")} · revision {message.context.modelRevisionId}</p>}
        {message.context.editorDirty && <p className="text-[10px] text-muted-foreground">Sent with unsaved editor changes; references point to the saved revision.</p>}
        {message.run && <p className="text-[10px] text-muted-foreground">{message.run.errorCode === "ORCHESTRATION_NOT_ENABLED" ? "Saved before AI processing was enabled" : message.run.progress ?? `Run: ${message.run.status}`}</p>}
        {message.run?.capabilities?.map((capability, i) => <p key={i} className="text-[10px] text-muted-foreground">{capability.assetType}: discussion {capability.discussionSupport.toLowerCase()} · planning {capability.planningSupport.toLowerCase()} · generation {capability.generationSupport.toLowerCase()} · analysis {capability.engineeringAnalysisSupport.toLowerCase()}</p>)}
        {message.run && (["FAILED", "INTERRUPTED"].includes(message.run.status) || message.run.errorCode === "ORCHESTRATION_NOT_ENABLED") && <div role="alert"><p>{message.run.errorCode === "ORCHESTRATION_NOT_ENABLED" ? "Process this saved message using its original context." : `${message.run.errorCode?.replaceAll("_", " ")}. Your message is saved.`}</p><Button size="sm" variant="secondary" disabled={busy || !!activeRun} onClick={() => {
          const runId = message.run!.id; const retryId = crypto.randomUUID();
          void execute(async () => { await api.post(`${base}/assistant/runs/${runId}/retry`, { clientRequestId: retryId }); if (conversation) await loadMessages(conversation.id); });
        }}>Retry assistant</Button></div>}
      </article>)}
      {!messages.length && <p className="text-muted-foreground">Describe your site or civil project. Chat alone never accepts a requirement.</p>}
      {source && <aside aria-label="Evidence source" className="rounded border border-border p-2"><p>{source.evidence.sourceType} · {source.evidence.status}</p><p>Retrieved: {source.evidence.retrievedAt}</p>{source.evidence.source.reason && <p>{source.evidence.source.reason}</p>}{source.evidence.source.sourceUrl && /^https?:\/\//.test(source.evidence.source.sourceUrl) && <a className="underline" href={source.evidence.source.sourceUrl} target="_blank" rel="noreferrer">Open source</a>}<Button size="sm" variant="ghost" onClick={() => setSource(null)}>Close source</Button></aside>}
      <details className="rounded border border-border p-2" open={memory.some(item => item.status === "PROPOSED")}>
        <summary className="cursor-pointer font-medium">Project memory ({memory.filter(item => item.status === "ACCEPTED").length} accepted)</summary>
        <div className="mt-2 space-y-2">
          {memory.filter(item => ["PROPOSED", "ACCEPTED"].includes(item.status)).map(item => <article key={item.versionId} aria-label={`${item.status.toLowerCase()} memory`} className="rounded border border-border p-2">
            <p className="text-[10px] text-muted-foreground">{item.content.kind} · {item.status} · {item.assetId ? `Asset ${item.assetId}` : "Project"}</p>
            <p className="mt-1 break-words">{memoryLabel(item)}</p>
            {item.status === "PROPOSED" && <div className="mt-2 flex gap-2"><Button size="sm" disabled={busy} onClick={() => decide(item, "accept")}>Accept</Button><Button size="sm" variant="secondary" disabled={busy} onClick={() => decide(item, "reject")}>Reject</Button></div>}
          </article>)}
          <p className="text-[10px] text-muted-foreground">Add a proposed project requirement, then review it before acceptance.</p>
          <input aria-label="Requirement key" className="w-full rounded border border-border bg-background p-2" placeholder="e.g. carriageway.width" value={memoryKey} onChange={e => setMemoryKey(e.target.value)} />
          <div className="flex gap-2"><input aria-label="Requirement value" className="min-w-0 flex-1 rounded border border-border bg-background p-2" placeholder="Value" value={memoryValue} onChange={e => setMemoryValue(e.target.value)} /><input aria-label="Requirement unit" className="w-16 rounded border border-border bg-background p-2" placeholder="Unit" value={memoryUnit} onChange={e => setMemoryUnit(e.target.value)} /></div>
          <Button size="sm" variant="secondary" disabled={busy || !memoryKey.trim() || !memoryValue.trim()} onClick={proposeMemory}>Propose requirement</Button>
        </div>
      </details>
    </div>
    <div className="space-y-2 border-t border-border p-3">
      {error && <div role="alert" className="space-y-2 text-destructive"><p>{error}</p><Button size="sm" variant="secondary" disabled={busy} onClick={() => { if (frozenSend.current) send(); else if (retry.current) void execute(retry.current); }}>Retry</Button></div>}
      {error && pendingSend && <Button size="sm" variant="ghost" disabled={busy} onClick={() => {
        frozenSend.current = null; frozenSite.current = null; setPendingSend(false); setInput("");
        if (conversation) void execute(() => loadMessages(conversation.id));
      }}>Start a new message</Button>}
      <textarea aria-label="Project message" className="min-h-20 w-full resize-none rounded border border-border bg-background p-2" placeholder="Discuss the selected site or objects…" value={input} disabled={pendingSend} onChange={e => setInput(e.target.value)} />
      <Button className="w-full" size="sm" disabled={busy || !!activeRun || pendingSend || !conversation || !input.trim()} onClick={send}>{busy ? "Saving…" : "Send message"}</Button>
    </div>
  </section>;
}

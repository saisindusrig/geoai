"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import ProposalReview from "./ProposalReview";
import type { ConversationView, MessageView, MessageInput, MemoryView, MemoryInput, ProfileView, ReadinessView, SelectionVersion } from "@/lib/generated/stage1";

type Props = { projectId: number; selectedIds: string[]; revisionId: number | null; dirty: boolean; siteGeometry?: import("@/lib/types").GeoJSONGeometry | null };
type Messages = { messages: MessageView[]; nextBefore: number | null };

function activeProgress(messages: MessageView[]) {
  return messages.map(message => message.run?.progress ?? message.run?.status ?? "").join("|");
}

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
  const [offlineDemo, setOfflineDemo] = useState<{ enabled: boolean; label: string; example: string; chatAvailable?: boolean; chatProvider?: string | null } | null>(null);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pendingSend, setPendingSend] = useState(false);
  const [memoryKey, setMemoryKey] = useState("");
  const [memoryValue, setMemoryValue] = useState("");
  const [memoryUnit, setMemoryUnit] = useState("");
  const [source, setSource] = useState<{ evidence: { sourceType: string; status: string; retrievedAt: string; source: { kind: string; sourceUrl?: string; reason?: string } } } | null>(null);
  const composer = useRef<HTMLTextAreaElement | null>(null);
  const transcript = useRef<HTMLDivElement | null>(null);
  const followLatest = useRef(true);
  const submitting = useRef(false);
  const focusAfterSend = useRef(false);
  const latestMessage = messages.at(-1)?.id;
  const progressKey = activeProgress(messages);
  useEffect(() => {
    if (composer.current) {
      composer.current.style.height = "auto";
      composer.current.style.height = `${Math.min(180, Math.max(76, composer.current.scrollHeight))}px`;
    }
  }, [input]);
  useEffect(() => {
    if (followLatest.current && transcript.current) transcript.current.scrollTop = transcript.current.scrollHeight;
  }, [latestMessage, progressKey, pendingSend, error]);
  const retry = useRef<(() => Promise<void>) | null>(null);
  const frozenSend = useRef<MessageInput | null>(null);
  const frozenSite = useRef<Props["siteGeometry"]>(null);
  const siteKey = JSON.stringify(siteGeometry ?? null);
  const activeRun = messages.find(m => m.run && ["QUEUED", "CLASSIFYING", "READING_CONTEXT", "RUNNING", "PROPOSING", "VALIDATING"].includes(m.run.status))?.run;
  const activeProposal = messages.flatMap(m => m.parts).filter(p => p.kind === "PROPOSAL").at(-1)?.proposalVersionId ?? null;
  const mounted = useRef(true);
  useEffect(() => {
    if (focusAfterSend.current && !busy && !pendingSend && !activeRun) {
      composer.current?.focus(); focusAfterSend.current = false;
    }
  }, [busy, pendingSend, activeRun]);

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
    const demo = await api.get<{ enabled: boolean; label: string; example: string; chatAvailable?: boolean; chatProvider?: string | null }>(`${base}/assistant/offline-platform`);
    if (mounted.current) setOfflineDemo(demo);
    const profiles = await api.get<{ profiles: ProfileView[] }>(`${base}/site-profiles`);
    if (profiles.profiles[0]) await loadProfile(profiles.profiles[0].id);
  }, [base, loadMemory, loadMessages, loadProfile]);

  const execute = useCallback(async (action: () => Promise<void>) => {
    if (submitting.current) return;
    submitting.current = true; retry.current = action; setBusy(true); setError(null);
    try { await action(); if (mounted.current) retry.current = null; }
    catch (e) { if (mounted.current) setError(e instanceof Error ? e.message : "Could not save. Please retry."); }
    finally { submitting.current = false; if (mounted.current) setBusy(false); }
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
    if (!conversation || busy || submitting.current || activeRun || (!input.trim() && !frozenSend.current)) return;
    // Capture synchronously at click time; a failed submission retries this exact body.
    const body: MessageInput = frozenSend.current ?? {
      clientRequestId: crypto.randomUUID(), parts: [{ kind: "TEXT", text: input.trim() }],
      context: { selectedObjectIds: [...selectedIds], modelRevisionId: revisionId === null ? null : String(revisionId),
        siteSelectionVersionId: profile?.version?.selectionVersion.id ?? null,
        siteProfileVersionId: profile?.version?.id ?? null, scenarioId: null, proposalVersionId: activeProposal, editorDirty: dirty },
    };
    if (!frozenSend.current) frozenSite.current = siteGeometry ? structuredClone(siteGeometry) : null;
    frozenSend.current = body; followLatest.current = true; setPendingSend(true);
    void execute(async () => {
      if (frozenSite.current && body.context.siteProfileVersionId) {
        // Read the saved version instead of creating a new selection on every send.
        // Validate the captured geometry on retry too; never silently rebind context.
        if (!profile?.current || !profile.version) throw new Error("Site changed. Save the boundary and Refresh site before sending a new request.");
        const saved = await api.get<SelectionVersion>(`${base}/site-selections/${profile.selectionId}/versions/${profile.version.selectionVersion.version}`);
        if (saved.id !== body.context.siteSelectionVersionId || saved.canonicalGeometry.type !== frozenSite.current.type || JSON.stringify(saved.canonicalGeometry.coordinates) !== JSON.stringify(frozenSite.current.coordinates)) {
          throw new Error("Site changed. Save the boundary and Refresh site before sending a new request.");
        }
      }
      await api.post(`${base}/conversations/${conversation.id}/messages`, body);
      await loadMessages(conversation.id);
      frozenSend.current = null; focusAfterSend.current = true; setPendingSend(false); setInput("");
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

  return <section aria-label="Project assistant" className="flex h-full min-h-0 flex-col text-sm">
    <header className="shrink-0 space-y-3 border-b border-border p-4">
      <div><h2 className="font-semibold">GeoAI Assistant</h2><p className="mt-1 text-xs text-muted-foreground">{offlineDemo?.enabled ? "Offline platform demo" : offlineDemo?.chatAvailable ? "AI provider configured" : "AI provider unavailable"}</p></div>
      <div className="flex items-center justify-between gap-2">
        <div aria-label="Site readiness" className="text-xs"><p>{profile?.version ? `Site profile v${profile.version.version} · ${profile.current ? "Current" : "Stale"}` : "No site profile yet"}</p>
          {profile?.errorCode && <p role="alert">Profile: {profile.errorCode.replaceAll("_", " ").toLowerCase()}</p>}
        </div>
        <Button size="sm" variant="secondary" onClick={refresh} disabled={busy || !!profile && ["QUEUED", "RUNNING"].includes(profile.refreshState)}>
          {profile && ["QUEUED", "RUNNING"].includes(profile.refreshState) ? "Creating profile…" : "Refresh site"}
        </Button>
      </div>
      <details className="rounded-lg border border-border px-3 py-2 text-xs">
        <summary className="cursor-pointer font-medium">Site context · {selectedIds.length} selected</summary>
        <div className="mt-2 space-y-2 text-muted-foreground">
          <div aria-label="Selected object context" className="break-words">{selectedIds.length ? `Selected: ${selectedIds.join(", ")}` : "No objects selected"}{revisionId !== null && ` · revision ${revisionId}`}{dirty && " · unsaved edits"}</div>
          <p>{readiness?.siteDataState ?? "Unknown site readiness"}{readiness?.databaseMode === "DEMO" && " · Demo storage"}</p>
          {profile?.version && <p>Elevation: {profile.version.relief.minElevation.sourceKind === "UNKNOWN" ? "Unknown" : `${profile.version.relief.minElevation.value.value} m`}</p>}
          <p>Chat never accepts requirements or approves a build. Review and approval are separate actions.</p>
        </div>
      </details>
      {offlineDemo?.enabled && messages.length > 0 && <div className="flex items-center justify-between gap-2 text-xs"><span className="text-muted-foreground">Fixed template · no inference</span><Button size="sm" variant="secondary" disabled={busy || pendingSend || !!activeRun} onClick={() => { setInput(offlineDemo.example); composer.current?.focus(); }}>Use platform example</Button></div>}
    </header>
    <div ref={transcript} role="log" aria-label="Conversation messages" aria-live="polite" aria-relevant="additions text" onScroll={() => {
      const node = transcript.current; if (node) followLatest.current = node.scrollHeight - node.scrollTop - node.clientHeight < 48;
    }} className="min-h-0 flex-1 space-y-5 overflow-y-auto overscroll-contain p-4">
      {before !== null && conversation && <Button size="sm" variant="ghost" disabled={busy} onClick={() => void execute(async () => {
        const result = await api.get<Messages>(`${base}/conversations/${conversation.id}/messages?before=${before}`);
        setMessages(current => [...result.messages, ...current]); setBefore(result.nextBefore);
      })}>Load older messages</Button>}
      {messages.map(message => <article key={message.id} aria-label={`${message.role === "USER" ? "Your" : "Assistant"} message`} className={`space-y-2 rounded-xl p-3 leading-relaxed ${message.role === "USER" ? "ml-6 border border-border bg-muted/60" : "mr-2 bg-background/40"}`}>
        <p className="text-[10px] text-muted-foreground">{message.role === "USER" ? "You" : message.role === "ASSISTANT" ? "Assistant" : "Project event"}</p>
        {message.createdAt && <time className="text-[10px] text-muted-foreground" dateTime={message.createdAt}>{new Date(message.createdAt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</time>}
        {message.parts.map((part, i) => part.kind === "PROPOSAL" ? <ProposalReview key={i} projectId={projectId} versionId={part.proposalVersionId} dirty={dirty} /> : part.kind === "EVIDENCE" ? <details key={i} className="text-xs text-muted-foreground"><summary className="cursor-pointer">Sources ({part.evidenceIds.length})</summary>{part.evidenceIds.map((id, index) => <button key={id} className="block underline" onClick={() => void execute(async () => {
          setSource(await api.get(`${base}/site-evidence/${id}`));
        })}>View source {index + 1}</button>)}</details> : <div key={i} className="whitespace-pre-wrap break-words">{part.kind === "TEXT" || part.kind === "QUESTION" ? part.text : part.kind === "ATTACHMENT" ? `Attachment: ${part.attachmentId}` : `Assumption: ${part.assumptionVersionId}`}
          {part.kind === "QUESTION" && part.options.map(option => <Button key={option} size="sm" variant="secondary" onClick={() => setInput(option)}>{option}</Button>)}
        </div>)}
        {!!message.context.selection?.length && <p className="text-[10px] text-muted-foreground">Captured: {message.context.selection.map(o => o.objectId).join(", ")} · revision {message.context.modelRevisionId}</p>}
        {message.context.editorDirty && <p className="text-[10px] text-muted-foreground">Sent with unsaved editor changes; references point to the saved revision.</p>}
        {message.run && <p className="text-[10px] text-muted-foreground">{message.run.errorCode === "ORCHESTRATION_NOT_ENABLED" ? "Saved before AI processing was enabled" : message.run.progress ?? `Run: ${message.run.status}`}</p>}
        {message.run?.capabilities?.length ? <details className="text-xs text-muted-foreground"><summary className="cursor-pointer">Capability details</summary>{message.run.capabilities.map((capability, i) => <p key={i} className="text-[10px] text-muted-foreground">{capability.assetType}: discussion {capability.discussionSupport.toLowerCase()} · planning {capability.planningSupport.toLowerCase()} · generation {capability.generationSupport.toLowerCase()} · analysis {capability.engineeringAnalysisSupport.toLowerCase()}</p>)}</details> : null}
        {message.run?.errorCode && ["SITE_PROFILE_REQUIRED", "STALE_SITE_PROFILE"].includes(message.run.errorCode) && <div role="alert">Save the current site boundary and Refresh site, then send a new request. No model was generated.</div>}
        {message.run?.errorCode === "OFFLINE_PLATFORM_SITE_UNSUPPORTED" && <div role="alert">The fixed 5 m × 3 m platform does not fit this saved site context. Choose a suitable area and Refresh site. The template has not been resized; no model was generated.</div>}
        {message.run?.errorCode === "AI_PROVIDER_UNAVAILABLE" && <div role="alert">General AI chat is unavailable in mock mode. Your message is saved. Use the supported offline platform example, or review provider setup in <a href="/settings/api-keys" className="underline">Settings</a>. No inference was sent.</div>}
        {message.run?.errorCode === "CONTEXT_REFRESH_REQUIRED" && <div role="alert">Saved model context changed. Refresh your selection and send a new message. Your original message remains saved.</div>}
        {message.run && !["CONTEXT_REFRESH_REQUIRED", "AI_PROVIDER_UNAVAILABLE"].includes(message.run.errorCode ?? "") && (["FAILED", "INTERRUPTED"].includes(message.run.status) || message.run.errorCode === "ORCHESTRATION_NOT_ENABLED") && <div role="alert"><p>{message.run.errorCode === "ORCHESTRATION_NOT_ENABLED" ? "Process this saved message using its original context." : `${message.run.errorCode?.replaceAll("_", " ")}. Your message is saved.`}</p><Button size="sm" variant="secondary" disabled={busy || !!activeRun} onClick={() => {
          const runId = message.run!.id; const retryId = crypto.randomUUID();
          void execute(async () => { await api.post(`${base}/assistant/runs/${runId}/retry`, { clientRequestId: retryId }); if (conversation) await loadMessages(conversation.id); });
        }}>Retry assistant</Button></div>}
      </article>)}
      {!messages.length && <div aria-label="Chat empty state" className="space-y-3 py-4"><h3 className="font-medium">Plan your project here</h3><p className="text-muted-foreground">Save a site boundary and Refresh site to attach current project context.</p></div>}
      {offlineDemo?.enabled && !messages.length && <aside aria-label="Offline demo availability" className="space-y-2 rounded-xl border border-border p-3 text-xs"><p className="font-medium">{offlineDemo.label}</p><p className="text-muted-foreground">Only the fixed 5 × 3 m platform template is available without inference. Free-form AI chat is unavailable. Concept only; review and approval required.</p><Button size="sm" variant="secondary" disabled={busy || pendingSend || !!activeRun} onClick={() => { setInput(offlineDemo.example); composer.current?.focus(); }}>Use platform example</Button></aside>}
      {!offlineDemo?.enabled && !offlineDemo?.chatAvailable && <p className="text-xs text-muted-foreground">General AI chat needs a connected provider. <a href="/settings/api-keys" className="underline">Review provider setup</a>; this does not enable or authorize paid inference.</p>}
      {pendingSend && <div role="status" aria-label="Message submission" className="text-xs text-muted-foreground">{error ? "Message not confirmed. Retry keeps the same request and context." : "Saving your message…"}</div>}
      {activeRun && <p role="status" className="text-xs text-muted-foreground">{activeRun.progress ?? "Processing saved message…"}</p>}
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
    <div className="shrink-0 space-y-2 border-t border-border p-4">
      {error && <div role="alert" className="space-y-2 text-destructive"><p>{error}</p><Button size="sm" variant="secondary" disabled={busy} onClick={() => { if (frozenSend.current) send(); else if (retry.current) void execute(retry.current); }}>Retry</Button></div>}
      {error && pendingSend && <Button size="sm" variant="ghost" disabled={busy} onClick={() => {
        frozenSend.current = null; frozenSite.current = null; setPendingSend(false); setInput("");
        if (conversation) void execute(() => loadMessages(conversation.id));
      }}>Start a new message</Button>}
      <textarea ref={composer} aria-label="Project message" aria-describedby="composer-help" rows={3} className="min-h-[76px] max-h-[180px] w-full resize-none rounded-xl border border-border bg-background p-3 text-sm leading-relaxed" placeholder="Message GeoAI…" value={input} disabled={pendingSend || busy || !!activeRun} onChange={e => setInput(e.target.value)} onKeyDown={e => {
        if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) { e.preventDefault(); send(); }
      }} />
      <p id="composer-help" className="text-[10px] text-muted-foreground">Enter to send · Shift+Enter for a new line</p>
      <Button className="w-full" size="sm" disabled={busy || !!activeRun || pendingSend || !conversation || !input.trim()} onClick={send}>{busy ? "Saving…" : "Send message"}</Button>
    </div>
  </section>;
}

"use client";

import { useEffect, useRef, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { Sparkles, ArrowUp, X, Maximize2, Minimize2 } from "lucide-react";
import { api } from "@/lib/api";
import { AssistantRequestError, sendAssistant, type AssistantAvailability, type AssistantContext, type AssistantEvent, type AssistantTask, type ToolResult } from "@/lib/site-assistant";

import {waitForWorkspace,type WorkspaceCommand,type WorkspaceOutcome} from "@/lib/workspace-assistant";
import AssistantMarkdown from "./AssistantMarkdown";
import {isPrimitive,type PrimitiveStatus} from '@/lib/primitive-status';
import { activityLabel, availabilityReason, availabilityLabel, canSendAssistant, toolLabels } from "@/lib/assistant-presentation";

const FLASH = "zai-org/GLM-5.3-Flash";
const emptyContext: AssistantContext = { project_id: null, revision_id: null, selected_ids: [], dirty: false };

export default function SiteAssistant() {
  const path = usePathname(); const router = useRouter();
  const projectId = Number(path?.match(/^\/projects\/(\d+)/)?.[1]) || null;
  const [editorContext, setEditorContext] = useState<AssistantContext>(emptyContext);
  const context = editorContext.project_id === projectId ? editorContext : { ...emptyContext, project_id: projectId };
  const [open, setOpen] = useState(false), [input, setInput] = useState(""), [model, setModel] = useState(FLASH);
  const [tasks, setTasks] = useState<AssistantTask[]>([]), [events, setEvents] = useState<AssistantEvent[]>([]);
  const [error, setError] = useState<string | null>(null), [busy, setBusy] = useState(false);
  const [status, setStatus] = useState<AssistantAvailability | null>(null);
  const [savedContext, setSavedContext] = useState<unknown>(null);
  const [legacy, setLegacy] = useState<unknown>(null);
  const [actionStatus, setActionStatus] = useState<string | null>(null);
  const [primitiveStates,setPrimitiveStates]=useState<Record<string,PrimitiveStatus>>({});
  const [currentPrimitive,setCurrentPrimitive]=useState<PrimitiveStatus|null>(null);
  useEffect(()=>{const receive=(event:Event)=>{const value=(event as CustomEvent<PrimitiveStatus>).detail;setPrimitiveStates(old=>({...old,[value.actionId]:value}));setCurrentPrimitive(value);setActionStatus(value.message);setPreviewPending(value.phase==='preview_pending');};window.addEventListener('geoai:primitive-status',receive);return()=>window.removeEventListener('geoai:primitive-status',receive);},[]);
  const [workspaceOutcomes,setWorkspaceOutcomes]=useState<Record<string,WorkspaceOutcome>>({});
  const [workspaceProgress,setWorkspaceProgress]=useState<string|null>(null);
  const dispatched=useRef(new Set<string>()),queuedWorkspace=useRef<WorkspaceCommand|null>(null);
  useEffect(()=>{
    const c=queuedWorkspace.current;
    if(c&&c.projectId===editorContext.project_id&&c.revisionId===editorContext.revision_id&&path===`/projects/${c.projectId}/workspace`){queuedWorkspace.current=null;window.dispatchEvent(new CustomEvent('geoai:workspace-command',{detail:c}));}
  },[path,editorContext]);
  const runWorkspace=async(commands:WorkspaceCommand[],taskId:string)=>{
    for(const prepared of commands.slice(0,3)){
      const command={...prepared,expiresAt:Date.now()+20000};
      const key=`${taskId}:${command.actionId}`;if(dispatched.current.has(key))continue;dispatched.current.add(key);
      setWorkspaceProgress(({open_project:'Finding the project',select_components:'Selecting the component',focus_components:'Focusing the camera',show_saved_result:'Opening the saved result',switch_workspace_view:'Switching the view',prepare_primitive_preview:'Preparing the temporary column',prepare_beam_preview:'Preparing the temporary beam',cancel_primitive_preview:'Cancelling the temporary proposal'})[command.operation]);
      let result:WorkspaceOutcome;
      try{
        if(context.dirty&&command.operation!=='cancel_primitive_preview')throw Error('Resolve the unsaved editor draft before controlling the workspace.');
        const verified=await api.post<WorkspaceCommand>('/api/assistant/workspace/validate',{...context,page:path,name:command.validation.name,arguments:command.validation.arguments,action_id:command.actionId});
        if(verified.actionId!==command.actionId||verified.documentHash!==command.documentHash)throw Error('Workspace source validation did not match.');
        const confirmation=waitForWorkspace(command);
        if(path===`/projects/${command.projectId}/workspace`&&context.revision_id===command.revisionId)window.dispatchEvent(new CustomEvent('geoai:workspace-command',{detail:command}));
        else {queuedWorkspace.current=command;router.push(`/projects/${command.projectId}/workspace`);}
        result=await confirmation;
        if(queuedWorkspace.current?.actionId===command.actionId)queuedWorkspace.current=null;
      }catch(e){result={actionId:command.actionId,ok:false,message:e instanceof Error?e.message:'Workspace action failed validation.'};}
      setWorkspaceOutcomes(old=>({...old,[key]:result}));setActionStatus(result.message);
      if(isPrimitive(command)&&!result.ok){const rejected:PrimitiveStatus={actionId:command.actionId,projectId:command.projectId,phase:'rejected_stale',message:`Rejected or stale · ${result.message}`};setPrimitiveStates(old=>({...old,[command.actionId]:rejected}));setCurrentPrimitive(rejected);setPreviewPending(false);}
      try{await api.post('/api/assistant/workspace/outcome',{task_id:taskId,action_id:command.actionId,ok:result.ok,message:result.message.slice(0,500)});}catch{setActionStatus(result.message+' The confirmation could not be saved to assistant history. No replay was attempted.');}
      if(!result.ok)break;
    }
    setWorkspaceProgress(null);
  };
  const [stopped, setStopped] = useState(false);
  const [retryAvailable, setRetryAvailable] = useState(false);
  const [outgoing, setOutgoing] = useState<string | null>(null);
  const [width, setWidth] = useState(480);
  const [newMessages, setNewMessages] = useState(false);
  const [cancelled, setCancelled] = useState<string[]>([]);
  const [previewPending, setPreviewPending] = useState(false);
  const historyRef = useRef<HTMLDivElement>(null), follow = useRef(true);
  const resizeStart = useRef<{x:number;width:number}|null>(null);
  const awaitingInspector = useRef<{tab:string;label:string}|null>(null);
  const opening = useRef<{href:string;label:string;projectId?:number}|null>(null);
  useEffect(() => {
    if (opening.current?.href === path && (!opening.current.projectId || opening.current.projectId === editorContext.project_id)) {
      setActionStatus(`Opened ${opening.current.label}. No changes were saved.`);
      opening.current = null;
    }
  }, [path, editorContext.project_id]);
  useEffect(() => {
    const pane = historyRef.current;
    if (!pane) return;
    if (follow.current) pane.scrollTop = pane.scrollHeight;
    else setNewMessages(true);
  }, [tasks, events, outgoing,workspaceOutcomes]);
  const newest = () => { follow.current = true; setNewMessages(false); const pane = historyRef.current; if (pane) pane.scrollTop = pane.scrollHeight; };

  const controller = useRef<AbortController | null>(null), sending = useRef(false);
  const frozen = useRef<object | null>(null), activeScope = useRef(projectId);
  const pendingNavigation = useRef<ToolResult | null>(null);
  useEffect(() => { activeScope.current = projectId; }, [projectId]);
  useEffect(() => {
    if (!open) return;
    const escape = (event: KeyboardEvent) => {
      if (event.key === "Escape" && document.activeElement === document.body) setOpen(false);
    };
    window.addEventListener("keydown", escape);
    return () => window.removeEventListener("keydown", escape);
  }, [open]);
  useEffect(() => {
    const acknowledge = (event: Event) => {
      const pending = awaitingInspector.current;
      if (pending && (event as CustomEvent<string>).detail === pending.tab) {
        setActionStatus(`Opened ${pending.label}. No calculation was started or model saved.`);
        awaitingInspector.current = null;
      }
    };
    window.addEventListener("geoai:inspector-view", acknowledge);
    return () => window.removeEventListener("geoai:inspector-view", acknowledge);
  }, []);
  useEffect(() => {
    const pending = pendingNavigation.current;
    if (!pending || pending.href !== path || pending.projectId !== editorContext.project_id) return;
    pendingNavigation.current = null;
    if (pending.destination === "inspect") window.dispatchEvent(new CustomEvent("geoai:inspect-component", { detail: pending }));
    else if (["analysis", "results", "cad"].includes(pending.destination || "")) window.dispatchEvent(new Event("geoai:show-analysis"));
  }, [path, editorContext]);
  useEffect(() => {
    const update = (e: Event) => setEditorContext((e as CustomEvent<AssistantContext>).detail);
    const show = () => setOpen(true);
    const action = (e: Event) => { const message = (e as CustomEvent<string>).detail; setActionStatus(message); setPreviewPending(message.startsWith("Visual preview shown")); };
    window.addEventListener("geoai:assistant-context", update);
    window.addEventListener("geoai:open-site-assistant", show);
    window.addEventListener("geoai:open-copilot", show);
    window.addEventListener("geoai:assistant-preview-status", action);
    return () => { window.removeEventListener("geoai:assistant-context", update); window.removeEventListener("geoai:open-site-assistant", show); window.removeEventListener("geoai:open-copilot", show); window.removeEventListener("geoai:assistant-preview-status", action); controller.current?.abort(); };
  }, []);
  useEffect(() => {
    if (!open) return;
    let active = true;
    void Promise.all([api.get<AssistantAvailability>("/api/assistant/status"), api.get<{ tasks: AssistantTask[] }>("/api/assistant/history")])
      .then(([s, h]) => { if (active) { setStatus(s); if (!sending.current) { setTasks(h.tasks); setError(null); } } })
      .catch(e => { if (active) { setStatus(null); setTasks([]); setError(e instanceof Error ? e.message : "Assistant history unavailable."); } });
    return () => { active = false; };
  }, [open, projectId]);
  useEffect(()=>{if(!open)return;let active=true;void api.get<{outcomes:(WorkspaceOutcome&{taskId:string})[]}>('/api/assistant/workspace/history').then(data=>{if(active)setWorkspaceOutcomes(old=>({...Object.fromEntries((data.outcomes||[]).map(o=>[`${o.taskId}:${o.actionId}`,o])),...old}));}).catch(()=>{});return()=>{active=false;};},[open]);
  const refreshAvailability = async () => {
    try { setStatus(await api.get<AssistantAvailability>("/api/assistant/status")); }
    catch (e) { setStatus({ enabled: false, state: "DISABLED", message: e instanceof Error ? e.message : "Availability could not be checked. Retry manually." }); }
  };
  const refreshHistory = async () => {
    try { const history = await api.get<{ tasks: AssistantTask[] }>("/api/assistant/history"); setTasks(history.tasks); }
    catch (e) { setError(e instanceof Error ? e.message : "History unavailable. Retry manually."); }
  };
  const request = async (retry = false) => {
    if (sending.current || workspaceProgress || !canSendAssistant(status)) return;
    setCurrentPrimitive(null);
    const scope = projectId;
    const body = retry && frozen.current ? frozen.current : { ...context, page: path, request_id: crypto.randomUUID(), message: input.trim(), model };
    if (!retry && !input.trim()) return;
    frozen.current = body; setRetryAvailable(true); setOutgoing((body as {message:string}).message); setStopped(false); follow.current = true; setActionStatus(null); setCancelled(old => old.filter(id => !id.startsWith("active:"))); sending.current = true; setBusy(true); setError(null); setEvents([]);
    controller.current = new AbortController(); const timeout = window.setTimeout(() => controller.current?.abort(), 115000);
    try {
      await sendAssistant(body, event => {
        if (activeScope.current !== scope) return;
        if (event.type === "task" && event.task) {
          const task = event.task;
          setTasks(old => [...old.filter(t => t.id !== task.id), task]); setEvents([]); setOutgoing(null); setRetryAvailable(false);
          if (task.status === "SUCCEEDED") { setInput(""); frozen.current = null; void runWorkspace(task.events.filter(e=>e.type==="tool_result"&&e.ok&&e.result?.kind==="workspace_action").map(e=>e.result as WorkspaceCommand),task.id); }
          else { setError(task.error || "The response did not finish. Check history before trying again."); frozen.current = null; }
        } else {
          if (event.type === "tool_result" && event.ok && event.result?.kind === "position_preview") setPreviewPending(true);
          if (event.type === "error" && event.availability) setStatus(old => ({ ...old, enabled: false, state: event.availability, code: event.code, message: event.message || "Inference unavailable. Retry manually." }));
          setEvents(old => [...old, event]);
        }
      }, controller.current.signal);
    } catch (e) { if (activeScope.current === scope) {
      setError(controller.current?.signal.aborted ? "Response stopped or timed out. Usage may be unknown and remains reserved. Refresh history or Retry manually; no automatic request is sent." : e instanceof Error ? e.message : "Inference failed. Retry manually.");
      if (e instanceof AssistantRequestError) setStatus(old => ({ ...old, enabled: false, state: e.availability, code: e.code, message: e.message }));
    } }
    finally { clearTimeout(timeout); sending.current = false; setBusy(false); }
  };
  const navigate = async (result: ToolResult) => {
    let projectName = result.projectName;
    const allowed = new Set(["/dashboard", "/diagnostics", "/settings", ...(projectId ? ["workspace", "estimate", "report"].map(s => `/projects/${projectId}/${s}`) : [])]);
    const target = result.href?.match(/^\/projects\/(\d+)\/(workspace|estimate|report)$/);
    if (target && Number(target[1]) === result.projectId) {
      try { const project = await api.get<{ name?: string }>(`/api/projects/${target[1]}`); projectName = project.name; allowed.add(result.href!); }
      catch { setActionStatus("Navigation rejected: project is no longer accessible."); return; }
    }
    if (!result.href || !allowed.has(result.href)) { setActionStatus("Navigation rejected: destination is outside the current allowed context."); return; }
    const label = projectName ? `${projectName} · ${result.destination}` : result.destination || "the tool";
    setActionStatus(`Opening ${label}…`);
    if (result.href === path && ["inspect","analysis","results","cad"].includes(result.destination || "")) {
      const tab = result.destination === "inspect" ? "properties" : "analysis";
      awaitingInspector.current = {tab,label};
      if (document.getElementById(`inspector-tab-${tab}`)?.getAttribute("aria-selected") === "true") {
        setActionStatus(`Opened ${label}. No calculation was started or model saved.`); awaitingInspector.current = null;
      }
      if (tab === "properties") window.dispatchEvent(new CustomEvent("geoai:inspect-component",{detail:result}));
      else window.dispatchEvent(new Event("geoai:show-analysis"));
    } else if (result.href === path) setActionStatus(`Already viewing ${label}. No changes were saved.`);
    else { pendingNavigation.current = result; opening.current={href:result.href,label,projectId:result.projectId}; router.push(result.href); }

  };
  const tool = (event: AssistantEvent, key: number | string) => {
    const result = event.result, identity = `${key}:${result?.projectId}:${result?.revisionId}:${result?.componentId}`;
    const dismissed = cancelled.includes(identity);
    const receipt=result?.kind==='workspace_action'?result as WorkspaceCommand:null;
    const receiptOutcome=receipt?workspaceOutcomes[`${String(key).split(':')[0]}:${receipt.actionId}`]:undefined;
    const primitive=receipt&&isPrimitive(receipt),state=receipt?primitiveStates[receipt.actionId]:undefined;
    const activePreview=state?.phase==='preview_pending'&&currentPrimitive?.actionId===state.actionId&&receipt?.projectId===projectId&&receipt?.revisionId===editorContext.revision_id;
    return <div key={key} className="assistant-action">
      <p className="font-medium">{primitive ? (state&&(state.phase!=='preview_pending'||activePreview)?state.message:receiptOutcome?.ok===false?`Rejected or stale · ${receiptOutcome.message}`:'Historical preview record · no active Apply approval. Review current status in the editor.') : receipt ? receiptOutcome?.message || "Workspace action prepared; waiting for frontend confirmation." : !event.ok ? "Action could not be completed" : result?.kind === "navigation" ? `Ready to open ${result.projectName || result.destination}` : result?.kind === "position_preview" ? dismissed ? "Preview cancelled" : "Position preview ready · not applied or saved" : toolLabels[event.name || ""] || "Checked requested information"}</p>
      {primitive&&<p className="text-xs text-muted-foreground">{activePreview?'Apply is available only in the current editor review after rendering.':'History is evidence of an earlier proposal; it cannot apply or save geometry.'}</p>}
      {event.error && <p>{event.error}</p>}
      {event.ok && result?.kind === "navigation" && <button className="assistant-secondary" onClick={() => void navigate(result)}>Open {result.destination}</button>}
      {event.ok && result?.kind === "position_preview" && !dismissed && <>
        <p>Review the visual preview first. Apply and Save remain separate actions in the editor.</p>
        <div className="flex flex-wrap gap-2"><button className="assistant-secondary" disabled={busy || context.dirty || result.revisionId !== context.revision_id || result.projectId !== projectId} onClick={() => {
          setActionStatus("Opening editor preview; waiting for editor verification.");
          window.dispatchEvent(new CustomEvent("geoai:assistant-position-preview", { detail: result }));
        }}>Preview</button><button className="assistant-secondary" onClick={() => {
          setCancelled(old => [...old, identity]); setPreviewPending(false);
          window.dispatchEvent(new CustomEvent("geoai:assistant-preview-cancel", {detail:result}));
          setActionStatus("Preview cancelled. No changes applied or saved.");
        }}>Cancel preview</button></div>
      </>}
      <details className="assistant-evidence"><summary>Evidence</summary><pre>{JSON.stringify(event.result, null, 2)}</pre></details>
    </div>;
  };
  const response = (items: AssistantEvent[], reply = "", scope = "active") => {
    const text = items.filter(e => e.type === "delta").map(e => e.text || "").join("") || reply;
    return <>{text && <AssistantMarkdown text={text} />}{items.filter(e => e.type === "tool_result").map((e,i) => tool(e,`${scope}:${i}`))}</>;
  };
  const latest = tasks.at(-1);
  const blocked = !canSendAssistant(status);
  const latestActionFailed=!!latest&&Object.entries(workspaceOutcomes).some(([key,value])=>key.startsWith(latest.id+':')&&!value.ok);
  const latestActionUnconfirmed=latest?.events.some(e=>e.type==='tool_result'&&e.ok&&e.result?.kind==='workspace_action'&&!workspaceOutcomes[`${latest.id}:${(e.result as WorkspaceCommand).actionId}`]);
  const phaseLabel=currentPrimitive?.projectId===projectId?({preview_pending:'Preview pending',canceled:'Canceled',applied_unsaved:'Applied but unsaved',saved:`Saved in revision ${currentPrimitive.revisionId}`,rejected_stale:'Rejected or stale'})[currentPrimitive.phase]:null;
  const label = workspaceProgress || activityLabel(busy, events) || (error ? (stopped ? "Response stopped" : status?.state === "RATE_LIMITED" ? "Usage limit reached" : "Connection error") : phaseLabel || (previewPending ? "Waiting for your approval" : latestActionFailed ? "Action not completed" : latestActionUnconfirmed ? "Awaiting workspace confirmation" : latest?.status === "SUCCEEDED" ? "Completed" : "No task in progress"));
  const detail = status?.state === "RATE_LIMITED" ? availabilityReason(status) : error || (blocked ? availabilityReason(status) : null);
  if (!path || /^\/(login|register|signup)(\/|$)/.test(path)) return null;
  return <>
    {!open && <button style={{ borderRadius: 9999 }} className={`fixed ${path?.endsWith("/workspace") ? "bottom-16 right-20" : "bottom-6 right-6"} z-[95] inline-flex items-center gap-2 rounded-full border border-primary/30 bg-background/95 py-2.5 pl-3 pr-4 text-sm font-medium shadow-lg shadow-black/20 backdrop-blur-xl transition-colors hover:border-primary/60 hover:bg-primary/10 focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-primary`} onClick={() => setOpen(true)}><span className="grid size-7 place-items-center rounded-full bg-primary/15 text-primary"><Sparkles className="size-4" aria-hidden="true" /></span>StruvoCivil Assistant</button>}
    {open && <aside aria-label="StruvoCivil Assistant" className="site-assistant" style={{width}} onKeyDown={event => { if (event.key === "Escape") { setOpen(false); } }}>
      <div role="separator" tabIndex={0} aria-label="Resize assistant" aria-orientation="vertical" aria-valuemin={360} aria-valuemax={720} aria-valuenow={width} className="assistant-resizer"
        onKeyDown={e => { if (["ArrowLeft","ArrowRight"].includes(e.key)) { e.preventDefault(); setWidth(w => Math.max(360,Math.min(720,w+(e.key === "ArrowLeft" ? 24 : -24)))); } }}
        onPointerDown={e => { resizeStart.current={x:e.clientX,width}; e.currentTarget.setPointerCapture(e.pointerId); }}
        onPointerMove={e => { if (resizeStart.current) setWidth(Math.max(360,Math.min(720,resizeStart.current.width+resizeStart.current.x-e.clientX))); }}
        onPointerUp={() => { resizeStart.current=null; }} onPointerCancel={() => { resizeStart.current=null; }} />
      <header className="assistant-header"><div className="flex items-center gap-2"><Sparkles size={18} className="text-primary" aria-hidden="true" /><h2>StruvoCivil Assistant</h2></div><div className="flex gap-1"><button aria-label={width > 500 ? "Compact assistant" : "Expand assistant"} onClick={() => setWidth(width > 500 ? 480 : 640)}>{width > 500 ? <Minimize2 size={17} /> : <Maximize2 size={17} />}</button><button aria-label="Close site assistant" onClick={() => setOpen(false)}><X size={18} /></button></div></header>
      <div className="assistant-status" aria-label="Latest task status" data-state={label} role="status" aria-live="polite"><span className={busy ? "assistant-dot busy" : "assistant-dot"} /><strong aria-label="Task status">{label}</strong></div>
      <div className="assistant-availability" aria-label="AI availability">{availabilityLabel(status)}</div>
      {detail && <div className="assistant-notice" role={error ? "alert" : undefined}><p>{detail}</p><button className="assistant-link" disabled={busy} onClick={() => void refreshAvailability()}>Refresh availability</button></div>}
      <div ref={historyRef} aria-label="Assistant task history" className="assistant-conversation" onScroll={() => { const p=historyRef.current; if(p) {follow.current=p.scrollHeight-p.scrollTop-p.clientHeight<64;if(follow.current)setNewMessages(false);} }}>
        {!tasks.length && !outgoing && <div className="assistant-empty"><h3>StruvoCivil Assistant · How can I help?</h3><p>Ask about your project, find saved results, or review a position preview.</p><p className="text-muted-foreground">Engineering changes and calculations still need your review in the existing tools.</p></div>}
        {tasks.map(task => <article key={task.id} className="assistant-turn"><div className="assistant-user"><span className="assistant-speaker">You</span><p>{task.request.message}</p></div><div className="assistant-answer"><span className="assistant-speaker">StruvoCivil Assistant</span>{response(task.events,task.reply,task.id)}{task.status !== "SUCCEEDED" && <p className="assistant-task-error">{task.error || "Response did not finish. Check the details before trying again."}</p>}
          {(context.dirty || task.request.project_id !== projectId || (task.request.revision_id && context.revision_id && task.request.revision_id !== context.revision_id)) && <p className="assistant-context-note">Earlier or unsaved context. Re-read evidence before acting.</p>}
          <details className="assistant-evidence"><summary>Message details</summary><p>{task.status} · {task.model}</p><pre>{JSON.stringify({context:task.context,events:task.events.filter(e => e.type !== "delta")},null,2)}</pre></details>
        </div></article>)}
        {outgoing && <article className="assistant-turn"><div className="assistant-user"><span className="assistant-speaker">You</span><p>{outgoing}</p></div><div className="assistant-answer"><span className="assistant-speaker">StruvoCivil Assistant</span>{response(events)}{busy && !events.some(e => e.type === "delta") && <p className="text-muted-foreground">{label}…</p>}</div></article>}
      </div>
      {newMessages && <button className="assistant-newest" onClick={newest}>New message ↓</button>}
      {actionStatus && <div className="assistant-action-status" aria-live="polite"><p>{actionStatus}</p>{previewPending && actionStatus.startsWith("Visual preview shown") && <button className="assistant-link" onClick={() => setOpen(false)}>Review in editor</button>}</div>}
      {error && retryAvailable && status?.state !== "RATE_LIMITED" && <button className="assistant-secondary mx-4 mb-2" disabled={busy || !canSendAssistant(status)} onClick={() => void request(true)}>Retry</button>}
      <details className="assistant-details"><summary>Details</summary><div className="assistant-details-body">
        <label>Model <select aria-label="Assistant model" disabled={busy} value={model} onChange={e => setModel(e.target.value)}>{(status?.models || [FLASH,"zai-org/GLM-5.3"]).map(m => <option key={m} value={m}>{m === FLASH ? "GLM-5.3-Flash" : "GLM-5.3 · advanced, higher cost"}</option>)}</select></label>
        <p>{status?.message}</p><p>Nebius Token Factory · engineering unverified · no offline AI fallback.</p>
        {status?.usage && <p>Accounted tokens: {status.usage.accounted_daily_tokens} / {status.dailyTokenAllowance}. Budget accounting: ${status.usage.accounted_usd.toFixed(6)} · estimates and retained reservations, not actual charges.</p>}
        <p>Context · {projectId ? `Project ${projectId}` : "Site-wide"} · {context.selected_ids.length} selected · revision {context.revision_id ?? "resolved by backend"}{context.dirty ? " · Unsaved draft" : ""}</p>
        <button className="assistant-link" onClick={() => { void api.post("/api/assistant/context", { ...context, page: path }).then(setSavedContext).catch(e => setError(String(e))); }}>Read saved context</button>
        {savedContext !== null && <pre>{JSON.stringify(savedContext,null,2)}</pre>}
        <button className="assistant-link" disabled={busy} onClick={() => void refreshHistory()}>Refresh history</button><button className="assistant-link" disabled={busy} onClick={() => void refreshAvailability()}>Refresh availability</button>
        <p>Arbitrary CAD editing, automatic building generation and engineering execution are unavailable in chat. Use the existing editor and analysis tools.</p>
        {!!events.length && <details><summary>Current request evidence</summary><pre>{JSON.stringify(events.filter(e => e.type !== "delta"),null,2)}</pre></details>}
        {projectId && <details><summary>Earlier project conversation history</summary><button className="assistant-link" onClick={async () => { try { const list = await api.get<{ conversations: { id: string }[] }>(`/api/projects/${projectId}/conversations`); setLegacy(await Promise.all(list.conversations.slice(0,5).map(c => api.get(`/api/projects/${projectId}/conversations/${c.id}/messages`)))); } catch(e) {setError(String(e));} }}>Read saved earlier conversations</button><p>Historical records may contain offline guidance; they are not new Nebius responses.</p><pre>{legacy ? JSON.stringify(legacy,null,2) : ""}</pre></details>}
      </div></details>
      <form className="assistant-composer" onSubmit={e => {e.preventDefault();void request();}}><label className="sr-only" htmlFor="site-assistant-input">Message StruvoCivil Assistant</label><textarea id="site-assistant-input" value={input} maxLength={6000} disabled={busy} onChange={e => setInput(e.target.value)} placeholder="Ask StruvoCivil Assistant…" /><div className="flex items-center justify-between gap-2"><span>Changes need your review</span>{busy ? <button key="stop" type="button" className="assistant-secondary" onClick={e => {e.preventDefault(); setStopped(true); controller.current?.abort();}}>Stop response</button> : <button key="send" type="submit" className="assistant-send" disabled={!input.trim() || !!workspaceProgress || !canSendAssistant(status)}><ArrowUp size={16} aria-hidden="true" />Send</button>}</div></form>
    </aside>}
  </>;
}

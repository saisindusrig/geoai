"use client";
import {useEffect,useLayoutEffect,useRef,useState} from 'react';
import type {EditableModelEditor} from '@/hooks/useEditableModelEditor';
import type {WorkspaceCommand} from '@/lib/workspace-assistant';
import {primitiveStatus,type PrimitivePhase,type PrimitiveStatus} from '@/lib/primitive-status';
import {boxFrame} from '@/lib/editor-transform';
import {api} from '@/lib/api';
type Review={command:WorkspaceCommand;terminal?:'canceled'|'rejected_stale'};
const fmt=(v:number)=>Number(v.toFixed(6));
export default function SupervisedPrimitiveControls({editor}:{editor:EditableModelEditor}){
 const live=useRef(editor);useLayoutEffect(()=>{live.current=editor;},[editor]);
 const [reviewed,setReviewed]=useState<Review|null>(null),[busy,setBusy]=useState(false),[error,setError]=useState(''),[readyAction,setReadyAction]=useState('');
 const p=editor.platformPreview?.proposal;
 useEffect(()=>{if(!p?.expiresAt)return;const timer=window.setTimeout(()=>{if(live.current.platformPreview?.proposal?.actionId===p.actionId){live.current.setPlatformPreview(null);setReviewed({command:p,terminal:'rejected_stale'});primitiveStatus(p,'rejected_stale','Rejected or stale · preview expired. No active approval.');}},Math.max(0,p.expiresAt-Date.now()));return()=>clearTimeout(timer);},[p]);
 useEffect(()=>{if(!p)return;let active=true;queueMicrotask(()=>{if(active)setReviewed(old=>old?.command.actionId===p.actionId?old:{command:p});});return()=>{active=false;};},[p]);
 useEffect(()=>{const ready=(event:Event)=>{const r=(event as CustomEvent<{actionId:string;ok:boolean}>).detail;if(r.actionId===p?.actionId)setReadyAction(r.ok?r.actionId:'');};window.addEventListener('geoai:workspace-outcome',ready);if(p&&document.querySelector(`[data-primitive-preview="${p.actionId}"]`))queueMicrotask(()=>setReadyAction(p.actionId));return()=>window.removeEventListener('geoai:workspace-outcome',ready);},[p]);
 useEffect(()=>{const status=(event:Event)=>{const r=(event as CustomEvent<PrimitiveStatus>).detail;if(p?.actionId===r.actionId&&(r.phase==='canceled'||r.phase==='rejected_stale'))setReviewed({command:p,terminal:r.phase});};window.addEventListener('geoai:primitive-status',status);return()=>window.removeEventListener('geoai:primitive-status',status);},[p]);
 const command=p??reviewed?.command,kind=command?.candidate?.category==='beam'?'beam':'column',title=kind==='beam'?'Beam':'Column';
 const terminal=reviewed?.command.actionId===command?.actionId?reviewed?.terminal:undefined;
 const current=command?editor.document?.components.find(c=>c.id===command.candidate?.id):undefined;
 const savedComponent=command?editor.baseRevision?.document?.components.find(c=>c.id===command.candidate?.id):undefined;
 const saved=!!current&&!editor.dirty&&!!editor.baseRevision&&editor.baseRevision.id!==command?.revisionId&&JSON.stringify(savedComponent)===JSON.stringify(current);
 const phase:PrimitivePhase=terminal??(p?'preview_pending':saved?'saved':current?'applied_unsaved':'rejected_stale');
 const message=phase==='preview_pending'?`Preview pending · temporary ${kind} · not applied or saved${readyAction===p?.actionId?'':' · waiting for renderer'}.`:phase==='canceled'?'Canceled · temporary proposal removed. No Apply approval is active.':phase==='saved'?`Saved ${kind} in revision ${editor.baseRevision?.id}.`:phase==='applied_unsaved'?`${title} applied to the editor draft · not saved.`:'Rejected or stale · no active approval. The proposal is absent or its source changed.';
 useEffect(()=>{if(command)primitiveStatus(command,phase,message,phase==='saved'?editor.baseRevision?.id:undefined);},[command,phase,message,editor.baseRevision?.id]);
 const cancel=()=>{const c=live.current.platformPreview?.proposal;if(!c)return;setReviewed({command:c,terminal:'canceled'});live.current.setPlatformPreview(null);setError('');primitiveStatus(c,'canceled','Canceled · temporary proposal removed. No Apply approval is active.');};
 const apply=async()=>{
  if(!p||busy||readyAction!==p.actionId||terminal)return;setBusy(true);setError('');
  try{
   const verified=await api.post<WorkspaceCommand>('/api/assistant/workspace/validate',{page:`/projects/${p.projectId}/workspace`,project_id:p.projectId,revision_id:p.revisionId,selected_ids:[],dirty:false,name:p.validation.name,arguments:p.validation.arguments,action_id:p.actionId});
   if(verified.actionId!==p.actionId||JSON.stringify(verified.candidate)!==JSON.stringify(p.candidate)||live.current.platformPreview?.proposal?.actionId!==p.actionId)throw Error('Saved source or preview changed. Nothing applied.');
   live.current.applyPrimitivePreview(p.actionId);setReviewed({command:p});
  }catch(e){setError(e instanceof Error?e.message:'Proposal validation failed. Nothing applied.');if(live.current.platformPreview?.proposal?.actionId===p.actionId){live.current.setPlatformPreview(null);setReviewed({command:p,terminal:'rejected_stale'});primitiveStatus(p,'rejected_stale','Rejected or stale · validation failed. No active approval.');}}
  finally{setBusy(false);}
 };
 if(!command)return null;
 const c=p?.candidate??current??command.candidate,beam=c?.category==='beam'&&c.geometry.kind==='box'?boxFrame(c):null;
 return <section aria-label={`Supervised ${kind} review`} data-proposal-state={phase} className={`absolute left-24 ${kind==='beam'?'bottom-16':'top-24'} z-40 max-w-[360px] space-y-2 rounded border border-fuchsia-400/60 bg-background/95 p-3 text-xs shadow-xl`}>
  <strong>{message}</strong>
  <p>Project {command.projectId} · source revision {command.revisionId} · user-supplied dimensions</p>
  {c&&<><p>{c.name} · independent rectangular {kind} · no parent or structural connections</p>{beam?<><p>A ENU: [{beam.start.toArray().map(fmt).join(', ')}] m</p><p>B ENU: [{beam.end.toArray().map(fmt).join(', ')}] m</p><p>Length: {fmt(beam.length)} m · width: {c.geometry.kind==='box'?fmt(c.geometry.size[1]*c.transform.scale[1]):''} m · depth: {c.geometry.kind==='box'?fmt(c.geometry.size[2]*c.transform.scale[2]):''} m</p><p>Direction A → B: [{beam.direction.toArray().map(fmt).join(', ')}]</p><details><summary>Orientation details</summary><p>XYZ rotation: [{c.transform.rotation_deg.map(fmt).join(', ')}]°</p><p>Section depth follows projected ENU Up; near-vertical beams use North. No endpoint snapping or structural connectivity is inferred.</p></details></>:<><p>Width × depth × height: {c.geometry.kind==='box'?c.geometry.size.join(' × '):'unsupported'} m</p><p>Centre ENU: [{c.transform.position.join(', ')}] m · yaw {c.transform.rotation_deg[2]}°</p></>}</>}
  <p>{p?'Magenta translucent geometry is proposed.':'This record describes the reviewed proposal.'} Existing geometry is retained. Conceptual geometry only, excluded from quantities and verified engineering results.</p>
  {p&&!terminal?<div className="flex gap-3"><button disabled={busy||readyAction!==p.actionId} onClick={()=>void apply()} className="rounded bg-primary px-3 py-2 text-primary-foreground">{busy?'Checking saved source…':`Apply ${kind}`}</button><button onClick={cancel}>Cancel proposal</button></div>:<div className="flex gap-3">{phase==='applied_unsaved'&&<button disabled={busy||!editor.dirty||editor.saving} onClick={async()=>{setBusy(true);setError('');try{await live.current.save();}catch(e){setError(e instanceof Error?e.message:'Save or refresh failed. Check the current saved revision.');primitiveStatus(command,'applied_unsaved','Save did not confirm. Check the current revision; no automatic retry.');}finally{setBusy(false);}}} className="rounded bg-primary px-3 py-2 text-primary-foreground">{editor.saving?'Saving…':'Save model revision'}</button>}{phase==='saved'&&<button disabled>Saved</button>}<button onClick={()=>setReviewed(null)}>Dismiss</button></div>}
  {error&&<p role="alert">{error}</p>}
 </section>;
}

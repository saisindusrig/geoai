"use client";

import {useEffect,useMemo,useRef,useState} from 'react';

import {FORCE_DISPLAY,diagramDisplayScales} from '@/lib/structural-display';
import {api,formatApiErrorMessage} from '@/lib/api';

import type {EditableModelEditor} from '@/hooks/useEditableModelEditor';

import type {FoundationData} from '@/lib/foundation-visual';

import {STRUCTURAL_MODES,buildStructuralOverlay,savedStructuralEvidence,selectedStructuralFrames,structuralCases,type StructuralMode,type StructuralRow} from '@/lib/structural-visual';

const clear=()=>window.dispatchEvent(new CustomEvent('geoai:elastic-results',{detail:{clearMode:'structural-visual'}}));

type FoundationRow={id:number;type:string;status:string;result:{computed:FoundationData;inputs:{inputs:{cover_mm:number}}}};

export default function StructuralVisualPanel({editor,projectId}:{editor:EditableModelEditor;projectId:number}){

 const rid=editor.baseRevision?.id;
 const foundationStudy=!!editor.document?.metadata?.foundation_system;

 const [history,setHistory]=useState<{frame:StructuralRow[];slab:StructuralRow[];foundation?:FoundationRow[]}>({frame:[],slab:[]}),[loading,setLoading]=useState(true),[error,setError]=useState(''),[mode,setMode]=useState<StructuralMode>('path'),[caseName,setCase]=useState(''),[scale,setScale]=useState(50),[force,setForce]=useState<'moment'|'shear'|'axial'>('moment'),[original,setOriginal]=useState(true),[isolate,setIsolate]=useState(true),[active,setActive]=useState(!editor.document?.metadata?.foundation_system),[fit,setFit]=useState(0);

 const fitted=useRef('');
 useEffect(()=>{const ownership=(event:Event)=>{const next=(event as CustomEvent<{mode?:string}|null>).detail;if(next?.mode&&next.mode!=='structural-visual')setActive(false);};window.addEventListener('geoai:elastic-results',ownership);return()=>window.removeEventListener('geoai:elastic-results',ownership);},[]);

 useEffect(()=>{let live=true;const read=async()=>{try{const [frame,slab,foundation]=await Promise.all([api.get<{records:StructuralRow[]}>(`/api/projects/${projectId}/engineering/assembly?compact=true`),api.get<{records:StructuralRow[]}>(`/api/projects/${projectId}/engineering/slab-transfer`),foundationStudy?api.get<{records:FoundationRow[]}>(`/api/projects/${projectId}/engineering/foundation-system?model_revision_id=${rid}`):Promise.resolve({records:[] as FoundationRow[]})]);if(live){setHistory({frame:frame.records,slab:slab.records,foundation:foundation.records});setError('');}}catch(e){if(live){setHistory({frame:[],slab:[]});setError(formatApiErrorMessage(e));}}finally{if(live)setLoading(false);}};queueMicrotask(()=>{if(live)setLoading(true);});void read();const timer=window.setInterval(()=>void read(),15000);return()=>{live=false;window.clearInterval(timer);clear();};},[projectId,rid,foundationStudy]);

 const evidence=useMemo(()=>{const e=savedStructuralEvidence(history.frame,history.slab,rid??0);const f=history.foundation?.find(r=>r.type==='FOUNDATION_SYSTEM_RESULT'&&r.status==='REVIEWED_SYNTHETIC_CALCULATION');if(f){e.foundation={data:f.result.computed,cover_mm:f.result.inputs.inputs.cover_mm};e.recordIds.push(f.id);}return e;},[history,rid]);

 const cases=structuralCases(evidence),selectedCase=cases.includes(caseName)?caseName:cases[0]??'',frames=selectedStructuralFrames(evidence,selectedCase);

 const components=useMemo(()=>editor.document?.components??[],[editor.document]),blocked=loading||editor.dirty||!!editor.platformPreview||!!editor.aiPreview||!!editor.comparison;

 const selected=components.find(c=>editor.selectedIds.includes(c.id)),members=frames.flatMap(f=>f.physical_to_analytical_graph?.members??[]),selectedSamples=frames.flatMap(f=>f.elements??[]).filter(e=>e.component_id===selected?.id).flatMap(e=>e.samples),peak=(key:'moment_nm'|'shear_n'|'axial_n')=>selectedSamples.length?Math.max(...selectedSamples.map(s=>Math.abs(s[key])))/1000:null;

 const selectedFoundation=evidence.foundation&&[evidence.foundation.data.geometry.footing_id,evidence.foundation.data.geometry.column_id].includes(selected?.id??'')?evidence.foundation.data:undefined;
 const selectedConnections=frames.flatMap(f=>f.inputs?.connections??[]).filter(c=>c.beam_id===selected?.id||c.column_id===selected?.id);

 useEffect(()=>{const inspect=(event:Event)=>{const id=(event as CustomEvent<{key:string}>).detail?.key;if(editor.document?.components.some(c=>c.id===id))editor.selectMany([id]);};window.addEventListener('geoai:foundation-inspect',inspect);return()=>window.removeEventListener('geoai:foundation-inspect',inspect);},[editor]);

 useEffect(()=>{

  if(blocked||!active){clear();return;}

  const key=`${projectId}:${rid}:${mode}:${fit}`,shouldFit=fitted.current!==key;fitted.current=key;

  const detail=buildStructuralOverlay(evidence,components,mode,{caseName:selectedCase,scale,force,original,isolate:mode==='warnings'||mode==='foundation'?false:isolate,selectedId:selected?.id,fit:shouldFit});

  window.dispatchEvent(new CustomEvent('geoai:elastic-results',{detail:{...detail,hideModel:mode==='deformation'&&!original&&frames.length>0}}));

 },[evidence,components,mode,selectedCase,frames.length,scale,force,original,isolate,selected?.id,blocked,active,fit,projectId,rid]);

 const show=(next:StructuralMode)=>{setMode(next);setActive(true);};

 const missing=components.filter(c=>['column','beam','slab','footing','foundation','base_plate','connection'].includes(c.category)&&!members.some(m=>m.component_id===c.id)&&c.id!==evidence.transfer?.slab_id);

 return <section aria-label="Structural visual engineering" data-mode={mode} data-blocked={blocked} className="mb-4 space-y-3 rounded border border-border p-3 text-xs [&_button]:rounded [&_button]:border [&_button]:border-border [&_button]:px-2 [&_button]:py-2 [&_button:disabled]:opacity-40 [&_select]:w-full [&_select]:bg-background">

  <h3 className="text-sm font-semibold">Structure · explore in 3D</h3><p className="text-amber-200">Saved analytical evidence · no safety or code approval</p>

  <div className="grid grid-cols-2 gap-1">{STRUCTURAL_MODES.map(([key,label])=><button key={key} aria-pressed={active&&mode===key} disabled={blocked} className={active&&mode===key?'text-primary':''} onClick={()=>show(key)}>{label}</button>)}</div>

  {blocked&&<p role="status">{loading?'Loading saved evidence…':'Draft / preview: saved overlays disabled until revision is restored or saved.'}</p>}

  {error&&<p role="alert">Saved evidence unavailable: {error}</p>}

  {!!cases.length&&<label>Saved load case<select aria-label="Structural saved load case" value={selectedCase} disabled={blocked} onChange={e=>setCase(e.target.value)}>{cases.map(c=><option key={c}>{c}</option>)}</select></label>}
  {cases.length>1&&!blocked&&<details><summary>Compare available saved load cases</summary><p>Saved sample maxima only; no new combination or design envelope. {selected?'Selected component':'Analyzed system'}.</p>{cases.map(name=>{const samples=selectedStructuralFrames(evidence,name).flatMap(f=>f.elements??[]).filter(e=>!selected||e.component_id===selected.id).flatMap(e=>e.samples);return <button key={name} aria-pressed={name===selectedCase} className="my-1 block w-full text-left" onClick={()=>setCase(name)}>{name} · {samples.length?`|u|max ${(Math.max(...samples.map(s=>Math.hypot(...s.displacement_m)))*1000).toPrecision(4)} mm · |M|max ${(Math.max(...samples.map(s=>Math.abs(s.moment_nm)))/1000).toFixed(3)} kN·m`:'No supported samples for this component'}</button>;})}</details>}

  {mode==='deformation'&&frames.length>0&&<><label className="block">Visual displacement magnification ×{scale}<input aria-label="Displacement magnification" className="w-full" type="range" min={1} max={1000} step={1} value={scale} disabled={blocked} onChange={e=>setScale(Number(e.target.value))}/></label><label className="block"><input aria-label="Show original structure" type="checkbox" checked={original} onChange={e=>setOriginal(e.target.checked)}/> Show original structure (grey); computed displacement in lime</label><p>Magnification affects display only. No slab shell deformation is available.</p></>}

  {mode==='forces'&&<label>Saved internal force<select aria-label="Structural force diagram" value={force} onChange={e=>setForce(e.target.value as typeof force)}><option value="moment">Bending moment · kN·m</option><option value="shear">Shear · kN</option><option value="axial">Axial · kN</option></select></label>}

  <div aria-label="Structural visual legend" className="rounded bg-muted/30 p-2">{mode==='path'?'Cyan: saved member topology · pink: declared rigid arms. Topology arrows are not force magnitudes or directions. Connections have no verified capacity.':mode==='loads'?'Yellow: saved applied loads · green: support reactions. Arrow length is normalized; labels retain signed kN, kN/m and kN·m about −North.':mode==='forces'?`${FORCE_DISPLAY[force].style}: saved signed local samples · grey dashed: centreline. Diagram offset is normalized, not physical displacement.`:mode==='deformation'?`Lime: computed planar member displacement ×${scale} · pink: computed rigid-arm motion · mm labels are unscaled.`:mode==='slab'?'Cyan: saved one-way tributary polygons, not slab stress contours or plate FEA.':mode==='foundation'?'Physical column-to-footing transfer and soil response are not verified by the frame solver. Use the existing foundation evidence below.':'Labels identify components without a current verified solver transfer; CAD proximity is not an analytical connection.'}</div>

  {mode==='forces'&&frames.length>0&&!blocked&&<div aria-label="Diagram display scale" className="space-y-1 rounded border border-border p-2"><b style={{color:FORCE_DISPLAY[force].color}}>{FORCE_DISPLAY[force].symbol} · {FORCE_DISPLAY[force].name} · {FORCE_DISPLAY[force].unit}</b><p>Diagram magnification: normalized display ordinates; not deformation.</p>{diagramDisplayScales(frames,force).map((s,i)=><div key={i}><p>Frame {i+1}: −{s.reference.toFixed(3)} / 0 / +{s.reference.toFixed(3)} {FORCE_DISPLAY[force].unit}</p><div aria-hidden="true" className="my-1 h-1 rounded" style={{background:FORCE_DISPLAY[force].color}}/><p>{s.peak===0?'Zero saved values · no offset':`±0.75 m diagram offset = ±${s.reference.toFixed(3)} ${FORCE_DISPLAY[force].unit} · 1 ${FORCE_DISPLAY[force].unit} = ${s.mmPerUnit.toFixed(2)} mm display offset`}</p></div>)}<p>Saved values retain their original signs. No stress contour.</p></div>}
  <p className="text-muted-foreground">Labels avoid overlap. Select a component or yellow marker for full saved values.</p>
  {!evidence.frames.length&&!loading&&<p>No current verified structural solver result for this revision. No response or load path is inferred.</p>}

  {mode==='slab'&&!evidence.transfer&&<p>Not supported: no saved verified slab-to-beam allocation for this revision.</p>}

  {mode==='slab'&&evidence.transfer&&<p>Saved pressure allocation: {evidence.transfer.applied_kn?.toFixed(3)} kN applied / {evidence.transfer.transferred_kn?.toFixed(3)} kN transferred. Residual {evidence.transfer.conservation_error_kn?.toExponential(2)} kN.</p>}

  {mode==='foundation'&&!evidence.foundation&&<p className="text-amber-200">Not verified: real footing contact, connection capacity and soil response. Foundation synthetic checks remain a separate, explicitly bounded study; frame base reactions are not silently applied to it.</p>}

  {mode==='foundation'&&evidence.foundation&&<p>Saved synthetic soil: {(evidence.foundation.data.contact.pmin_pa/1000).toFixed(3)} kPa uniform · settlement {(evidence.foundation.data.contact.delta_down_m*1000).toFixed(3)} mm. Settlement outline ×20; no physical frame-to-soil connection inferred.</p>}

  <div className="flex flex-wrap gap-2"><label><input aria-label="Isolate analyzed structural system" type="checkbox" disabled={blocked||mode==='warnings'||mode==='foundation'} checked={isolate} onChange={e=>setIsolate(e.target.checked)}/> Isolate analyzed system</label><button disabled={blocked} onClick={()=>{setActive(true);setFit(v=>v+1);}}>Frame view</button><button onClick={()=>{setIsolate(false);setOriginal(true);setActive(false);clear();}}>Restore full structure</button></div>

  <label>Inspect saved component<select aria-label="Inspect structural component" value={selected?.id??''} onChange={e=>editor.selectMany(e.target.value?[e.target.value]:[])}><option value="">Click a component in 3D or choose here</option>{components.filter(c=>['beam','column','slab','footing','foundation','base_plate','connection'].includes(c.category)).map(c=><option key={c.id} value={c.id}>{c.name} · {c.category}</option>)}</select></label>

  {selected&&<article aria-label="Selected structural evidence" className="space-y-2 rounded border border-border p-2"><b>{selected.name}</b><p>{blocked?'Saved evidence hidden while draft or preview is active.':selectedSamples.length?`Available saved planar samples · |M|max ${peak('moment_nm')?.toFixed(3)} kN·m · |V|max ${peak('shear_n')?.toFixed(3)} kN · |N|max ${peak('axial_n')?.toFixed(3)} kN`:selectedFoundation?`Saved synthetic footing: service column ${selectedFoundation.actions.service_column_kn.toFixed(3)} kN; gross pressure ${(selectedFoundation.contact.pmax_pa/1000).toFixed(3)} kPa; settlement ${(selectedFoundation.contact.delta_down_m*1000).toFixed(3)} mm. No full structural approval.`:selected.id===evidence.transfer?.slab_id?'Saved one-way tributary allocation only; slab moments and shell displacements not supported.':'Not verified: no current saved member forces or displacement for this component.'}</p><details><summary>Calculation evidence and source identity</summary><p className="break-all">Component {selected.id} · revision {rid} · records {evidence.recordIds.join(', ')||'none'} · case {selectedCase||'none'}</p><pre className="max-h-64 overflow-auto whitespace-pre-wrap break-all">{JSON.stringify({connections:selectedConnections,samples:blocked?[]:selectedSamples,foundation:blocked?undefined:selectedFoundation},null,2)}</pre></details></article>}

  <details><summary>Coverage, warnings and immutable numerical evidence</summary><p>{new Set(members.map(m=>m.component_id)).size} analyzed members · {missing.length} structural/context components without current transfer evidence. Excluded model context is not assigned loads.</p><p>Planar elastic methods only. No invented torsion, slab FEA, connection capacity, soil stiffness or cross-system transfer.</p>{missing.map(c=><button className="m-1" key={c.id} onClick={()=>{editor.selectMany([c.id]);show('warnings');}}>{c.name} · Not verified</button>)}<pre className="max-h-64 overflow-auto whitespace-pre-wrap break-all">{JSON.stringify({records:evidence.recordIds,solver:frames.map(f=>({version:f.solver_version,run:f.run_id,equilibrium:f.equilibrium_residual_si,limitations:(f as FrameResultWithLimits).limitations}))},null,2)}</pre></details>

 </section>;

}

type FrameResultWithLimits={limitations?:string[]};


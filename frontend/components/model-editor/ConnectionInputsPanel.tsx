"use client";
import {useEffect,useState,useRef} from 'react';
import {api,formatApiErrorMessage} from '@/lib/api';
import type {EditableModelEditor} from '@/hooks/useEditableModelEditor';

type Evidence={category:string|null;reference:string;method:string;applicability:string;reviewed_by:string};
type Quantity={value:number|null;evidence:Evidence};
type Anchor={id:string;material:string;geometry_and_material_evidence:Evidence;tension_load_path:string;diameter_m:Quantity;effective_embedment_m:Quantity;tensile_area_m2:Quantity;steel_modulus_pa:Quantity;axial_stiffness_n_m:Quantity;max_valid_tension_n:Quantity;max_valid_opening_m:Quantity};
type Inputs={anchors:Anchor[];saved_geometry_evidence:Evidence;mechanical_evidence:Evidence;contact_stiffness_n_m3:Quantity;max_valid_pressure_pa:Quantity;max_valid_contact_displacement_m:Quantity;concrete_material:string;contact_model_justification:string;reference_plane_assumption:string;rigid_plate:boolean;homogeneous_contact:boolean;fixed_anchor_ground:boolean;zero_pretension:boolean;shear_excluded:boolean;engineer_input_review:boolean};
type Assessment={status:string;missing:{path:string;reason:string}[]};
type Actual={source_interface_analysis_id:number;source_revision_id:number;source_evidence_sha256:string;geometry:{column_base_enu_m:number[];objects:{component_id:string;name:string;size_m:number[];position_enu_m:number[]}[]};actual_anchor_local_positions:{id:string;position_east_north_m:number[]}[];demand:{compression_n:number;horizontal_shear_east_n:number;moment_about_negative_north_nm:number;solver_version:string;run_id:string}};
type Result={inputs:Inputs;assessment?:Assessment;actual_project_audit:Actual;input_sha256:string;pressure_max_kpa?:number;compression_resultant_n?:number;active_contact_area_m2?:number;active_contact_polygon_east_north_m?:number[][];equilibrium_residual_si?:number[];translation_down_m?:number;rotations_east_north_rad?:number[];anchors?:{id:string;position_east_north_m:number[];tension_n:number;opening_m:number}[];pressure_vertices?:{position_east_north_m:number[];pressure_pa:number}[]};
type Row={id:number;model_revision_id:number;status:string;result:Result};
type Audit={actual:Actual;template:Inputs;assessment:Assessment;anchor_fields:Record<string,[string,string]>;contact_fields:Record<string,[string,string]>;flags:Record<string,string>};
const categories=['measured','manufacturer_data','engineer_declared_assumption','synthetic_verification'];
function EvidenceFields({value,onChange,label,expanded=false}:{value:Evidence;onChange:(v:Evidence)=>void;label:string;expanded?:boolean}){
 const [open,setOpen]=useState(expanded);
 return <details open={open} onToggle={event=>setOpen(event.currentTarget.open)} className="mt-1 rounded border border-border p-2"><summary>{label} · {value.category?.replaceAll('_',' ')??'source missing'}</summary><div className="mt-3 grid grid-cols-2 gap-3 text-xs"><label className="col-span-2 block">Evidence category<select aria-label={`${label} category`} value={value.category??''} onChange={e=>onChange({...value,category:e.target.value||null})}><option value="">Choose provenance</option>{categories.map(c=><option key={c} value={c}>{c.replaceAll('_',' ')}</option>)}</select></label>{(['reference','method','applicability','reviewed_by'] as const).map(k=><label className="block" key={k}>{({reference:'Source / document / page / date',method:'Measurement or derivation method',applicability:'Applicability and exclusions',reviewed_by:'Input reviewed by'})[k]}<input aria-label={`${label} ${k}`} value={value[k]} onChange={e=>onChange({...value,[k]:e.target.value})}/></label>)}<p className="col-span-2 text-xs text-muted-foreground">Source declarations are not independently verified. Synthetic data cannot authorize actual analysis.</p></div></details>;
}
function QuantityField({label,why,value,onChange}:{label:string;why:string;value:Quantity;onChange:(v:Quantity)=>void}){
 return <div className="rounded border border-border p-2"><label className="block font-medium">{label}<input aria-label={label} type="number" min="0" step="any" placeholder="Not supplied" value={value.value??''} onChange={e=>onChange({...value,value:e.target.value===''?null:Number(e.target.value)})}/></label><p className="text-xs text-muted-foreground">{why}</p><EvidenceFields label={`${label} evidence`} value={value.evidence} onChange={e=>onChange({...value,evidence:e})}/></div>;
}
export default function ConnectionInputsPanel({editor,projectId}:{editor:EditableModelEditor;projectId:number}){
 const base=`/api/projects/${projectId}/engineering/connection-inputs`,rid=editor.baseRevision?.id,inputId=useRef<number|undefined>(undefined);
 const [audit,setAudit]=useState<Audit>(),[q,setQ]=useState<Inputs>(),[rows,setRows]=useState<Row[]>([]),[dirty,setDirty]=useState(false),[busy,setBusy]=useState(false),[consent,setConsent]=useState(false),[error,setError]=useState(''),[anchorIndex,setAnchorIndex]=useState(0),[loaded,setLoaded]=useState<number>(),[scale,setScale]=useState(.4);
 type InputTarget={projectId:number;revisionId:number;recordId:number;path:string};
 const [requestedTarget,setRequestedTarget]=useState<InputTarget|null>(null);
 const [requestedField,setRequestedField]=useState<string|null>(null);
 const [task,setTask]=useState("geometry"),[step,setStep]=useState(0);
 const [navigationNotice,setNavigationNotice]=useState("");
 useEffect(()=>{
  const navigate=(event:Event)=>setRequestedTarget((event as CustomEvent<InputTarget>).detail);
  window.addEventListener("geoai:connection-input",navigate);
  return()=>window.removeEventListener("geoai:connection-input",navigate);
 },[]);
 useEffect(()=>{
  let active=true;
  queueMicrotask(()=>{
  if(!active)return;
  const target=requestedTarget;
  if(!target || !q || !audit || target.projectId!==projectId || target.revisionId!==rid)return;
  if(target.recordId!==rows.find(row=>row.result.assessment)?.id){setNavigationNotice("This saved input record has been replaced. Review the current assessment before editing.");return;}
  const parts=target.path.split(".");
  if(parts[0]==="anchors"){
   const index=q.anchors.findIndex(a=>a.id===parts[1]);
   if(index<0){setNavigationNotice("The referenced anchor is unavailable in this input record.");return;}
   setAnchorIndex(index);
  }
  setRequestedField(target.path);setNavigationNotice(`Saved input #${target.recordId} · ${target.path}`);
  });
  return()=>{active=false;};
 },[requestedTarget,projectId,rid,q,audit,rows]);
 useEffect(()=>{
  let active=true;
  queueMicrotask(()=>{
   if(!active || !requestedField || !audit)return;
   const parts=requestedField.split("."),anchor=parts[0]==="anchors",field=anchor?parts[2]:parts[0];
   const contact=["concrete_material","contact_model_justification",...Object.keys(audit.contact_fields)];
   const anchorFields=["material","geometry_and_material_evidence","tension_load_path",...Object.keys(audit.anchor_fields)];
   const assumptions=["reference_plane_assumption","mechanical_evidence",...Object.keys(audit.flags)];
   setTask(anchor?`anchor:${parts[1]}`:field==="saved_geometry_evidence"?"geometry":contact.includes(field)?"contact":"assumptions");
   setStep(Math.max(0,(anchor?anchorFields:contact.includes(field)?contact:assumptions).indexOf(field)));
  });
  return()=>{active=false;};
 },[requestedField,audit]);
 useEffect(()=>{
  if(!requestedField || !audit)return;
  const parts=requestedField.split("."),anchor=parts[0]==="anchors",field=anchor?parts.slice(2):parts;
  const names:Record<string,string>={saved_geometry_evidence:"Saved geometry evidence",mechanical_evidence:"Mechanical model evidence",concrete_material:"Concrete material identification",contact_model_justification:"Contact model justification",reference_plane_assumption:"Reference-plane assumption",material:"Anchor material identification",tension_load_path:"Anchor tension load path",geometry_and_material_evidence:"Anchor geometry and material evidence"};
  let label=names[field[0]] ?? (anchor?audit.anchor_fields:audit.contact_fields)[field[0]]?.[0] ?? field[0];
  if(field[1]==="evidence")label+=" evidence";
  if(field[1] && field[1]!=="value")label+=" "+(field.at(-1)==="evidence"?"category":field.at(-1));
  else if(field[0].endsWith("_evidence"))label+=" category";
  const region=document.querySelector('[aria-label="Real connection engineering inputs"]');
  const control=Array.from(region?.querySelectorAll<HTMLElement>("[aria-label]")??[]).find(el=>el.getAttribute("aria-label")===label);
  if(control){for(let el=control.parentElement;el;el=el.parentElement)if(el instanceof HTMLDetailsElement)el.open=true;control.scrollIntoView({block:"center"});control.focus();}
 },[requestedField,anchorIndex,audit,task,step]);
 const input=rows.find(r=>r.result.assessment),result=rows.find(r=>r.result.pressure_vertices),assessment=input?.result.assessment??audit?.assessment;
 const geometryChanged=editor.dirty&&JSON.stringify(editor.document)!==JSON.stringify(editor.baseRevision?.document),blocked=busy||loaded!==rid||!rid||editor.dirty||!!editor.platformPreview||!!editor.aiPreview||!!editor.comparison;
 const stale=dirty||geometryChanged||!!editor.platformPreview||!!editor.aiPreview||!!editor.comparison||result?.status==='STALE'||result?.model_revision_id!==rid;
 useEffect(()=>{let active=true;if(!rid)return;Promise.all([api.get<Audit>(`${base}/audit?model_revision_id=${rid}`),api.get<{records:Row[]}>(base)]).then(([a,h])=>{if(!active)return;setAudit(a);setRows(h.records);const i=h.records.find(r=>r.result.assessment);setQ(i?.result.inputs??a.template);inputId.current=i?.id;setDirty(false);setConsent(false);setLoaded(rid);setError('');}).catch(e=>{if(active){setError(formatApiErrorMessage(e));setLoaded(rid);}});return()=>{active=false;};},[base,rid]);
 useEffect(()=>{if(stale)window.dispatchEvent(new CustomEvent('geoai:elastic-results',{detail:null}));},[stale]);
 useEffect(()=>{let active=true;const timer=window.setInterval(()=>{if(busy||loaded!==rid)return;const expected=inputId.current;api.get<{records:Row[]}>(base).then(h=>{if(!active||inputId.current!==expected)return;if(h.records.find(r=>r.result.assessment)?.id!==expected){setDirty(true);setConsent(false);setError('Engineering inputs changed elsewhere. Reload the latest draft.');}setRows(h.records);}).catch(()=>{});},5000);return()=>{active=false;window.clearInterval(timer);};},[base,busy,loaded,rid]);
 const edit=(value:Inputs)=>{setQ(value);setDirty(true);setConsent(false);window.dispatchEvent(new CustomEvent('geoai:elastic-results',{detail:null}));};
 const save=async()=>{setBusy(true);setError('');try{const r=await api.post<Row>(base+'/inputs',{inputs:q,model_revision_id:rid,base_input_id:inputId.current??null});inputId.current=r.id;setRows((await api.get<{records:Row[]}>(base)).records);setDirty(false);setConsent(false);window.dispatchEvent(new CustomEvent('geoai:engineering-inputs-saved',{detail:{projectId}}));}catch(e){setError(formatApiErrorMessage(e));}finally{setBusy(false);}};
 const run=async()=>{if(!input)return;setBusy(true);setError('');try{await api.post(base+'/authorize-run',{input_id:input.id,input_sha256:input.result.input_sha256,authorize_n_m_contact:true});setRows((await api.get<{records:Row[]}>(base)).records);setConsent(false);}catch(e){setError(formatApiErrorMessage(e));}finally{setBusy(false);}};
 const view=(computed=false)=>{if(!audit||computed&&(!result||stale))return;const a=audit.actual,origin=a.geometry.column_base_enu_m,plate=a.geometry.objects[1],foot=a.geometry.objects[2],to=(p:number[],z=0)=>[origin[0]+p[0],origin[1]+p[1],origin[2]+z],paths:number[][][]=[],colors:string[]=[],labels:{name:string;position:number[];componentId:string}[]=[],arrows:number[]=[];
  for(const o of [plate,foot]){const [B,L,H]=o.size_m,z=o.position_enu_m[2]+H/2-origin[2],corners=[[-B/2,-L/2],[B/2,-L/2],[B/2,L/2],[-B/2,L/2],[-B/2,-L/2]];paths.push(corners.map(p=>to(p,z)));colors.push(o===plate?'#56cbff':'#bacbd8');}
  a.actual_anchor_local_positions.forEach((v,i)=>{paths.push([to(v.position_east_north_m,-.08),to(v.position_east_north_m,.06)]);colors.push('#ffca72');if(!computed)labels.push({name:`A${i+1} declared position`,position:to(v.position_east_north_m,.1+(i%2)*.13),componentId:plate.component_id});});
  if(computed&&result){const r=result.result;for(const v of r.pressure_vertices!){paths.push([to(v.position_east_north_m,.015),to(v.position_east_north_m,.015+v.pressure_pa/1e6*scale)]);colors.push('#acff68');}for(const [i,v] of r.anchors!.entries()){paths.push([to(v.position_east_north_m,.05),to(v.position_east_north_m,-.15-v.tension_n/1000*.003)]);colors.push('#ff8c65');arrows.push(paths.length-1);labels.push({name:`A${i+1} T ${(v.tension_n/1000).toFixed(3)} kN`,position:to(v.position_east_north_m,-.35-(i%2)*.13),componentId:plate.component_id});}labels.push({name:`Declared-input N/M only · C ${(r.compression_resultant_n!/1000).toFixed(3)} kN · pmax ${r.pressure_max_kpa?.toFixed(3)} kPa`,position:to([0,0],.65),componentId:plate.component_id});}
  window.dispatchEvent(new CustomEvent('geoai:elastic-results',{detail:{paths,componentIds:paths.map(()=>plate.component_id),colors,nodeMarkers:labels,arrowIndices:arrows,mode:'foundation-interface',focusComponentIds:a.geometry.objects.map(o=>o.component_id),fit:true,fitRange:3.2,fitPitch:-48,fitHeadingOffset:Math.PI*1.25,focus:to([0,0],-.05),label:computed?`Actual N/M declared-input calculation · pressure height ${scale} m/MPa; shear unsupported`:'Saved connection geometry · anchors declared, not measured; no calculated forces or pressure'}}));};
 if(!audit||!q)return <section className="mb-4 p-3" aria-label="Real connection engineering inputs">{error||'Loading saved connection evidence…'}</section>;
 const actual=audit.actual,ready=!dirty&&!blocked&&input?.status==='READY_FOR_EXPLICIT_AUTHORIZATION';
 const missingGroups:Record<string,{path:string;reason:string}[]>={};
 for(const m of assessment?.missing??[]){const anchor=q.anchors.findIndex(a=>m.path.startsWith('anchors.'+a.id+'.'));const group=anchor>=0?`A${anchor+1} · dimensions, material and tension spring`:m.path.startsWith('saved_geometry')?'Saved geometry and anchor positions':m.path.startsWith('mechanical')||m.path.startsWith('reference_plane')||m.path in audit.flags?'Mechanical assumptions and review':'Concrete contact model and limits';(missingGroups[group]??=[]).push(m);}
 const tasks=[{id:"geometry",name:"Geometry source"},{id:"contact",name:"Concrete contact model"},...q.anchors.map((anchor,index)=>({id:`anchor:${anchor.id}`,name:`Anchor ${index+1} properties`})),{id:"assumptions",name:"Assumptions and review"},{id:"review",name:"Validate and authorize"}];
 type TaskStep={key:string;title:string;content:React.ReactNode};
 const taskAnchor=task.startsWith("anchor:")?q.anchors.findIndex(anchor=>`anchor:${anchor.id}`===task):-1;
 const activeAnchor=q.anchors[Math.max(0,taskAnchor)];
 const updateAnchor=(value:Anchor)=>edit({...q,anchors:q.anchors.map((anchor,index)=>index===taskAnchor?value:anchor)});
 let steps:TaskStep[]=[];
 if(task==="geometry")steps=[{key:"saved_geometry_evidence",title:"Confirm where the geometry comes from",content:<><p className="text-xs text-muted-foreground">Document the source of the saved dimensions and anchor positions. Synthetic dimensions are not measured evidence.</p><EvidenceFields expanded label="Saved geometry evidence" value={q.saved_geometry_evidence} onChange={v=>edit({...q,saved_geometry_evidence:v})}/></>}];
 else if(task==="contact")steps=[
  {key:"concrete_material",title:"Identify the concrete",content:<label>Concrete material identification<input aria-label="Concrete material identification" value={q.concrete_material} onChange={e=>edit({...q,concrete_material:e.target.value})}/></label>},
  {key:"contact_model_justification",title:"Explain the contact model",content:<><p className="text-xs">Supported law: p = kc max(w, 0). Explain calibration, layers and why a homogeneous bed applies. Concrete strength and soil modulus do not automatically establish this stiffness.</p><label>Contact model justification<textarea aria-label="Contact model justification" rows={3} value={q.contact_model_justification} onChange={e=>edit({...q,contact_model_justification:e.target.value})}/></label></>},
  ...Object.entries(audit.contact_fields).map(([key,[label,why]])=>({key,title:label,content:<QuantityField label={label} why={why} value={q[key as keyof Inputs] as Quantity} onChange={v=>edit({...q,[key]:v})}/>}))];
 else if(taskAnchor>=0)steps=[
  {key:"material",title:"Identify this anchor's material",content:<label>Anchor material identification<input aria-label="Anchor material identification" value={activeAnchor.material} onChange={e=>updateAnchor({...activeAnchor,material:e.target.value})}/></label>},
  {key:"geometry_and_material_evidence",title:"Document the anchor source",content:<EvidenceFields expanded label="Anchor geometry and material evidence" value={activeAnchor.geometry_and_material_evidence} onChange={v=>updateAnchor({...activeAnchor,geometry_and_material_evidence:v})}/>},
  {key:"tension_load_path",title:"Explain the tension load path",content:<><p className="text-xs">Each anchor requires its own justified effective tension stiffness. Embedment length is not evidence of capacity; stiffness is not automatically calculated as EA/L.</p><label>Effective tension load path and stiffness model<textarea aria-label="Anchor tension load path" rows={3} value={activeAnchor.tension_load_path} onChange={e=>updateAnchor({...activeAnchor,tension_load_path:e.target.value})}/></label></>},
  ...Object.entries(audit.anchor_fields).map(([key,[label,why]])=>({key,title:label,content:<QuantityField label={label} why={why} value={activeAnchor[key as keyof Anchor] as Quantity} onChange={v=>updateAnchor({...activeAnchor,[key]:v})}/>}))];
 else if(task==="assumptions")steps=[
  {key:"reference_plane_assumption",title:"Confirm the reference plane",content:<label>Column-base reference-plane assumption<textarea aria-label="Reference-plane assumption" rows={3} value={q.reference_plane_assumption} onChange={e=>edit({...q,reference_plane_assumption:e.target.value})}/></label>},
  {key:"mechanical_evidence",title:"Document the mechanical assumptions",content:<EvidenceFields expanded label="Mechanical model evidence" value={q.mechanical_evidence} onChange={v=>edit({...q,mechanical_evidence:v})}/>},
  ...Object.entries(audit.flags).map(([key,text])=>({key,title:"Review this assumption explicitly",content:<label className="block"><input aria-label={key} type="checkbox" checked={q[key as keyof Inputs] as boolean} onChange={e=>edit({...q,[key]:e.target.checked})}/> {text}</label>}))];
 else steps=[{key:"review",title:"Validate the draft before authorization",content:<p className="text-sm">Saving validates the existing requirements against this exact model revision. Missing values stay missing. Moving through these screens does not mark inputs complete.</p>}];
 const current=steps[Math.min(step,steps.length-1)],taskIndex=Math.max(0,tasks.findIndex(value=>value.id===task));
 const focusTask=()=>requestAnimationFrame(()=>document.querySelector<HTMLElement>('[aria-label="Current engineering input step"] h4')?.focus());
 const chooseTask=(id:string)=>{focusTask();setTask(id);setStep(0);const index=q.anchors.findIndex(anchor=>`anchor:${anchor.id}`===id);if(index>=0)setAnchorIndex(index);};
 const advance=(direction:number)=>{focusTask();const next=step+direction;if(next>=0&&next<steps.length)setStep(next);else{const nextTask=tasks[taskIndex+direction];if(nextTask)chooseTask(nextTask.id);}};
 return <section aria-label="Real connection engineering inputs" className="mb-4 space-y-4 text-sm [&_input:not([type=checkbox])]:w-full [&_input]:rounded [&_input]:border [&_input]:border-border [&_input]:bg-background [&_input]:p-2 [&_select]:w-full [&_select]:rounded [&_select]:border [&_select]:border-border [&_select]:bg-background [&_select]:p-2 [&_textarea]:w-full [&_textarea]:rounded [&_textarea]:border [&_textarea]:border-border [&_textarea]:bg-background [&_textarea]:p-2 [&_summary]:cursor-pointer">
 <div><h3 className="font-semibold">Foundation connection</h3><p role="status" className="mt-2 text-xs text-amber-200">{geometryChanged||input?.status==='STALE'?"Needs refresh":dirty?"Draft changed — validate before use":assessment?.missing.length?"Needs inputs":ready?"Ready for explicit authorization":"Review saved inputs"}</p></div>
 <nav aria-label="Engineering input tasks"><label className="text-xs text-muted-foreground">Task {taskIndex+1} of {tasks.length}<select aria-label="Engineering task" value={task} onChange={e=>chooseTask(e.target.value)}>{tasks.map(value=><option value={value.id} key={value.id}>{value.name}</option>)}</select></label></nav>
 {taskAnchor>=0&&<label className="block text-xs">Anchor to inspect<select aria-label="Actual anchor to inspect" value={taskAnchor} onChange={e=>chooseTask(`anchor:${q.anchors[Number(e.target.value)].id}`)}>{q.anchors.map((anchor,index)=><option value={index} key={anchor.id}>Anchor {index+1}</option>)}</select></label>}
 <article aria-label="Current engineering input step" className="space-y-4 rounded border border-border bg-muted/10 p-4"><p className="text-xs text-muted-foreground">Step {Math.min(step,steps.length-1)+1} of {steps.length}</p><h4 tabIndex={-1} className="font-medium outline-none">{current.title}</h4>{current.content}</article>
 <div className="flex items-center justify-between gap-3"><button className="text-xs underline disabled:opacity-40" disabled={taskIndex===0&&step===0} onClick={()=>advance(-1)}>Back</button>{task!=="review"&&<button className="copilot-primary-action" onClick={()=>advance(1)}>{step===steps.length-1?"Next task":"Next"}</button>}</div>
 {task==="review"&&<><button className="copilot-primary-action" disabled={blocked} onClick={()=>void save()}>Save engineering draft and validate</button><p className="text-xs text-muted-foreground">Draft saves retain missing values and previous records. Only validation can establish input readiness.</p>
 {input&&<article aria-label="Actual contact authorization" className="rounded border border-border p-2"><p>Input #{input.id} · revision {input.model_revision_id} · {input.status}</p><details><summary>Exact proposal and input evidence</summary><p className="break-all">{input.result.input_sha256}</p><pre className="max-h-72 overflow-auto whitespace-pre-wrap break-all text-xs">{JSON.stringify(input.result.inputs,null,2)}</pre></details><label className="block"><input aria-label="Authorize actual N M contact" type="checkbox" disabled={!ready} checked={consent} onChange={e=>setConsent(e.target.checked)}/> Authorize only this exact reviewed N/M contact calculation</label><button disabled={!ready||!consent} onClick={()=>void run()}>Run authorized actual contact calculation</button></article>}
 </>}
 {result&&<article aria-label="Actual contact computed results" className="space-y-2 rounded border border-border p-2"><b>{stale?'STALE — results display disabled':result.status}</b><p>User-supplied properties and assumptions; physical adequacy NOT VERIFIED.</p><p>C {(result.result.compression_resultant_n!/1000).toFixed(6)} kN · pmax {result.result.pressure_max_kpa?.toFixed(6)} kPa · active area {result.result.active_contact_area_m2?.toFixed(6)} m²</p><p>Translation {(result.result.translation_down_m!*1000).toFixed(6)} mm · rotations [{result.result.rotations_east_north_rad?.map(v=>v.toFixed(9)).join(', ')}] rad</p>{result.result.anchors?.map(a=><p key={a.id}>{a.id}: T {(a.tension_n/1000).toFixed(6)} kN · opening {(a.opening_m*1000).toFixed(6)} mm</p>)}<p>Independent force / East-moment / North-moment residuals [{result.result.equilibrium_residual_si?.map(v=>v.toExponential(3)).join(', ')}] N / N·m / N·m</p><label>Pressure diagram scale [m/MPa]<input aria-label="Actual pressure diagram scale" type="number" min="0.01" max="2" step="0.05" value={scale} onChange={e=>setScale(Math.max(.01,Math.min(2,Number(e.target.value))))}/></label><button disabled={stale||busy} onClick={()=>view(true)}>Show actual N/M contact results</button><details><summary>Calculation and authorization evidence</summary><pre className="max-h-80 overflow-auto whitespace-pre-wrap break-all text-xs">{JSON.stringify(result,null,2)}</pre></details></article>}
 <details className="border-t border-border pt-3"><summary className="text-xs text-muted-foreground">Advanced requirements and saved evidence</summary><div className="mt-3 space-y-3 text-xs">
 {navigationNotice&&<p role="status" className="break-words">{navigationNotice}</p>}
 <p>{assessment?.missing.length ?? 0} missing fields in the saved assessment. Current unsaved edits are validated only when saved.</p>
 {Object.entries(missingGroups).map(([group,items])=><details key={group}><summary>{group} ({items.length})</summary>{items.map((item,index)=><p className="my-2 break-words" key={index}><b>{item.path}</b>: {item.reason}</p>)}</details>)}
 <details><summary>Saved geometry, loads and source provenance</summary><p>N {(actual.demand.compression_n/1000).toFixed(6)} kN compression · |V| {(Math.abs(actual.demand.horizontal_shear_east_n)/1000).toFixed(6)} kN · |M| {(Math.abs(actual.demand.moment_about_negative_north_nm)/1000).toFixed(6)} kN·m</p>{actual.geometry.objects.map(object=><p key={object.component_id} className="break-all">{object.name} · {object.size_m.join(" × ")} m · {object.component_id}</p>)}<p>Source interface #{actual.source_interface_analysis_id} · revision {actual.source_revision_id} · OpenSees {actual.demand.solver_version} · run {actual.demand.run_id}</p><p className="break-all">{actual.source_evidence_sha256}</p><p>Saved anchors are conceptual, not verified physical bolts. Prior 20 mm diameter and 300 mm embedment are synthetic declarations.</p><button className="mt-2 underline" disabled={blocked} onClick={()=>view()}>Fit actual connection geometry</button><button className="ml-3 underline" onClick={()=>window.dispatchEvent(new CustomEvent('geoai:elastic-results',{detail:null}))}>Show full saved model</button></details>
 </div></details>
 <p className="text-amber-200">NOT VERIFIED: horizontal shear transfer, anchor strength, concrete breakout, plate bending/prying, welds, footing/soil capacity and IS/US compliance.</p>{error&&<p role="alert">{error}</p>}
 </section>;
}

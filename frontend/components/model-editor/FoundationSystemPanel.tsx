"use client";
import {downloadFile} from "@/lib/download";

import {useEffect,useState} from 'react';

import {api,formatApiErrorMessage} from '@/lib/api';

import type {EditableModelEditor} from '@/hooks/useEditableModelEditor';
import type {EditableModelDocument} from '@/lib/types';
import FoundationVisualExplorer from './FoundationVisualExplorer';
import type {FoundationData,FoundationAlternative} from '@/lib/foundation-visual';
const EMPTY_ALTERNATIVES:FoundationAlternative[]=[];

type Inputs={classification:string;profile:string;jurisdiction:string;load_standard:string;factored_column_kn:number;factored_action_source:string;concrete_cylinder_mpa:number;concrete_cube_mpa:number;steel_yield_mpa:number;steel_modulus_mpa:number;concrete_unit_weight_kn_m3:number;steel_density_kg_m3:number;cover_mm:number;aggregate_mm:number;east_west:{diameter_mm:number;count:number};north_south:{diameter_mm:number;count:number};stiffness_kn_m3:number;undrained_strength_kpa:number;soil_global_factor:number;material_source:string;soil_source:string;detailing_source:string;reviewed_synthetic_patch:boolean};

type Computed=FoundationData;

type ReactionLink={project_id:number;model_revision_id:number;result_id:number;reviewed_exact_column_and_footing:boolean};

type Row={id:number;type:string;status:string;result:{inputs:{inputs:Inputs;reaction_link?:ReactionLink|null};proposal_sha256:string;computed:Computed}};

type Alternatives={scenarios:FoundationAlternative[]};

type History={fixture:Inputs;source_service_column_kn:number;records:Row[]};

const numeric=[['factored_column_kn','Independent factored column action kN'],['concrete_cylinder_mpa','Independent cylinder strength MPa'],['concrete_cube_mpa','Independent cube strength MPa'],['steel_yield_mpa','Steel yield MPa'],['steel_modulus_mpa','Steel modulus MPa'],['concrete_unit_weight_kn_m3','Concrete unit weight kN/m³'],['steel_density_kg_m3','Steel density kg/m³'],['cover_mm','Clear cover mm'],['aggregate_mm','Nominal maximum aggregate mm'],['stiffness_kn_m3','Winkler stiffness kN/m³'],['undrained_strength_kpa','Undrained shear strength kPa'],['soil_global_factor','Soil strength reference global factor']] as const;

const clear=()=>window.dispatchEvent(new CustomEvent('geoai:elastic-results',{detail:{clearMode:'foundation-integrated'}}));

function Content({editor,projectId}:{editor:EditableModelEditor;projectId:number}){

 const rid=editor.baseRevision?.id,study=!!editor.document?.metadata?.foundation_system,base=`/api/projects/${projectId}/engineering/foundation-system`;

 const blocked=editor.dirty||!!editor.platformPreview||!!editor.aiPreview||!!editor.comparison;

 const [candidate,setCandidate]=useState<FoundationAlternative|null>(null),[geometryConsent,setGeometryConsent]=useState(false),[geometryProposal,setGeometryProposal]=useState<{id:number;status:string;result:{proposal_sha256:string;proposed_document?:EditableModelDocument;approved_document?:EditableModelDocument;missing?:unknown[]}}|null>(null);
 const [link,setLink]=useState<ReactionLink|null>(null);

 const [h,setH]=useState<History|null>(null),[q,setQ]=useState<Inputs|null>(null),[dirty,setDirty]=useState(false),[consent,setConsent]=useState(false),[review,setReview]=useState(false),[busy,setBusy]=useState(false),[error,setError]=useState(''),[alts,setAlts]=useState<Alternatives|null>(null);

 useEffect(()=>{let active=true;if(study&&rid)api.get<History>(`${base}?model_revision_id=${rid}`).then(v=>{if(active){setH(v);setQ(v.records[0]?.result.inputs.inputs??v.fixture);setLink(v.records[0]?.result.inputs.reaction_link??null);}}).catch(e=>{if(active)setError(formatApiErrorMessage(e));});return()=>{active=false;clear();};},[base,rid,study]);

 const proposal=h?.records.find(r=>r.type==='FOUNDATION_SYSTEM_PROPOSAL'),result=h?.records.find(r=>r.type==='FOUNDATION_SYSTEM_RESULT');

 const stale=dirty||blocked||result?.status==='STALE',computed=result?.result.computed;

 useEffect(()=>{if(stale)clear();},[stale]);

 const edit=(v:Inputs)=>{setQ(v);setDirty(true);setConsent(false);setReview(false);setAlts(null);clear();};

 const task=async(action:()=>Promise<void>)=>{setBusy(true);setError('');try{await action();}catch(e){setError(formatApiErrorMessage(e));}finally{setBusy(false);}};

 const reload=async()=>{setH(await api.get<History>(`${base}?model_revision_id=${rid}`));setDirty(false);setConsent(false);setReview(false);clear();};

 const compare=()=>void task(async()=>{if(!result||stale)return;setAlts(await api.post<Alternatives>(`${base}/alternatives`,{model_revision_id:rid,inputs:result.result.inputs.inputs,reaction_link:result.result.inputs.reaction_link??null}));});
 const previewGeometry=()=>void task(async()=>{
  if(!candidate||!computed||!editor.document||blocked||stale)return;
  const document=editor.document,footing=document.components.find(c=>c.id===computed.geometry.footing_id);
  const cad=footing?.metadata?.drawing_cad as {input?:Record<string,unknown>}|undefined;
  const model=document.metadata?.drawing_cad_model as {inputs?:{connections?:unknown[]}}|undefined;
  if(!cad?.input||!model?.inputs?.connections)throw new Error('Owned CAD source and explicit attachment evidence required');
  const audit=await api.get<{source_reference_id:number;review_record_id:number}>(`/api/projects/${projectId}/engineering/drawing-cad?model_revision_id=${rid}`);
  const proposed=await api.post<NonNullable<typeof geometryProposal>>(`/api/projects/${projectId}/engineering/drawing-cad/preview`,{model_revision_id:rid,source_reference_id:audit.source_reference_id,review_record_id:audit.review_record_id,inputs:{classification:'SYNTHETIC_VERIFICATION',items:[{...cad.input,operation:'update_generated',size_east_mm:candidate.width_m*1000,size_north_mm:candidate.width_m*1000,bottom_mm:(computed.geometry.column_face_up_m-candidate.thickness_m)*1000,top_mm:computed.geometry.column_face_up_m*1000,plan_policy:'EXPLICIT_GEOMETRY_OVERRIDE',override_reason:'Explicit reviewed synthetic foundation comparison. Original CAD source remains unchanged; no engineering approval.'}],connections:model.inputs.connections,reviewed_by:'Local foundation alternative review',geometry_only_no_analysis:true}});
  setGeometryProposal(proposed);setGeometryConsent(false);
  if(proposed.result.proposed_document)editor.setPlatformPreview({source:document,document:proposed.result.proposed_document,label:'Foundation CAD alternative — explicit authorization required'});
 });
 const applyGeometry=()=>void task(async()=>{
  if(!geometryConsent||!geometryProposal||!editor.platformPreview||editor.dirty)return;
  const approved=await api.post<NonNullable<typeof geometryProposal>>(`/api/projects/${projectId}/engineering/drawing-cad/authorize`,{proposal_id:geometryProposal.id,proposal_sha256:geometryProposal.result.proposal_sha256,authorize_geometry:true});
  if(approved.result.approved_document){editor.setPlatformPreview(null);editor.commit(approved.result.approved_document);setGeometryProposal(null);setGeometryConsent(false);setCandidate(null);setError('Authorized geometry is an unsaved draft. Save model, then review and recalculate. Reinforcement inputs were not automatically changed.');}
 });

 const download=()=>void task(async()=>{await downloadFile(`${base}/report/${result!.id}`,`foundation-${projectId}-${result!.id}.html`);});

 return <section aria-label="Integrated foundation workflow" data-busy={busy} className="mb-4 space-y-3 rounded border border-border p-3 text-sm [&_input:not([type=checkbox])]:w-full [&_input]:bg-background [&_select]:w-full [&_select]:bg-background [&_textarea]:w-full [&_textarea]:bg-background [&_button]:rounded [&_button]:border [&_button]:p-2">

 <h3 className="font-semibold">Foundation engineering</h3><p className="text-xs text-muted-foreground">Synthetic review · saved CAD identities · no engineering approval</p>

 {!study?<button disabled={busy||blocked||!rid||projectId!==804} onClick={()=>void task(async()=>{const v=await api.post<{project_id:number}>(`${base}/copy`,{model_revision_id:rid,authorize_separate_study:true});window.location.assign(`/projects/${v.project_id}/workspace`);})}>Create separate foundation study from 804</button>:<>

 {computed&&q&&<FoundationVisualExplorer key={result!.id} data={computed} cover={result!.result.inputs.inputs.cover_mm} stale={stale} alternatives={alts?.scenarios??EMPTY_ALTERNATIVES} onCompare={compare} onReviewAlternative={v=>{setCandidate(v);setGeometryProposal(null);setGeometryConsent(false);}} busy={busy}/>}
 {candidate&&<section aria-label="Review foundation alternative" className="space-y-2 rounded border border-amber-300/40 p-2"><b>Review unsaved alternative</b><p className="text-xs">{candidate.width_m.toFixed(3)} m square × {candidate.thickness_m.toFixed(3)} m. Geometry preview, exact authorization and Save model are separate steps. Bar-count comparisons never change saved reinforcement automatically.</p><button disabled={busy||blocked||stale} onClick={previewGeometry}>Preview CAD alternative</button>{geometryProposal&&<><p className="text-xs">{geometryProposal.status}</p>{geometryProposal.result.missing&&<pre className="max-h-32 overflow-auto text-xs">{JSON.stringify(geometryProposal.result.missing,null,2)}</pre>}<label className="block text-xs"><input type="checkbox" aria-label="Authorize exact alternative geometry" checked={geometryConsent} onChange={e=>setGeometryConsent(e.target.checked)}/>Authorize the exact CAD geometry preview only</label><button disabled={!geometryConsent||!editor.platformPreview||busy||editor.dirty} onClick={applyGeometry}>Apply authorized alternative draft</button></>}<button onClick={()=>{editor.setPlatformPreview(null);setGeometryProposal(null);setCandidate(null);setGeometryConsent(false);}}>Cancel alternative review</button>{q&&candidate.layers&&<button disabled={blocked||busy} onClick={()=>edit({...q,east_west:{count:candidate.layers![0].bar_count,diameter_mm:candidate.layers![0].bar_diameter_mm},north_south:{count:candidate.layers![1].bar_count,diameter_mm:candidate.layers![1].bar_diameter_mm}})}>Use compared reinforcement as input draft</button>}</section>}
 <details open={!computed}><summary className="cursor-pointer">Inputs, proposals and authorization</summary>
 <p>Saved service column action {h?.source_service_column_kn??'…'} kN. Soil contact uses gross service actions including declared footing weight. RC cuts use separately declared factored net pressure. No code load factors are supplied automatically.</p>

 {q&&<fieldset disabled={busy||blocked} className="space-y-3"><label>Code and edition<select aria-label="Foundation code and edition" value={q.profile} onChange={e=>edit({...q,profile:e.target.value})}>{['IS456-2000-A1A2','ACI318-14','ACI318-19','ACI318-25'].map(v=><option key={v}>{v}</option>)}</select></label><label>Jurisdiction<input aria-label="Foundation jurisdiction" value={q.jurisdiction} onChange={e=>edit({...q,jurisdiction:e.target.value})}/></label><label>Load standard context<select aria-label="Foundation load standard" value={q.load_standard} onChange={e=>edit({...q,load_standard:e.target.value})}>{['MANUALLY_DECLARED_NO_AUTOMATIC_COMBINATIONS','ASCE7-16','ASCE7-22','IS875-1987'].map(v=><option key={v}>{v}</option>)}</select></label><p>ASCE/IS automatic combinations disabled. ACI 2019/2025 checks disabled; selecting them never substitutes 2014 formulas. IS profile uses the published 2000 scan with amendments 1 and 2; later adoption/amendments require review.</p>

 <details><summary>Actions, materials, soil and detailing inputs</summary>{numeric.map(([key,label])=><label className="block" key={key}>{label}<input aria-label={label} type="number" step="any" value={Number.isFinite(q[key])?q[key]:''} onChange={e=>edit({...q,[key]:e.target.value===''?NaN:Number(e.target.value)})}/></label>)}{(['east_west','north_south'] as const).map(key=><div key={key}>{(['diameter_mm','count'] as const).map(prop=><label key={prop}>{key} {prop}<input aria-label={`${key} ${prop}`} type="number" value={Number.isFinite(q[key][prop])?q[key][prop]:''} onChange={e=>edit({...q,[key]:{...q[key],[prop]:e.target.value===''?NaN:Number(e.target.value)}})}/></label>)}</div>)}{(['factored_action_source','material_source','soil_source','detailing_source'] as const).map(key=><label className="block" key={key}>{key.replaceAll('_',' ')}<textarea aria-label={`Foundation ${key}`} value={q[key]} onChange={e=>edit({...q,[key]:e.target.value})}/></label>)}</details>

 <details><summary>Optional saved OpenSees reaction mapping</summary><label><input aria-label="Use saved reaction mapping" type="checkbox" checked={link!==null} onChange={e=>{setLink(e.target.checked?{project_id:797,model_revision_id:112,result_id:464,reviewed_exact_column_and_footing:false}:null);edit(q);}}/>Link an owned current transported support reaction</label><p>Exact CAD column/footing identities and reference planes must match. Current reference reactions contain moments and shear: these remain outside the uniform-pressure RC profile and will be rejected, never silently discarded.</p>{link&&<>{(['project_id','model_revision_id','result_id'] as const).map(key=><label key={key}>Reaction {key}<input aria-label={`Reaction ${key}`} type="number" value={link[key]} onChange={e=>{setLink({...link,[key]:Number(e.target.value)});edit(q);}}/></label>)}<label><input type="checkbox" aria-label="Review exact reaction mapping" checked={link.reviewed_exact_column_and_footing} onChange={e=>{setLink({...link,reviewed_exact_column_and_footing:e.target.checked});edit(q);}}/>Reviewed exact saved column, footing and reference mapping</label></>}</details>

 <label><input type="checkbox" aria-label="Review foundation assumptions" checked={review} onChange={e=>setReview(e.target.checked)}/>Reviewed synthetic direct patch, independent actions/materials/soil and straight orthogonal mats; no actual connection or site approval</label><button disabled={!review} onClick={()=>void task(async()=>{await api.post(`${base}/preview`,{model_revision_id:rid,inputs:q,reaction_link:link});await reload();})}>Preview integrated foundation calculation</button><button disabled={!review} onClick={()=>void task(async()=>setAlts(await api.post<Alternatives>(`${base}/alternatives`,{model_revision_id:rid,inputs:q,reaction_link:link})))}>Compare foundation alternatives</button></fieldset>}

 {proposal&&<details><summary>Exact proposal #{proposal.id} · {dirty?'STALE':proposal.status}</summary><p>Review the complete inputs, assumptions, disabled checks and numerical preview before authorizing.</p><pre className="max-h-72 overflow-auto whitespace-pre-wrap break-all text-xs">{JSON.stringify(proposal.result,null,2)}</pre></details>}

 <label><input type="checkbox" aria-label="Authorize exact foundation calculation" checked={consent} disabled={busy||blocked||dirty||proposal?.status!=='AWAITING_EXPLICIT_REVIEW'} onChange={e=>setConsent(e.target.checked)}/>Authorize this exact calculation only; no model change or engineering safety approval</label><button disabled={busy||blocked||dirty||!consent} onClick={()=>void task(async()=>{await api.post(`${base}/authorize`,{proposal_id:proposal!.id,proposal_sha256:proposal!.result.proposal_sha256,authorize_calculation:true});await reload();})}>Save reviewed foundation result</button>

</details>
 <details><summary className="cursor-pointer">Reports, methods and immutable evidence</summary>{result&&<><button disabled={stale||busy} onClick={download}>Download calculation report</button><p className="text-xs">Saved result #{result.id} · {stale?'Stale':result.status}. Full inputs, source hashes, formulas and limitations are retained.</p><pre className="max-h-80 overflow-auto whitespace-pre-wrap break-all text-xs">{JSON.stringify(result,null,2)}</pre></>}<p className="text-xs">Synthetic direct-column patch only. Site settlement, actual connection, durability and complete detailing remain unverified. A subset passing is not engineering approval or a safety certificate.</p></details></>}{error&&<p role="alert">{error}</p>}</section>;

}

export default function FoundationSystemPanel(props:{editor:EditableModelEditor;projectId:number}){return <Content key={`${props.projectId}:${props.editor.baseRevision?.id}`} {...props}/>;}


export type {Inputs as FoundationInputs,ReactionLink};

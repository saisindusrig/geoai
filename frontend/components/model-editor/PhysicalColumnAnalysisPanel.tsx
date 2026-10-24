"use client";
import {useEffect,useRef,useState} from "react";
import {api,formatApiErrorMessage} from "@/lib/api";
import {Button} from "@/components/ui/button";
import {Input} from "@/components/ui/input";
import type {EditableModelEditor} from "@/hooks/useEditableModelEditor";

type Geometry={component_id:string;name:string;length_m:number;width_m:number;depth_m:number;base_enu_m:number[];head_enu_m:number[];axis_enu:number[];rotation_deg:number[];component_sha256:string};
type Inputs={purpose:string;material_name:string;material_source:string;elastic_modulus_pa:number;section_width_m:number;section_depth_m:number;section_source:string;compression_n:number;load_source:string;support_stiffness_n_per_m:number;support_source:string;elements:number;solver_units:string;isolated_axial_only:boolean;section_kind:string;support_kind:string};
type Result={status:string;run_id:string;solver_version:string;error?:string;engineering_inputs:Inputs;engineering_inputs_sha256:string;input_record_id:number;model_document_sha256:string;physical_component:Geometry;solver:{executable_sha256:string};values_si?:{column_shortening_m:number;spring_settlement_m:number;total_displacement_m:number;compression_stress_pa:number;reaction_n:number};elements?:{id:number;axial_force_n:number}[];nodes?:{id:number;z_m:number;displacement_m:number}[];comparisons?:Record<string,{computed:number;reference:number;relative_error:number;passed:boolean}>;force_residual_n:number;independent_reference?:{formulas:Record<string,string>};verification_suite?:{status:string}};
type Row={id:number;model_revision_id:number;status:string;result:Result};
type SavedInput={id:number;model_revision_id:number;status:string;result:{engineering_inputs:Inputs}};
type Data={physical_component:Geometry;latest_input:SavedInput|null;analyses:Row[]};
const numeric=[['E','Elastic modulus · GPa'],['width','Section width · m'],['depth','Section depth · m'],['load','Head compression · kN'],['spring','Axial support stiffness · MN/m']] as const;
const text=[['material','Material identification'],['materialSource','Material source'],['sectionSource','Section source'],['loadSource','Load source'],['supportSource','Support source']] as const;
type Draft=Record<typeof numeric[number][0]|typeof text[number][0]|'purpose'|'elements'|'units',string>&{ack:boolean};
const empty:Draft={E:'',width:'',depth:'',load:'',spring:'',material:'',materialSource:'',sectionSource:'',loadSource:'',supportSource:'',purpose:'',elements:'2',units:'SI',ack:false};
function fromInputs(i:Inputs):Draft{return{E:String(i.elastic_modulus_pa/1e9),width:String(i.section_width_m),depth:String(i.section_depth_m),load:String(i.compression_n/1000),spring:String(i.support_stiffness_n_per_m/1e6),material:i.material_name,materialSource:i.material_source,sectionSource:i.section_source,loadSource:i.load_source,supportSource:i.support_source,purpose:i.purpose,elements:String(i.elements),units:i.solver_units,ack:i.isolated_axial_only};}
function normalize(d:Draft):Inputs{return{purpose:d.purpose,material_name:d.material.trim(),material_source:d.materialSource.trim(),elastic_modulus_pa:Number(d.E)*1e9,section_width_m:Number(d.width),section_depth_m:Number(d.depth),section_source:d.sectionSource.trim(),compression_n:Number(d.load)*1000,load_source:d.loadSource.trim(),support_stiffness_n_per_m:Number(d.spring)*1e6,support_source:d.supportSource.trim(),elements:Number(d.elements),solver_units:d.units,isolated_axial_only:d.ack,section_kind:'solid_rectangle',support_kind:'axial_linear_spring'};}
function same(a:Inputs,b:Inputs){return Object.keys(a).every(key=>a[key as keyof Inputs]===b[key as keyof Inputs]);}

export default function PhysicalColumnAnalysisPanel({editor,projectId}:{editor:EditableModelEditor;projectId:number}){
  const selected=editor.selectedIds.length===1 ? editor.selected : null;
  const columns=editor.baseRevision?.document?.components.filter(c=>/^industrial-platform-5x3:column-(ne|nw|se|sw)$/.test(c.id)&&c.category==='column')??[];
  const componentId=columns.some(c=>c.id===selected?.id)?selected!.id:'';
  const revisionId=editor.baseRevision?.id;
  const key=`${projectId}:${revisionId}:${componentId}`;
  const current=useRef(key);
  const [state,setState]=useState<{key:string;data:Data}|null>(null),[draft,setDraft]=useState<Draft>({...empty});
  const [busy,setBusy]=useState(false),[error,setError]=useState<string|null>(null);
  useEffect(()=>{current.current=key;},[key]);
  useEffect(()=>{
    if(!revisionId||!componentId)return;
    let active=true;
    void api.get<Data>(`/api/projects/${projectId}/engineering/opensees/columns?model_revision_id=${revisionId}&component_id=${encodeURIComponent(componentId)}`).then(data=>{
      if(!active)return;
      setState({key,data});setDraft(data.latest_input ? fromInputs(data.latest_input.result.engineering_inputs):{...empty});setError(null);
    }).catch(reason=>{if(active){setState(null);setError(formatApiErrorMessage(reason));}});
    return()=>{active=false;};
  },[projectId,revisionId,componentId,key]);
  const data=state?.key===key?state.data:null;
  const saved=data?.latest_input;
  const analysis=data?.analyses[0];
  const result=analysis?.result;
  const dirtyInputs=!!saved&&!same(normalize(draft),saved.result.engineering_inputs);
  useEffect(()=>{
    const notify=()=>window.dispatchEvent(new CustomEvent('geoai:column-engineering-inputs-dirty',{detail:{componentId,dirty:dirtyInputs}}));
    notify();window.addEventListener('geoai:request-column-input-draft-status',notify);
    return()=>{window.removeEventListener('geoai:request-column-input-draft-status',notify);window.dispatchEvent(new CustomEvent('geoai:column-engineering-inputs-dirty',{detail:{componentId,dirty:false}}));};
  },[componentId,dirtyInputs]);
  const dirtyModel=editor.dirty||!!editor.platformPreview||!!editor.aiPreview||!!editor.comparison;
  const stale=!!analysis&&(analysis.status==='STALE'||dirtyModel||dirtyInputs||analysis.model_revision_id!==revisionId||result!.input_record_id!==saved?.id);
  const valid=!!draft.purpose&&draft.ack&&numeric.every(([k])=>draft[k].trim()!==''&&Number.isFinite(Number(draft[k]))&&Number(draft[k])>0)&&text.every(([k])=>draft[k].trim().length>=3);
  const save=async()=>{
    if(!data||!componentId||!revisionId)return;
    setBusy(true);setError(null);
    try{
      const next=await api.post<SavedInput>(`/api/projects/${projectId}/engineering/opensees/columns/inputs`,{model_revision_id:revisionId,component_id:componentId,base_input_id:saved?.id??null,...normalize(draft)});
      if(current.current===key){setState({key,data:{...data,latest_input:next}});setDraft(fromInputs(next.result.engineering_inputs));}
    }catch(reason){if(current.current===key)setError(formatApiErrorMessage(reason));}finally{setBusy(false);}
  };
  const run=async()=>{
    if(!data||!saved||dirtyInputs)return;
    setBusy(true);setError(null);
    try{
      const next=await api.post<Row>(`/api/projects/${projectId}/engineering/opensees/columns/run`,{model_revision_id:revisionId,component_id:componentId,input_record_id:saved.id});
      if(current.current===key)setState({key,data:{...data,analyses:[next,...data.analyses]}});
    }catch(reason){if(current.current===key)setError(formatApiErrorMessage(reason));}finally{setBusy(false);}
  };
  const download=async(name:string)=>{
    if(!analysis)return;
    try{const r=await api.get<{contents:string}>(`/api/projects/${projectId}/engineering/opensees/columns/${analysis.id}/artifacts/${name}`);const u=URL.createObjectURL(new Blob([r.contents],{type:'text/plain'}));const a=document.createElement('a');a.href=u;a.download=name;a.click();URL.revokeObjectURL(u);}catch(reason){setError(formatApiErrorMessage(reason));}
  };
  const change=(k:keyof Draft,v:string|boolean)=>setDraft(d=>({...d,[k]:v}));
  return <section aria-label="Physical column analysis" className="space-y-3 border border-border p-3">
    <h3 className="text-xs font-semibold">Analyze saved physical column</h3>
    <p className="text-[10px] text-amber-200">Engineering approval and IS/US code checks DISABLED. Connections, foundations, bending and buckling UNSUPPORTED.</p>
    <label className="block text-[11px]">Saved 3D column<select aria-label="Saved physical column" className="mt-1 w-full border border-border bg-background p-1" disabled={busy} value={componentId} onChange={e=>editor.select(e.target.value)}><option value="">Select one saved column</option>{columns.map(c=><option key={c.id} value={c.id}>{c.name}</option>)}</select></label>
    {!componentId&&<p className="text-[11px] text-muted-foreground">Select one column in the 3D viewer, Layers, or this list. Engineering inputs are never inferred from display materials.</p>}
    {error&&<p role="alert" className="text-xs text-destructive">{error}</p>}
    {data&&<>
      <div aria-label="Saved column geometry" className="space-y-1 text-[10px]"><p className="break-all">{data.physical_component.component_id} · revision #{revisionId}</p><p>Length {data.physical_component.length_m.toFixed(6)} m · envelope {data.physical_component.width_m.toFixed(4)} × {data.physical_component.depth_m.toFixed(4)} m</p><p>Base ENU [{data.physical_component.base_enu_m.map(v=>v.toFixed(4)).join(', ')}] m</p><p>Head ENU [{data.physical_component.head_enu_m.map(v=>v.toFixed(4)).join(', ')}] m · axis [0, 0, 1]</p><p>Saved rotation [{data.physical_component.rotation_deg.join(', ')}]° · geometry consistency validated; engineering unverified</p></div>
      {dirtyModel&&<p role="status" className="text-[11px] text-amber-200">Model changed or preview active. Save the revision before assigning inputs or running.</p>}
      <details open={!saved} className="space-y-2 text-[11px]"><summary>Explicit material, section, load and support inputs</summary>
        <p className="text-[10px] text-muted-foreground">Only a declared uniform solid rectangle matching the saved envelope, centered head compression and a prescribed linear axial spring are supported. No hidden load combinations or material strength.</p>
        <label className="block">Input purpose<select aria-label="Column input purpose" className="mt-1 w-full border border-border bg-background p-1" value={draft.purpose} disabled={busy} onChange={e=>change('purpose',e.target.value)}><option value="">Choose purpose</option><option value="VERIFICATION_ONLY">Verification data only</option><option value="ENGINEER_INPUT_UNAPPROVED">Engineer supplied · unapproved</option></select></label>
        <div className="grid grid-cols-2 gap-2">{numeric.map(([k,label])=><label key={k} className="text-[10px]">{label}<Input aria-label={`Column ${label}`} inputMode="decimal" value={draft[k]} disabled={busy} className="mt-1 h-8 text-xs" onChange={e=>change(k,e.target.value)}/></label>)}</div>
        {text.map(([k,label])=><label key={k} className="block text-[10px]">{label}<Input aria-label={`Column ${label}`} value={draft[k]} disabled={busy} className="mt-1 h-8 text-xs" onChange={e=>change(k,e.target.value)}/></label>)}
        <div className="grid grid-cols-2 gap-2"><label>Segments<select aria-label="Column segments" disabled={busy} className="mt-1 w-full border border-border bg-background p-1" value={draft.elements} onChange={e=>change('elements',e.target.value)}>{[1,2,4].map(n=><option key={n}>{n}</option>)}</select></label><label>Solver units<select aria-label="Column solver units" disabled={busy} className="mt-1 w-full border border-border bg-background p-1" value={draft.units} onChange={e=>change('units',e.target.value)}><option>SI</option><option>N-mm</option></select></label></div>
        <label className="flex gap-2 text-[10px]"><input type="checkbox" aria-label="Confirm isolated axial idealization" checked={draft.ack} disabled={busy} onChange={e=>change('ack',e.target.checked)}/><span>I explicitly declare this solid section and isolated axial idealization. Surrounding components and their load transfer are excluded.</span></label>
        <Button size="sm" variant="secondary" onClick={()=>void save()} disabled={!valid||busy||dirtyModel}>Save column engineering inputs</Button>
      </details>
      {saved&&<p className="text-[10px] text-muted-foreground">Input revision #{saved.id} · {saved.result.engineering_inputs.purpose==='VERIFICATION_ONLY'?'VERIFICATION DATA ONLY · not project design values':'Engineer inputs · unapproved'} · {saved.result.engineering_inputs.material_name}{saved.status==='STALE'?' · stale geometry association':''}</p>}
      <Button size="sm" className="w-full" variant="secondary" onClick={()=>void run()} disabled={!saved||saved.status==='STALE'||dirtyInputs||dirtyModel||busy}>{busy?'Processing local column analysis…':'Run selected column in OpenSees'}</Button>
      {dirtyInputs&&<p role="status" className="text-[11px] text-amber-200">Engineering inputs changed. Save a new input revision; previous results are stale.</p>}
      {analysis&&<div className="space-y-2" aria-label="Physical column solver result">
        <p role="status" className={stale?'text-xs text-amber-200':'text-xs text-primary'}>{stale?'STALE · geometry or engineering inputs changed':`${result!.status} · isolated axial response only`}</p>
        <p className="text-[10px]">Result model #{analysis.model_revision_id} · input #{result!.input_record_id} · OpenSees {result!.solver_version}</p>
        {result!.error&&<p role="alert" className="text-xs text-destructive">{result!.error}</p>}
        {result!.status==='VERIFIED'&&result!.values_si&&<>
          <dl aria-label="Computed physical column results" className="space-y-1 text-[11px]">{([
            ['Column shortening',result!.values_si.column_shortening_m*1000,'mm'],['Support translation',result!.values_si.spring_settlement_m*1000,'mm'],['Head displacement',result!.values_si.total_displacement_m*1000,'mm'],['Compression stress',result!.values_si.compression_stress_pa/1e6,'MPa'],['Upward reaction',result!.values_si.reaction_n/1000,'kN']] as const).map(([label,v,unit])=><div key={label} className="flex justify-between gap-2"><dt>{label}</dt><dd className="font-data">{v.toFixed(7)} {unit}</dd></div>)}</dl>
          <svg aria-label="Physical column computed displacement" viewBox="0 0 290 230" className="w-full border border-border text-primary"><text x="8" y="15" fontSize="9" fill="currentColor">Physical axis + computed mesh · deformation ×100</text><line x1="65" x2="65" y1="35" y2="175" stroke="currentColor" strokeDasharray="4 3"/><polyline points={(result!.nodes??[]).filter(n=>n.id!==1).map(n=>`120,${175-140*(n.z_m+n.displacement_m*100)/result!.physical_component.length_m}`).join(' ')} fill="none" stroke="currentColor" strokeWidth="2"/>{(result!.nodes??[]).filter(n=>n.id!==1).map(n=><g key={n.id}><circle cx="120" cy={175-140*(n.z_m+n.displacement_m*100)/result!.physical_component.length_m} r="3" fill="currentColor"/><text x="132" y={178-140*(n.z_m+n.displacement_m*100)/result!.physical_component.length_m} fontSize="9" fill="currentColor">z {n.z_m.toFixed(3)} m: {(-n.displacement_m*1000).toFixed(5)} mm ↓</text></g>)}<text x="8" y="210" fontSize="9" fill="currentColor">Dashed physical axis offset for comparison; z from base</text></svg>
          <p className="text-[10px]">{result!.elements?.map(e=>`E${e.id}: ${(e.axial_force_n/1000).toFixed(4)} kN`).join(' · ')} · negative = compression</p>
          <p className="text-[10px]">Equilibrium residual {result!.force_residual_n.toExponential(3)} N · existing benchmark {result!.verification_suite?.status}</p>
          <details className="text-[10px]"><summary>Independent calculation and solver evidence</summary><p>P L/(E A) + P/k · stress P/A · reaction P. Separate two-DOF stiffness calculation also checked.</p>{Object.entries(result!.comparisons??{}).map(([name,c])=><p key={name}>{name}: relative error {c.relative_error.toExponential(3)} · {c.passed?'matched reference':'failed'}</p>)}<p className="break-all">Run {result!.run_id}</p><p className="break-all">Component SHA-256 {result!.physical_component.component_sha256}</p><p className="break-all">Model SHA-256 {result!.model_document_sha256}</p><p className="break-all">Inputs SHA-256 {result!.engineering_inputs_sha256}</p><p className="break-all">Executable SHA-256 {result!.solver.executable_sha256}</p><div className="flex flex-wrap gap-2">{['model.tcl','nodes.tsv','forces.tsv','summary.tsv','stdout.txt','stderr.txt','manifest.json'].map(name=><button key={name} className="text-primary underline" onClick={()=>void download(name)}>{name}</button>)}</div></details>
        </>}
      </div>}
    </>}
  </section>;
}

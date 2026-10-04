"use client";
import { useEffect, useMemo, useRef, useState } from "react";
import type { EditableModelEditor } from "@/hooks/useEditableModelEditor";
import type { Project } from "@/lib/types";
import { api, formatApiErrorMessage } from "@/lib/api";
import { sectionGeometry, analyseSupports, designProfile, sampleSection, type AnalysisPlacement, type GroundAnalysisSample } from "@/lib/editor-analysis";
import { useProjectStore } from "@/stores/projectStore";
import type { AnalysisClip } from "@/lib/editor-clipping";

type Station = { chainage_m:number; longitude:number; latitude:number; ground_elevation_m:number|null; proposed_elevation_m:number|null; grade_percent:number|null; source:string; terrain_version_id:number|null; sample_status:string };
type Analysis = { id:number;type:string;status:string;model_revision_id:number;terrain_version_id:number|null;algorithm_version:string;result:{stations?:Station[]} };
const tabs=["QUANTITIES","PROFILE","SECTION","CONFLICTS","VALIDATION","LOG"];
const show=(value:unknown,unit="")=>typeof value === "number" && Number.isFinite(value) ? `${value.toFixed(3)} ${unit}` : "Unavailable";
export default function EngineeringDockPanel({editor,project,initialTab="QUANTITIES"}:{editor:EditableModelEditor;project:Project;initialTab?:string}) {
  const [tab,setTab]=useState(initialTab),[analyses,setAnalyses]=useState<Analysis[]>([]),[evidence,setEvidence]=useState<Record<string,unknown>|null>(null),[logs,setLogs]=useState<{id:number;action:string;timestamp:string}[]>([]);
  const [error,setError]=useState<string|null>(null),[busy,setBusy]=useState(false),[interval,setInterval]=useState(20);
  const [east,setEast]=useState(0),[north,setNorth]=useState(0),[heading,setHeading]=useState(0);
  const [clip,setClip]=useState<AnalysisClip>({mode:"off",value:0,size:50});
  const [clearances,setClearances]=useState<Awaited<ReturnType<typeof analyseSupports>>>([]);
  const [clearanceSnapshot,setClearanceSnapshot]=useState<string|null>(null);
  const [designStations,setDesignStations]=useState<{snapshot:string;profile:number;rows:Station[]}|null>(null);
  const [sectionGround,setSectionGround]=useState<Awaited<ReturnType<typeof sampleSection>>>([]),[sectionSnapshot,setSectionSnapshot]=useState<string|null>(null);
  const underground=useProjectStore(state=>state.undergroundView);
  const generation=useRef(0);
  useEffect(()=>()=>{generation.current++;},[project.id,editor.document,editor.baseRevision?.id]);
  useEffect(()=>{
    let active=true;
    const refresh=()=>{void Promise.all([api.get<Analysis[]>(`/api/projects/${project.id}/engineering/analyses`),api.get<Record<string,unknown>>(`/api/projects/${project.id}/engineering/evidence`),api.get<{id:number;action:string;timestamp:string}[]>(`/api/projects/${project.id}/engineering/log`)]).then(([a,e,l])=>{if(active){setAnalyses(a);setEvidence(e);setLogs(l);}}).catch(reason=>{if(active)setError(formatApiErrorMessage(reason));});};
    const terrainChanged=()=>{generation.current++;setClearanceSnapshot(null);setSectionSnapshot(null);setDesignStations(null);refresh();};
    refresh();window.addEventListener("geoai:terrain-changed",terrainChanged);
    return()=>{active=false;window.removeEventListener("geoai:terrain-changed",terrainChanged);};
  },[project.id]);
  const segments=useMemo(()=>editor.document ? sectionGeometry(editor.document,east,north,heading) : [],[editor.document,east,north,heading]);
  const sectionKey=JSON.stringify([editor.document,east,north,heading]);
  const sectionPoints=[...segments.flatMap(segment=>segment.points),...sectionGround.filter(row=>row.elevation!==null).map(row=>[row.offset,row.elevation!] as [number,number])];
  const minX=sectionPoints.length?Math.min(...sectionPoints.map(point=>point[0])):0,maxX=sectionPoints.length?Math.max(...sectionPoints.map(point=>point[0])):1;
  const minZ=sectionPoints.length?Math.min(...sectionPoints.map(point=>point[1])):0,maxZ=sectionPoints.length?Math.max(...sectionPoints.map(point=>point[1])):1;
  const sectionScale=Math.min(860/Math.max(1,maxX-minX),90/Math.max(1,maxZ-minZ));
  const profile=analyses.find(item=>item.type === "PROFILE");
  const snapshot=JSON.stringify(editor.document);
  const stations=designStations?.snapshot===snapshot && designStations.profile===profile?.id ? designStations.rows : profile?.result.stations ?? [];
  useEffect(()=>{
    if(!profile || !editor.document || editor.dirty || profile.model_revision_id!==editor.baseRevision?.id)return;
    let active=true;
    const document=editor.document;
    void api.get<{placement:AnalysisPlacement|null}>(`/api/projects/${project.id}/engineering/placements/${profile.model_revision_id}`).then(async({placement})=>{
      if(!placement)return;
      const rows=await designProfile(document,placement,profile.result.stations ?? []);
      if(active)setDesignStations({snapshot,profile:profile.id,rows});
    }).catch(reason=>{if(active)setError(formatApiErrorMessage(reason));});
    return()=>{active=false;};
  },[profile,editor.document,editor.dirty,editor.baseRevision?.id,project.id,snapshot]);
  const generate=async()=>{
    if(!editor.baseRevision)return;
    const current=++generation.current;setBusy(true);setError(null);
    try {const result=await api.post<{id:number;status:string;stations:Station[]}>(`/api/projects/${project.id}/engineering/analyses/profile`,{model_revision_id:editor.baseRevision.id,station_interval_m:interval});
      if(current!==generation.current)return;
      setAnalyses(previous=>[{id:result.id,type:"PROFILE",status:result.status,model_revision_id:editor.baseRevision!.id,terrain_version_id:result.stations[0]?.terrain_version_id ?? null,algorithm_version:"alignment-profile/1",result:{stations:result.stations}},...previous]);
    }catch(reason){if(current===generation.current)setError(formatApiErrorMessage(reason));}finally{setBusy(false);}
  };
  useEffect(()=>{const open=(event:Event)=>{const next=(event as CustomEvent<string>).detail;if(tabs.includes(next))setTab(next);};window.addEventListener("geoai:dock-tab",open);return()=>window.removeEventListener("geoai:dock-tab",open);},[]);
  useEffect(()=>()=>{window.dispatchEvent(new CustomEvent("geoai:analysis-clip",{detail:{mode:"off",value:0,size:50}}));window.dispatchEvent(new CustomEvent("geoai:analysis-location",{detail:null}));},[]);
  const updateClip=(next:AnalysisClip)=>{setClip(next);window.dispatchEvent(new CustomEvent("geoai:analysis-clip",{detail:next}));};
  const checkClearance=async()=>{
    if(!editor.document || !editor.baseRevision)return;
    const current=++generation.current;
    setBusy(true);setError(null);
    const snapshot=JSON.stringify(editor.document), document=editor.document;
    try {
      const {placement}=await api.get<{placement:AnalysisPlacement|null}>(`/api/projects/${project.id}/engineering/placements/${editor.baseRevision.id}`);
      if(!placement)throw new Error("Accept a model placement before support clearance analysis.");
      const rows=await analyseSupports(document,placement,(longitude,latitude)=>api.post<GroundAnalysisSample>(`/api/projects/${project.id}/engineering/ground-samples`,{longitude,latitude}));
      if(current===generation.current){setClearances(rows);setClearanceSnapshot(snapshot);}
    }catch(reason){if(current===generation.current)setError(formatApiErrorMessage(reason));}finally{setBusy(false);}
  };
  const quantities=editor.impact?.quantities;
  const sectionTerrain=async()=>{
    if(!editor.document || !editor.baseRevision)return;
    const current=++generation.current,document=editor.document,key=sectionKey;
    setBusy(true);setError(null);
    try{
      const {placement}=await api.get<{placement:AnalysisPlacement|null}>(`/api/projects/${project.id}/engineering/placements/${editor.baseRevision.id}`);
      if(!placement)throw new Error("Accept a saved placement before sampling a section.");
      const rows=await sampleSection(document,placement,east,north,heading,Math.max(50,Math.ceil(Math.max(Math.abs(minX),Math.abs(maxX))/interval)*interval),interval,(longitude,latitude)=>api.post<GroundAnalysisSample>(`/api/projects/${project.id}/engineering/ground-samples`,{longitude,latitude}));
      if(current===generation.current){setSectionGround(rows);setSectionSnapshot(key);}
    }catch(reason){if(current===generation.current)setError(formatApiErrorMessage(reason));}finally{setBusy(false);}
  };
  return <div className="max-h-[34vh] overflow-y-auto border-t border-white/10 pt-2">
    <div role="tablist" aria-label="Engineering analyses" className="mb-2 flex gap-2">{tabs.map(name=><button role="tab" aria-selected={tab===name} key={name} className={`px-3 py-1.5 text-[10px] ${tab===name?"bg-primary/10 text-primary":"text-muted-foreground"}`} onClick={()=>setTab(name)}>{name}</button>)}</div>
    {error && <p role="alert" className="mb-2 text-xs text-amber-200">{error}</p>}
    <div role="tabpanel" aria-label={tab} className="p-2 text-xs">
      {tab === "QUANTITIES" && <><p className="mb-2 text-[10px] text-muted-foreground">PRELIMINARY · revision {editor.baseRevision?.revision_number ?? "unsaved"}{editor.dirty && " · unsaved geometry"} · no survey-dependent estimate is validated here</p><div className="grid grid-cols-5 gap-3">{[
        ["Concrete",quantities?.concrete_m3,"m³"],["Steel",quantities ? quantities.steel_kg+quantities.rebar_kg : null,"kg"],
        ["Excavation",null,"m³"],["Fill",null,"m³"],["Pavement",quantities?.asphalt_m3,"m³"],["Deck area",null,"m²"],["Foundations",editor.document?.components.filter(item=>item.category.includes("foundation")).length,"objects"],
        ["Cost",editor.impact?.total_cost_estimate,editor.impact?.currency ?? ""],["Duration",null,"months"],
      ].map(([name,value,unit])=><div key={String(name)}><p className="text-muted-foreground">{String(name)}</p><p className="mt-1 font-mono">{show(value,String(unit))}</p><p className="text-[9px] text-muted-foreground">{value==null?"SURVEY / ANALYSIS DATA REQUIRED":"PRELIMINARY"}</p></div>)}</div></>}
      {tab === "PROFILE" && <><div className="mb-2 flex items-center gap-3"><label>Stations <select aria-label="Profile interval" className="border border-border bg-background px-2" value={interval} onChange={event=>setInterval(Number(event.target.value))}>{[10,20,50].map(value=><option key={value} value={value}>{value} m</option>)}</select></label><button className="text-primary disabled:opacity-40" disabled={busy || editor.dirty || !editor.baseRevision || !project.alignment_geojson} onClick={()=>void generate()}>{busy?"Calculating…":"Create terrain profile"}</button><span className="text-muted-foreground">{profile ? `${profile.status} · terrain v${profile.terrain_version_id ?? "unknown"} · revision ${profile.model_revision_id}${editor.dirty || profile.model_revision_id!==editor.baseRevision?.id ? " · STALE FOR CURRENT DRAFT" : ""}`:"A saved model, alignment and authoritative terrain are required."}</span></div>
        {stations.length>0 && <ProfilePlot stations={stations}/>}
        <div className="max-h-36 overflow-y-auto">{stations.map(station=><button key={station.chainage_m} className="block w-full border-b border-white/5 py-1 text-left text-[10px]" onMouseEnter={()=>window.dispatchEvent(new CustomEvent("geoai:analysis-location",{detail:{longitude:station.longitude,latitude:station.latitude,elevation:station.ground_elevation_m}}))} onMouseLeave={()=>window.dispatchEvent(new CustomEvent("geoai:analysis-location",{detail:null}))}>0+{station.chainage_m.toFixed(0).padStart(3,"0")} · ground {show(station.ground_elevation_m,"m")} · design {show(station.proposed_elevation_m,"m")} · grade {show(station.grade_percent,"%")} · {station.source} v{station.terrain_version_id ?? "unknown"} · {station.sample_status}</button>)}</div>
      </>}
      {tab === "SECTION" && <><div className="mb-2 flex flex-wrap items-center gap-3">{[["Section East",east,setEast],["Section North",north,setNorth],["Section heading",heading,setHeading]] .map(([name,value,set])=><label key={String(name)}>{String(name)} <input aria-label={String(name)} type="number" className="w-20 border border-border bg-background px-2" value={value as number} onChange={event=>{if(Number.isFinite(event.target.valueAsNumber))(set as (value:number)=>void)(event.target.valueAsNumber);}}/></label>)}<label>Clipping <select aria-label="Analysis clipping" value={clip.mode} className="border border-border bg-background" onChange={event=>updateClip({...clip,mode:event.target.value as AnalysisClip["mode"]})}>{["off","horizontal","vertical","box","terrain"].map(mode=><option key={mode}>{mode}</option>)}</select></label><label>Plane / box size <input aria-label="Clipping value" type="number" className="w-20 border border-border bg-background" value={clip.mode==="box"?clip.size:clip.value} onChange={event=>{const value=event.target.valueAsNumber;if(Number.isFinite(value)&& (clip.mode!=="box" || value>0))updateClip({...clip,...(clip.mode==="box"?{size:value}:{value})});}}/></label><label><input type="checkbox" checked={underground} onChange={()=>useProjectStore.getState().toggleUndergroundView()}/> Underground view</label></div>
        <p className="mb-1 text-[10px] text-muted-foreground">SECTION A-A · document ENU · exact design geometry. Sampled ground requires resolved survey terrain; differences are preliminary, not earthwork quantities.</p>
        <div className="mb-2 flex gap-3"><label>Section interval <select aria-label="Section interval" value={interval} className="border border-border bg-background" onChange={event=>setInterval(Number(event.target.value))}>{[10,20,50].map(value=><option key={value} value={value}>{value} m</option>)}</select></label><button disabled={busy || editor.dirty || !editor.baseRevision} className="text-primary disabled:opacity-40" onClick={()=>void sectionTerrain()}>Sample section terrain</button>{sectionGround.length>0 && <span>{sectionSnapshot===sectionKey?"SAMPLED":"STALE"}</span>}</div><svg viewBox="0 0 900 120" className="h-28 w-full" role="img" aria-label="Design cross section">{sectionGround.map((row,index)=>row.elevation!==null && sectionGround[index-1]?.elevation!=null ? <line key={`ground-${index}`} x1={450+(sectionGround[index-1].offset-(minX+maxX)/2)*sectionScale} y1={105-(sectionGround[index-1].elevation!-minZ)*sectionScale} x2={450+(row.offset-(minX+maxX)/2)*sectionScale} y2={105-(row.elevation-minZ)*sectionScale} stroke="#94a093" opacity={sectionSnapshot===sectionKey?1:.35}/> : null)}{segments.map((segment,index)=><polyline key={index} points={segment.points.map(([x,z])=>`${450+(x-(minX+maxX)/2)*sectionScale},${105-(z-minZ)*sectionScale}`).join(" ")} fill="none" stroke="#c8ff32" strokeWidth="1" onMouseEnter={()=>{editor.select(segment.id);window.dispatchEvent(new CustomEvent("geoai:analysis-location",{detail:{local:[east,north,segment.points[0][1]]}}));}}><title>{segment.name}</title></polyline>)}</svg>{sectionGround.map(row=><p key={row.offset} className="text-[10px] text-muted-foreground">Offset {row.offset} m · ground ENU {show(row.elevation,"m")} · design {show(row.design,"m")} · {row.difference===null?"Cut/fill unknown":row.difference>=0?`Fill ${show(row.difference,"m")}`:`Cut ${show(-row.difference,"m")}`} · {row.source} v{row.version ?? "unknown"} · {sectionSnapshot===sectionKey?row.status:"STALE"}</p>)}{!segments.length && <p>No design geometry crosses this section line.</p>}
      </>}
      {tab === "CONFLICTS" && <><button className="text-primary" onClick={()=>void editor.validateDraft().catch(reason=>setError(formatApiErrorMessage(reason)))}>Check current design rules</button><p className="mt-2 text-muted-foreground">Terrain, survey coverage and building conflicts require explicit spatial analysis. No automatic geometry changes.</p>{editor.layoutValidation?.violations.map((issue,index)=><button key={index} className="mt-2 block text-left" onClick={()=>editor.select(issue.component_id ?? null)}>{issue.message} · {issue.action}</button>)}</>}
      {tab === "VALIDATION" && <><p>Readiness: {String(evidence?.readiness ?? "Unavailable")}</p><button className="mt-2 text-primary" onClick={()=>window.dispatchEvent(new CustomEvent("geoai:open-site-data"))}>Review site evidence and placement</button><p className="mt-2 text-muted-foreground">No engineering clearance is reported without resolved datum, ground samples and the matching terrain version.</p><button className="mt-2 text-primary disabled:opacity-40" disabled={busy || editor.dirty || !editor.baseRevision} onClick={()=>void checkClearance()}>{busy?"Sampling supports…":"Check bridge support clearances"}</button>{clearances.map(row=><button key={row.id} className="mt-1 block text-left text-[10px]" onClick={()=>editor.select(row.id)}>{row.name} · ground {show(row.ground,"m")} · support base {show(row.foundation,"m")} · deck underside {show(row.deck,"m")} · clearance {show(row.clearance,"m")} · {row.source} v{row.version ?? "unknown"} · {JSON.stringify(editor.document)!==clearanceSnapshot?"STALE":row.status}</button>)}</>}
      {tab === "LOG" && <>{logs.map(entry=><p className="border-b border-white/5 py-1 text-[10px]" key={entry.id}>{entry.timestamp} · {entry.action}</p>)}{!logs.length && <p>No engineering audit events available.</p>}</>}
    </div>
  </div>;
}

function ProfilePlot({stations}:{stations:Station[]}){
  const known=stations.flatMap(station=>[station.ground_elevation_m,station.proposed_elevation_m]).filter((value):value is number=>value!==null && Number.isFinite(value));
  if(!known.length)return <p>Terrain elevations are unknown.</p>;
  const min=Math.min(...known),max=Math.max(...known),length=stations.at(-1)!.chainage_m || 1;
  const path=(key:"ground_elevation_m"|"proposed_elevation_m")=>{let continuous=false;return stations.map(station=>{const value=station[key];if(value===null){continuous=false;return "";}const prefix=continuous?"L":"M";continuous=true;return `${prefix}${station.chainage_m/length*900},${100-(value-min)/Math.max(1,max-min)*90}`;}).join(" ");};
  return <svg viewBox="0 0 900 120" className="h-28 w-full" role="img" aria-label="Alignment terrain profile"><path d={path("ground_elevation_m")} stroke="#94a093" fill="none"/><path d={path("proposed_elevation_m")} stroke="#c8ff32" fill="none"/></svg>;
}



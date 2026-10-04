"use client";

import { Crosshair, ArrowDown } from "lucide-react";
import { terrainHeight, bridgeGrade, roadGrade, roadZ, alignmentZ, SITE } from "./engineeringSite";

const STAGES = [
  {label:"01 / REAL-WORLD CONTEXT",title:["EVERY PROJECT", "STARTS HERE."],body:"A real site. A landscape of possibilities. Follow one valley from spatial context to an infrastructure concept.",note:"ONE SITE / ONE CONNECTED WORKFLOW"},
  {label:"02 / SPATIAL CONTEXT",title:["SELECT", "THE SITE."],body:"Step above the landscape. Establish a boundary, inspect the watercourse and define your project extent.",note:"WGS 84 / SYNTHETIC DEMONSTRATION SITE"},
  {label:"03 / TERRAIN ANALYSIS",title:["READ THE", "TERRAIN."],body:"The surface becomes measurable. Read ridges, low points and slope relationships before choosing a route.",note:"ELEVATION / CONTOURS / WATER CROSSING"},
  {label:"04 / ALIGNMENT EXPLORATION",title:["DEFINE THE", "ALIGNMENT."],body:"Compare candidate routes against the land. Resolve the crossing and choose a continuous design profile.",note:"A—01 / SELECTED CONCEPT ALIGNMENT"},
  {label:"05 / CONCEPT ASSEMBLY",title:["ALIGNMENT", "BECOMES STRUCTURE."],body:"Reference points become foundations. Piers rise, the deck connects the spans, and the road takes shape.",note:"5 × 40 M SPANS / ILLUSTRATIVE DESIGN BASIS"},
];
export function SiteProfile({kind="bridge",detailed=false}:{kind?:"bridge"|"pipeline"|"road";detailed?:boolean}) {
  const samples=Array.from({length:91},(_,i)=>{const x=-17+i*34/90;const z=kind==="road"?roadZ(x):alignmentZ(x);return {x:i*640/90,ground:terrainHeight(x,z),design:kind==="pipeline"?terrainHeight(x,z)+.16:kind==="road"?roadGrade(x):bridgeGrade(x)};});
  const path=(key:"ground"|"design")=>samples.map((p,i)=>`${i?"L":"M"}${p.x.toFixed(1)} ${(114-p[key]*22).toFixed(1)}`).join(" ");
  return <div className={`geo-profile ${detailed?"geo-profile-detailed":""}`}><div className="geo-profile-title"><span>{kind==="pipeline"?"PIPELINE":kind==="road"?"ROAD":"BRIDGE"} / LONGITUDINAL PROFILE</span><span>DATUM +{SITE.datum} M</span></div><svg viewBox="0 0 640 130" role="img" aria-label={`${kind} profile generated from the demonstration geometry`}><path d="M0 25H640M0 65H640M0 105H640" fill="none" stroke="currentColor" strokeOpacity=".15"/><path d={`${path("ground")} L640 130H0Z`} fill="currentColor" fillOpacity=".08"/><path d={path("ground")} fill="none" stroke="currentColor"/><path d={path("design")} fill="none" stroke="#c8ff32" strokeWidth="1.4"/>{kind==="bridge"&&SITE.pierStations.map(x=><path key={x} d={`M${(x+17)*640/34} ${114-bridgeGrade(x)*22}V${114-terrainHeight(x,alignmentZ(x))*22}`} stroke="#bacaa0"/>)}</svg><div className="geo-profile-title"><span>0+000</span><span>0+170</span><span>0+340</span></div></div>;
}
export function WorkflowIndicator({stage}:{stage:number}) { return <ol className="geo-workflow-indicator" aria-label="Transformation stage">{["Earth","Map","Topography","Alignment","Structure","Data"].map((label,i)=><li key={label} aria-current={stage===i?"step":undefined}><span>0{i+1}</span>{label}</li>)}</ol>; }

export default function TransformationStory({stage,progress}:{stage:number;progress:number}) {
  const active=Math.min(4,Math.max(0,stage));const step=STAGES[active];
  return <section id="how-it-works" data-chapter="story" className="geo-transformation"><div className="geo-transformation-sticky" data-story-stage={active}>
    <div className="geo-transform-top"><span>SITE 042 / VALLEY CROSSING</span><span>01—05 / FROM CONTEXT TO CONCEPT</span></div>
    <div key={active} className="geo-transform-copy"><p className="geo-eyebrow">{step.label}</p><h2>{step.title[0]}<br/>{step.title[1]}</h2><p>{step.body}</p><span className="geo-transform-note">{step.note}</span></div>
    {active===0&&<div className="geo-transform-guide"><Crosshair size={25}/><span>17°26′18″N / 78°22′04″E<br/>Illustrative site · not survey data</span></div>}
    {active===1&&<><div className="geo-map-controls"><span>N ↑</span><Crosshair size={18}/><span>+<br/>−</span></div><div className="geo-survey-label geo-transform-boundary"><span>PROJECT BOUNDARY</span><strong>3.52 HA / SITE 042</strong><span>22 × 16 SCENE UNITS</span></div><div className="geo-map-scale">0 ├────────┤ 100 M <small>SCHEMATIC SCALE</small></div></>}
    {active===2&&<><div className="geo-survey-label geo-transform-ridge"><span>RIDGE / SP—03</span><strong>EL. +{(600+terrainHeight(7,5)*10).toFixed(1)} M</strong></div><div className="geo-survey-label geo-transform-valley"><span>LOW POINT / WATERCOURSE</span><strong>EL. +600.8 M</strong><span>SLOPE BREAK / VALLEY FLOOR</span></div><div className="geo-transform-profile"><SiteProfile/></div></>}
    {active===3&&<><div className="geo-candidates"><span className={progress>.35?"is-selected":""}>A—01 <b>{progress>.35?"SELECTED":"CANDIDATE"}</b></span><span style={{opacity:Math.max(.25,1-progress)}}>A—02 <b>LONGER CROSSING</b></span><span style={{opacity:Math.max(.25,1-progress)}}>A—03 <b>HILLSIDE CUT</b></span></div><div className="geo-survey-label geo-transform-ridge"><span>CHAINAGE 0+170 / RIVER CROSSING</span><strong>GRADE 2.0% / R ≈ 2,000 M</strong><span>DESIGNED PROFILE / A—01</span></div><div className="geo-cut-fill"><span>CUT / APPROACH</span><i/><span>FILL / APPROACH</span></div></>}
    {active===4&&<><div className="geo-assembly-status"><span>{progress<.2?"REFERENCE POINTS":progress<.48?"PIER ASSEMBLY":progress<.82?"DECK ASSEMBLY":"STRUCTURAL DETAILS"}</span><i><b style={{width:`${Math.round(progress*100)}%`}}/></i></div>{progress>.78&&<div className="geo-survey-label geo-transform-ridge"><span>SPAN 03 / PIER P2 → P3</span><strong>40 M / 9.6 M CARRIAGEWAY</strong><span>200 M CROSSING / PRELIMINARY</span></div>}</>}
    <WorkflowIndicator stage={active}/><span className="geo-story-scroll">CONTINUE SCROLLING <ArrowDown size={13}/></span>
  </div></section>;
}

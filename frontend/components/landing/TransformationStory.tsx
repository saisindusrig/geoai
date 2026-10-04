"use client";
import { terrainHeight, bridgeGrade, roadGrade, roadZ, alignmentZ, SITE } from "./engineeringSite";

const STAGES = [
  ["Site", "Choose the project location.", "Establish the boundary, inspect the watercourse and define the project extent.", "SITE 042 / SYNTHETIC DEMONSTRATION"],
  ["Data", "Read the terrain.", "Load terrain or validated survey data. Understand elevations and slope relationships before choosing a route.", "ELEVATION / CONTOURS / SOURCE EVIDENCE"],
  ["Generate", "Find a considered alignment.", "Create an infrastructure concept around site conditions. Compare candidate routes and their design implications.", "A—01 / CONCEPT ALIGNMENT"],
  ["Refine", "Give the concept structure.", "Adjust geometry, alignment and engineering parameters. Inspect how deck, supports and approaches meet the land.", "5 × 40 M SPANS / ILLUSTRATIVE GEOMETRY"],
  ["Verify", "Inspect the relationships.", "Review sections, profiles, clearances and conflicts against the source data. Engineering judgement remains explicit.", "PROFILE A—A / PRELIMINARY REVIEW"],
  ["Export", "Carry the evidence forward.", "Export the concept geometry and retain spatial provenance for the next stage of professional review.", "GEOMETRY / SOURCE / REVISION"],
];
export function SiteProfile({kind="bridge",detailed=false}:{kind?:"bridge"|"pipeline"|"road";detailed?:boolean}) {
  const samples=Array.from({length:91},(_,i)=>{const x=-17+i*34/90;const z=kind==="road"?roadZ(x):alignmentZ(x);return {x:i*640/90,ground:terrainHeight(x,z),design:kind==="pipeline"?terrainHeight(x,z)+.16:kind==="road"?roadGrade(x):bridgeGrade(x)};});
  const path=(key:"ground"|"design")=>samples.map((p,i)=>`${i?"L":"M"}${p.x.toFixed(1)} ${(114-p[key]*22).toFixed(1)}`).join(" ");
  return <div className={`geo-profile ${detailed?"geo-profile-detailed":""}`}><div className="geo-profile-title"><span>{kind==="pipeline"?"PIPELINE":kind==="road"?"ROAD":"BRIDGE"} / LONGITUDINAL PROFILE</span><span>DATUM +{SITE.datum} M</span></div><svg viewBox="0 0 640 130" role="img" aria-label={`${kind} profile generated from the demonstration geometry`}><path d="M0 25H640M0 65H640M0 105H640" fill="none" stroke="currentColor" strokeOpacity=".15"/><path d={`${path("ground")} L640 130H0Z`} fill="currentColor" fillOpacity=".08"/><path d={path("ground")} fill="none" stroke="currentColor"/><path d={path("design")} fill="none" stroke="#c8ff32" strokeWidth="1.4"/>{kind==="bridge"&&SITE.pierStations.map(x=><path key={x} d={`M${(x+17)*640/34} ${114-bridgeGrade(x)*22}V${114-terrainHeight(x,alignmentZ(x))*22}`} stroke="#bacaa0"/>)}</svg><div className="geo-profile-title"><span>0+000</span><span>0+170</span><span>0+340</span></div></div>;
}

export default function TransformationStory({stage,onStageChange}:{stage:number;onStageChange:(stage:number)=>void}) {
  const step=STAGES[stage];
  return <section id="how-it-works" data-chapter="story" className="geo-transformation">
    <div className="geo-transformation-sticky">
      <div className="geo-transform-top"><span>01 / ONE CONNECTED WORKFLOW</span><span>SITE 042 / VALLEY CROSSING</span></div>
      <h2 className="geo-workflow-heading">FROM SITE<br/><em>TO CONCEPT.</em></h2>
      <div id="workflow-panel" role="tabpanel" aria-labelledby={"workflow-"+stage} className="geo-workflow-copy" key={stage}>
        <span className="geo-workflow-number">0{stage+1} / {step[0].toUpperCase()}</span><h3>{step[1]}</h3><p>{step[2]}</p><span className="geo-transform-note">{step[3]}</span>
      </div>
      {stage>=4&&<div className="geo-transform-profile"><SiteProfile/><span className="geo-transform-note">ILLUSTRATIVE / NOT FOR CONSTRUCTION</span></div>}
      <div className="geo-workflow-tabs" role="tablist" aria-label="Site to concept workflow">{STAGES.map(([name],i)=><button key={name} id={"workflow-"+i} role="tab" aria-controls="workflow-panel" aria-selected={stage===i} tabIndex={stage===i?0:-1} onClick={()=>onStageChange(i)} onKeyDown={e=>{if(["ArrowRight","ArrowLeft","Home","End"].includes(e.key)){e.preventDefault();const next=e.key==="Home"?0:e.key==="End"?5:(i+(e.key==="ArrowRight"?1:5))%6;onStageChange(next);document.getElementById("workflow-"+next)?.focus();}}}><span>0{i+1}</span>{name}</button>)}</div>
    </div>
  </section>;
}

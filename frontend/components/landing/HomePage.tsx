"use client";

import Link from "next/link";
import dynamic from "next/dynamic";
import { ArrowDown, ArrowUpRight, Check, Pause, Play } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { appEntryPath } from "@/lib/auth-routes";
import type { TerrainState } from "./EngineeringTerrain";
import TechnicalOverview from "./TechnicalOverview";
import TransformationStory, { SiteProfile } from "./TransformationStory";
import "./engineering-home.css";

const Terrain = dynamic(() => import("./EngineeringTerrain"), { ssr:false, loading:()=> <div className="geo-loading">INITIALIZING TERRAIN <span/></div> });
const chapterNames = ["Site", "Workflow", "Infrastructure", "Design basis", "Your next project"];
const systems = [
  { name:"Road", code:"RD", title:"Find the natural line.", description:"A corridor that follows the land. Explore grades, curves and preliminary cut-and-fill relationships.", length:"340 m", slope:"−1.24–2.84%", extra:"Continuous vertical profile" },
  { name:"Bridge", code:"BR", title:"Connect across the valley.", description:"A conceptual deck and pier system spans the crossing. Inspect its relationship to the terrain below.", length:"200 m", slope:"2.0%", extra:"4 pier bents" },
  { name:"Pipeline", code:"PL", title:"Trace the essential networks.", description:"Follow terrain with a continuous utility corridor, inspection nodes and preliminary alignment geometry.", length:"≈350 m", slope:"Variable", extra:"5 inspection nodes" },
  { name:"Dam", code:"DM", title:"Work with the watershed.", description:"Explore a retaining structure and its upstream water boundary within the valley context.", length:"160 m", slope:"—", extra:"Conceptual impoundment" },
];
const faqs = [
  ["What terrain does GeoAI use?", "Terrain depends on the elevation sources configured for your project location. Coverage and resolution vary. This homepage uses a synthetic demonstration site; inspect source metadata in your project before relying on measurements."],
  ["Can I use my own survey data?", "The workspace includes survey import. Supply the coordinate reference system and vertical datum, then review validation results before using the survey as an engineering reference."],
  ["Are GeoAI measurements engineering-grade?", "Accuracy depends on the source data, coordinate system and validation status. Visual map context is not survey-grade evidence. Concept outputs require professional verification before construction."],
  ["Can I edit generated concepts manually?", "Yes. The workspace provides geometry, alignment and parameter editing tools. Available controls depend on the infrastructure type and project workflow."],
  ["Does GeoAI automatically change designs?", "You initiate generation and editing actions. Review proposed changes and the resulting geometry before saving a revision; AI assistance does not replace engineering approval."],
  ["How are revisions tracked?", "Saved model revisions provide a record of geometry and parameter changes. Use revision comparison to review what changed, while checking the terrain and survey source attached to the project."],
  ["What infrastructure types are supported?", "Explore roads, bridges, pipelines, dams and other civil infrastructure concepts. The four systems above demonstrate different structures within the same illustrative terrain."],
  ["Can GeoAI work without premium map data?", "Available map and terrain sources depend on your deployment configuration. Premium imagery is not the same as validated survey data. Review source availability and use survey inputs where engineering accuracy is required."],
];

function Brand() { return <span className="geo-brand"><svg width="27" height="29" viewBox="0 0 27 29" fill="none" aria-hidden="true"><path d="M2 23 13.5 3 25 23H2Z M8 23l5.5-10L19 23 M2 23l11.5 4L25 23" stroke="currentColor" strokeWidth="1.3"/></svg>GeoAI<span className="geo-brand-dot"/></span>; }
function Eyebrow({ n, children }: { n: string; children: React.ReactNode }) { return <p className="geo-eyebrow"><span>{n}</span><i/>{children}</p>; }
function Launch({ small = false, label = "Launch GeoAI" }: { small?: boolean; label?: string }) { return <Link href={appEntryPath("/projects/new")} className={`geo-launch ${small ? "geo-launch-small" : ""}`}>{label} <ArrowUpRight size={small?16:20}/></Link>; }
export default function HomePage() {
  const root = useRef<HTMLDivElement>(null);
  const pointer = useRef({x:0,y:0});
  const [workflow, setWorkflow] = useState(0);
  const [compact, setCompact] = useState(false);
  const [pageHidden, setPageHidden] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const [chapter, setChapter] = useState({ stage:0, progress:0, storytelling:false });
  const [system,setSystem] = useState(3);
  const [structuralView,setStructuralView] = useState(true);

  const [paused,setPaused] = useState(false);
  const [reduced,setReduced] = useState(false);
  useEffect(()=> {
    const media = window.matchMedia("(prefers-reduced-motion: reduce)");
    const sync = () => setReduced(media.matches); sync(); media.addEventListener("change", sync);
    const mobile = window.matchMedia("(max-width: 760px)");
    const syncMobile = () => setCompact(mobile.matches);
    const syncVisibility = () => setPageHidden(document.hidden);
    syncMobile(); syncVisibility();
    mobile.addEventListener("change", syncMobile);
    document.addEventListener("visibilitychange", syncVisibility);
    const container = root.current; if (!container) return;
    let frame = 0;
    let previousStage = -1;
    let sections: HTMLElement[] = [];
    const cacheSections = () => { sections = Array.from(container.querySelectorAll<HTMLElement>("[data-chapter]")).filter(s=>s.offsetHeight>0); };
    const update = () => {
      frame = 0;
      setScrolled(container.scrollTop > 24);
      const y = container.getBoundingClientRect().top;
      const current = sections.filter(s=>s.getBoundingClientRect().top-y < container.clientHeight*.22).at(-1) || sections[0];
      if (!current) return;
      const storytelling=current.dataset.chapter==="story";
      const rect=current.getBoundingClientRect();
      const position=storytelling ? {stage:2,progress:1} : {stage:Number(current.dataset.chapter),progress:Math.max(0,Math.min(1,(container.clientHeight*.5-(rect.top-y))/current.offsetHeight))};
      const {stage}=position, progress=Math.round(position.progress*1000)/1000;
      if (stage === 5 && previousStage !== 5) { setSystem(3); setStructuralView(true); }
      previousStage = stage;
      setChapter(old=>old.stage===stage && old.progress===progress && old.storytelling===storytelling ? old : {stage,progress,storytelling});
    };
    const scroll = () => { if (!frame) frame = requestAnimationFrame(update); };
    const resize = () => { cacheSections(); scroll(); };
    cacheSections();
    container.addEventListener("scroll",scroll,{passive:true}); window.addEventListener("resize",resize); update();
    return ()=> {mobile.removeEventListener("change",syncMobile); document.removeEventListener("visibilitychange",syncVisibility); media.removeEventListener("change",sync); container.removeEventListener("scroll",scroll); window.removeEventListener("resize",resize); cancelAnimationFrame(frame);};
  },[]);
  const technicalScene = !chapter.storytelling && chapter.stage === 9;
  const sceneState: TerrainState = {...chapter,stage:chapter.storytelling?[0,2,3,4,6,12][workflow]:technicalScene?5:chapter.stage,progress:chapter.storytelling?1:chapter.progress,storytelling:false,system:technicalScene?0:system,structuralView:technicalScene||(chapter.stage===5&&structuralView),topDown:false,terrain:true,structure:chapter.storytelling?workflow>=3:true,alignment:chapter.storytelling?workflow>=2:true,hydrology:true,paused:paused||compact||pageHidden||(!chapter.storytelling&&[8,10,11].includes(chapter.stage)),reduced};
  const selected = systems[system];
  const chapterIndex = chapter.storytelling ? 1 : ({ 0: 0, 5: 2, 9: 3, 12: 4 } as Record<number, number>)[chapter.stage] ?? 0;
  return <div ref={root} className="geo-home" data-motion-paused={paused||reduced} data-active-scene={chapter.stage} onPointerMove={e=>{pointer.current={x:e.clientX/window.innerWidth-.5,y:e.clientY/window.innerHeight-.5};}}>
    <header className={`geo-nav ${scrolled ? "geo-nav-solid" : ""}`}><a href="#earth" aria-label="GeoAI home"><Brand/></a><nav aria-label="Homepage"><a href="#how-it-works">Workflow</a><a href="#projects">Infrastructure</a><a href="#design-basis">Design basis</a><a href="#faq">Technical details</a></nav><div className="geo-nav-actions"><Launch small/></div></header>
    <div className="geo-journey">
      <div className="geo-persistent-scene" aria-hidden="true"><Terrain state={sceneState} pointer={pointer}/><div className={`geo-scene-shade ${chapter.stage===5 || chapter.stage===7 ? "geo-shade-light" : ""}`}/><div className="geo-scene-grain"/></div>

      <section id="earth" data-chapter="0" className="geo-chapter geo-hero">
        <div className="geo-hero-topline"><span><i/> SPATIAL INTELLIGENCE, ENGINEERED.</span><span>CONCEPT PLANNING PLATFORM / V.01</span></div>
        <div className="geo-hero-copy"><p className="geo-product-label">GEOAI / INFRASTRUCTURE CONCEPT SYSTEM</p><h1>Real terrain.<br/>Considered<br/><em>infrastructure.</em></h1><div className="geo-hero-description"><p>Plan infrastructure against real terrain, site constraints and spatial data — then refine it inside a precision 3D engineering workspace.</p></div><div className="geo-hero-actions"><Launch/><a className="geo-text-link" href="#how-it-works">See how it works <ArrowDown size={15}/></a></div></div>
        <div className="geo-survey-label geo-hero-label"><span>PROJECT CORRIDOR / A—01</span><strong>ALIGNMENT A—01 / CONCEPT</strong><span>17°26′18″N &nbsp; 78°22′04″E</span></div>
        <div className="geo-hero-scale"><span>N ↑</span><div/><span>NATURAL TERRAIN / CONCEPT VIEW</span></div>
        <div className="geo-hero-bottom"><a href="#how-it-works"><span className="geo-scroll-icon"><ArrowDown size={14}/></span>SCROLL TO EXPLORE</a><span className="geo-demo-note">ILLUSTRATIVE SITE / PRELIMINARY CONCEPT</span></div>
      </section>

      <TransformationStory stage={workflow} onStageChange={setWorkflow}/>

      <section id="projects" data-chapter="5" className="geo-chapter geo-explorer"><div className="geo-section-top"><Eyebrow n="02">INFRASTRUCTURE EXPLORER</Eyebrow><span>ONE SITE. FOUR WAYS FORWARD.</span></div><h2>ONE TERRAIN.<br/>MULTIPLE SYSTEMS.</h2><div className="geo-structural-view"><span>INSPECT THE MODEL</span><div><button aria-pressed={!structuralView} onClick={()=>setStructuralView(false)}>Site view</button><button aria-pressed={structuralView} onClick={()=>setStructuralView(true)}>Structural view ↗</button></div><p>{["SHOULDERS / BARRIERS / DRAINAGE","GIRDERS / CROSS-BRACING / FOUNDATIONS","JOINTS / SADDLES / VALVE STATIONS","SPILLWAYS / CREST / DOWNSTREAM FACE"][system]}</p></div><div className="geo-system-tabs" role="tablist" aria-label="Infrastructure system">{systems.map((s,i)=><button key={s.name} role="tab" id={`system-${i}`} aria-controls="system-panel" aria-selected={i===system} tabIndex={i===system?0:-1} onClick={()=>setSystem(i)} onKeyDown={e=>{if(["ArrowRight","ArrowLeft","Home","End"].includes(e.key)){e.preventDefault();const next=e.key==="Home"?0:e.key==="End"?3:(i+(e.key==="ArrowRight"?1:3))%4;setSystem(next);document.getElementById(`system-${next}`)?.focus();}}}><small>0{i+1} / {s.code}</small>{s.name}<ArrowUpRight size={21}/></button>)}</div><div className="geo-system-panel" id="system-panel" role="tabpanel" aria-labelledby={`system-${system}`}><h3>{selected.title}</h3><p>{selected.description}</p><dl className="geo-small-data"><div><dt>Alignment</dt><dd>{selected.length}</dd></div><div><dt>Design basis</dt><dd>Illustrative</dd></div><div><dt>Grade</dt><dd>{selected.slope}</dd></div></dl><span className="geo-generated"><Check size={13}/> CONCEPT GENERATED</span><small>{selected.extra} · Illustrative values</small></div><div className="geo-explorer-profile">{system===3?<><span className="geo-tag">UPSTREAM WATER LEVEL / DEMO</span><strong>RL 619.5 m</strong><p>Tapered section · valley-side contact<br/>Hydraulics and stability not verified.</p></>:<SiteProfile kind={system===0?"road":system===2?"pipeline":"bridge"}/>}</div></section>


      <TechnicalOverview faqs={faqs}/>

      <section data-chapter="12" className="geo-chapter geo-final"><Eyebrow n="05">YOUR NEXT PROJECT STARTS HERE</Eyebrow><h2>START WITH<br/><em>THE SITE.</em></h2><p>Create an infrastructure concept against real terrain.</p><Launch/><span className="geo-final-caption">MAPS · TERRAIN · AI · 3D · ENGINEERING QUANTITIES</span>{chapter.stage===12&&<div className="geo-survey-label geo-final-label"><span>CONCEPT A—01 / COMPLETE</span><strong>READY FOR EXPLORATION ↗</strong></div>}</section>
      <footer className="geo-footer geo-opaque"><div><a href="#earth" aria-label="Back to GeoAI home"><Brand/></a><p>Infrastructure concept planning.</p></div><nav aria-label="Footer"><a href="#design-basis">Product</a><a href="#how-it-works">Workflow</a><a href="#faq">Technical clarity</a></nav><div className="geo-footer-bottom"><span>© {new Date().getFullYear()} GeoAI</span><span>Concept outputs require professional verification before construction.</span><a href="#earth">BACK TO TOP ↑</a></div></footer>
    </div>
    <div className="geo-chapter-indicator"><span>{String(chapterIndex+1).padStart(2,"0")}</span><i/><span>{chapterNames[chapterIndex]}</span></div>
    <button className="geo-motion-toggle" onClick={()=>setPaused(!paused)} aria-label={paused?"Resume ambient motion":"Pause ambient motion"}>{paused?<Play size={12}/>:<Pause size={12}/>}<span>{paused?"MOTION PAUSED":"LIVE PERSPECTIVE"}</span></button>
  </div>;
}


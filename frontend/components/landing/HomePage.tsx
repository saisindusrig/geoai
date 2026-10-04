"use client";

import Link from "next/link";
import dynamic from "next/dynamic";
import { ArrowDown, ArrowUpRight, Check, Crosshair, Eye, Layers, Minus, Pause, Play, Plus, Settings2 } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { appEntryPath, loginPath } from "@/lib/auth-routes";
import { useDemoProjectId } from "@/lib/useDemoProjectId";
import type { TerrainState } from "./EngineeringTerrain";
import TransformationStory, { SiteProfile, WorkflowIndicator } from "./TransformationStory";
import { approachEarthwork, storyPosition } from "./engineeringSite";
import "./engineering-home.css";

const Terrain = dynamic(() => import("./EngineeringTerrain"), { ssr:false, loading:()=> <div className="geo-loading">INITIALIZING TERRAIN <span/></div> });
const chapterNames = ["Earth", "Map", "Topography", "Alignment", "Structure", "Systems", "Data", "Workspace", "Intelligence", "Verification", "Transformation", "Questions", "Your next project"];
const systems = [
  { name:"Road", code:"RD", title:"Find the natural line.", description:"A corridor that follows the land. Explore grades, curves and preliminary cut-and-fill relationships.", length:"340 m", slope:"−1.24–2.84%", extra:"Continuous vertical profile" },
  { name:"Bridge", code:"BR", title:"Connect across the valley.", description:"A conceptual deck and pier system spans the crossing. Inspect its relationship to the terrain below.", length:"200 m", slope:"2.0%", extra:"4 pier bents" },
  { name:"Pipeline", code:"PL", title:"Trace the essential networks.", description:"Follow terrain with a continuous utility corridor, inspection nodes and preliminary alignment geometry.", length:"≈350 m", slope:"Variable", extra:"5 inspection nodes" },
  { name:"Dam", code:"DM", title:"Work with the watershed.", description:"Explore a retaining structure and its upstream water boundary within the valley context.", length:"160 m", slope:"—", extra:"Conceptual impoundment" },
];
const faqs = [
  ["Are the designs approved for construction?", "No. GeoAI generates conceptual planning outputs. Qualified engineering professionals must verify the source data, assumptions, quantities and detailed design before construction."],
  ["What can I create with GeoAI?", "Explore conceptual roads, bridges, pipelines and civil infrastructure layouts using site context and project requirements. The homepage models are illustrative demonstrations, not generated designs for a surveyed site."],
  ["What terrain and map data does GeoAI use?", "GeoAI uses the map and elevation sources configured for the application and project location. Coverage and resolution vary. Check the project source metadata and validate terrain against survey data; this homepage uses a synthetic demonstration site."],
  ["Which files can I export?", "Available project outputs include GLB models, GeoJSON, CSV, JSON and PDF reports, depending on the generated project and enabled export options."],
  ["Can I modify a generated alignment?", "Use the project workspace to review the concept and adjust the available project parameters or alignment inputs, then regenerate and compare the result. Editing options depend on the project workflow."],
  ["Does the AI invent quantities?", "Preliminary quantities depend on the generated geometry, parameters and calculation assumptions. Treat them as estimates to review, not surveyed or certified quantities."],
  ["What data is sent to map and AI providers?", "Map providers receive requests for the areas you view. Configured AI providers may receive project requirements and relevant site context to generate a concept. The exact data depends on the enabled integration."],
];

function Brand() { return <span className="geo-brand"><svg width="27" height="29" viewBox="0 0 27 29" fill="none" aria-hidden="true"><path d="M2 23 13.5 3 25 23H2Z M8 23l5.5-10L19 23 M2 23l11.5 4L25 23" stroke="currentColor" strokeWidth="1.3"/></svg>GeoAI<span className="geo-brand-dot"/></span>; }
function Eyebrow({ n, children }: { n: string; children: React.ReactNode }) { return <p className="geo-eyebrow"><span>{n}</span><i/>{children}</p>; }
function Launch({ small = false, label = "Launch GeoAI" }: { small?: boolean; label?: string }) { return <Link href={appEntryPath("/projects/new")} className={`geo-launch ${small ? "geo-launch-small" : ""}`}>{label} <ArrowUpRight size={small?16:20}/></Link>; }
function Profile({ detailed = false }: { detailed?: boolean }) { return <SiteProfile detailed={detailed}/>; }
const earthwork = approachEarthwork();

export default function HomePage() {
  const root = useRef<HTMLDivElement>(null);
  const pointer = useRef({x:0,y:0});
  const demoId = useDemoProjectId();
  const [chapter, setChapter] = useState({ stage:0, progress:0, storytelling:false });
  const [system,setSystem] = useState(1);
  const [structuralView,setStructuralView] = useState(false);
  const [openFaq,setOpenFaq] = useState<number|null>(null);
  const [paused,setPaused] = useState(false);
  const [reduced,setReduced] = useState(false);
  const [topDown,setTopDown] = useState(false);
  const [layers,setLayers] = useState({terrain:true,structure:true,alignment:true,hydrology:true});
  const [settings,setSettings] = useState(false);
  useEffect(()=> {
    const media = window.matchMedia("(prefers-reduced-motion: reduce)");
    const sync = () => setReduced(media.matches); sync(); media.addEventListener("change", sync);
    const container = root.current; if (!container) return;
    let frame = 0;
    let sections: HTMLElement[] = [];
    const cacheSections = () => { sections = Array.from(container.querySelectorAll<HTMLElement>("[data-chapter]")).filter(s=>s.offsetHeight>0); };
    const update = () => {
      frame = 0;
      const y = container.getBoundingClientRect().top;
      const current = sections.filter(s=>s.getBoundingClientRect().top-y < container.clientHeight*.22).at(-1) || sections[0];
      if (!current) return;
      const storytelling=current.dataset.chapter==="story";
      const rect=current.getBoundingClientRect();
      const position=storytelling ? storyPosition(Math.max(0,(y-rect.top)/Math.max(1,current.offsetHeight-container.clientHeight))) : {stage:Number(current.dataset.chapter),progress:Math.max(0,Math.min(1,(container.clientHeight*.5-(rect.top-y))/current.offsetHeight))};
      const {stage}=position, progress=Math.round(position.progress*1000)/1000;
      setChapter(old=>old.stage===stage && old.progress===progress && old.storytelling===storytelling ? old : {stage,progress,storytelling});
    };
    const scroll = () => { if (!frame) frame = requestAnimationFrame(update); };
    const resize = () => { cacheSections(); scroll(); };
    cacheSections();
    container.addEventListener("scroll",scroll,{passive:true}); window.addEventListener("resize",resize); update();
    return ()=> {media.removeEventListener("change",sync); container.removeEventListener("scroll",scroll); window.removeEventListener("resize",resize); cancelAnimationFrame(frame);};
  },[]);
  const sceneState: TerrainState = {...chapter,system,structuralView:chapter.stage===5&&structuralView,topDown:chapter.stage===7&&topDown,terrain:chapter.stage!==7||layers.terrain,structure:chapter.stage!==7||layers.structure,alignment:chapter.stage!==7||layers.alignment,hydrology:chapter.stage!==7||layers.hydrology,paused:paused||(chapter.stage>=8&&chapter.stage<=11),reduced};
  const selected = systems[system];
  return <div ref={root} className="geo-home" data-active-scene={chapter.stage} onPointerMove={e=>{pointer.current={x:e.clientX/window.innerWidth-.5,y:e.clientY/window.innerHeight-.5};}}>
    <header className={`geo-nav ${chapter.stage>0 ? "geo-nav-solid" : ""}`}><a href="#earth" aria-label="GeoAI home"><Brand/></a><nav aria-label="Homepage"><a href="#platform">Platform</a><a href="#projects">Projects</a><a href="#how-it-works">How it works</a><a href="#accuracy">Accuracy</a><a href="#faq">FAQ</a></nav><div className="geo-nav-actions"><Link href={loginPath("/dashboard")}>Sign in</Link><Launch small/></div></header>
    <div className="geo-journey">
      <div className="geo-persistent-scene" aria-hidden="true"><Terrain state={sceneState} pointer={pointer}/><div className={`geo-scene-shade ${chapter.stage===5 || chapter.stage===7 ? "geo-shade-light" : ""}`}/><div className="geo-scene-grain"/></div>

      <section id="earth" data-chapter="0" className="geo-chapter geo-hero">
        <div className="geo-hero-topline"><span><i/> SPATIAL INTELLIGENCE, ENGINEERED.</span><span>CONCEPT PLANNING PLATFORM / V.01</span></div>
        <div className="geo-hero-copy"><p className="geo-product-label">GEOSPATIAL PLANNING FOR CIVIL ENGINEERS</p><h1>Real terrain.<br/>Considered<br/><em>infrastructure.</em></h1><div className="geo-hero-description"><p>Turn real-world locations and terrain into conceptual 3D roads, bridges, pipelines and civil infrastructure layouts.</p></div><div className="geo-hero-actions"><Launch label="Start a project"/><Link className="geo-text-link" href={`/projects/${demoId}/workspace?demo=1`}>View the demo <ArrowUpRight size={15}/></Link></div></div>
        <div className="geo-survey-label geo-hero-label"><span>PROJECT CORRIDOR / A—01</span><strong>From context to concept.</strong><span>17°26′18″N &nbsp; 78°22′04″E</span></div>
        <div className="geo-hero-scale"><span>N ↑</span><div/><span>NATURAL TERRAIN / CONCEPT VIEW</span></div>
        <div className="geo-hero-bottom"><a href="#how-it-works"><span className="geo-scroll-icon"><ArrowDown size={14}/></span>SCROLL TO EXPLORE</a><span className="geo-demo-note">ILLUSTRATIVE SITE / PRELIMINARY CONCEPT</span></div>
      </section>

      <section id="capabilities" className="geo-chapter geo-capabilities">
        <div className="geo-section-top"><Eyebrow n="01">WHAT GEOAI DOES</Eyebrow><span>ONE PLATFORM / SIX CAPABILITIES</span></div>
        <h2>FROM SITE TO<br/>CONCEPT, <em>IN ONE FLOW.</em></h2>
        <div className="geo-capability-grid">
          {[
            ["01","Site mapping","Pin coordinates, search addresses, and draw boundaries or alignments on satellite basemaps."],
            ["02","Terrain analysis","Read elevation, slope, contours and cut/fill context before committing to a layout."],
            ["03","3D infrastructure","Model roads, bridges, pipelines and dams as a navigable concept scene."],
            ["04","Earthworks & quantities","Cut-fill volumes and deterministic BOQ lines for concrete, steel and asphalt."],
            ["05","AI design studio","Natural-language edits to regenerate, iterate and compare concept options."],
            ["06","Export & reporting","GLB, GeoJSON, CSV and PDF report packages ready for engineer review."],
          ].map(([n,t,d])=><article key={n}><span>{n}</span><h3>{t}</h3><p>{d}</p></article>)
        }
        </div>
      </section>

      <TransformationStory stage={chapter.storytelling?chapter.stage:chapter.stage>4?4:0} progress={chapter.storytelling?chapter.progress:1}/>





      <section id="projects" data-chapter="5" className="geo-chapter geo-explorer"><div className="geo-section-top"><Eyebrow n="02">INFRASTRUCTURE EXPLORER</Eyebrow><span>ONE SITE. FOUR WAYS FORWARD.</span></div><h2>ONE TERRAIN.<br/>MULTIPLE SYSTEMS.</h2><div className="geo-structural-view"><span>INSPECT THE MODEL</span><div><button aria-pressed={!structuralView} onClick={()=>setStructuralView(false)}>Site view</button><button aria-pressed={structuralView} onClick={()=>setStructuralView(true)}>Structural view ↗</button></div><p>{["SHOULDERS / BARRIERS / DRAINAGE","GIRDERS / CROSS-BRACING / FOUNDATIONS","JOINTS / SADDLES / VALVE STATIONS","SPILLWAYS / CREST / DOWNSTREAM FACE"][system]}</p></div><div className="geo-system-tabs" role="tablist" aria-label="Infrastructure system">{systems.map((s,i)=><button key={s.name} role="tab" id={`system-${i}`} aria-controls="system-panel" aria-selected={i===system} tabIndex={i===system?0:-1} onClick={()=>setSystem(i)} onKeyDown={e=>{if(e.key==="ArrowRight"||e.key==="ArrowLeft"){e.preventDefault();const next=(i+(e.key==="ArrowRight"?1:3))%4;setSystem(next);document.getElementById(`system-${next}`)?.focus();}}}><small>0{i+1} / {s.code}</small>{s.name}<ArrowUpRight size={21}/></button>)}</div><div className="geo-system-panel" id="system-panel" role="tabpanel" aria-labelledby={`system-${system}`}><h3>{selected.title}</h3><p>{selected.description}</p><dl className="geo-small-data"><div><dt>Alignment</dt><dd>{selected.length}</dd></div><div><dt>Design basis</dt><dd>Illustrative</dd></div><div><dt>Grade</dt><dd>{selected.slope}</dd></div></dl><span className="geo-generated"><Check size={13}/> CONCEPT GENERATED</span><small>{selected.extra} · Illustrative values</small></div><div className="geo-explorer-profile">{system===3?<><span className="geo-tag">UPSTREAM WATER LEVEL / DEMO</span><strong>RL 619.5 m</strong><p>Tapered section · valley-side contact<br/>Hydraulics and stability not verified.</p></>:<SiteProfile kind={system===0?"road":system===2?"pipeline":"bridge"}/>}</div></section>


      <section id="engineering-data" data-chapter="6" className="geo-chapter geo-engineering-data">
        <div className="geo-data-intro"><Eyebrow n="03">STRUCTURE → ENGINEERING DATA</Eyebrow><h2>SEE MORE<br/>THAN THE MODEL.</h2><p>Turn the geometry into questions you can measure. Inspect the profile, span arrangement and preliminary quantities together.</p><span className="geo-tag">COMPUTED DEMO GEOMETRY / PRELIMINARY</span></div>
        <svg className="geo-model-dimensions" viewBox="0 0 1000 500" aria-hidden="true"><path d="M130 280 770 175 M130 269V295 M770 160V190 M415 160 420 340 M405 160H425 M410 340H430" fill="none" stroke="currentColor" strokeWidth="1"/><g fill="currentColor" fontFamily="monospace" fontSize="12"><text x="440" y="198" transform="rotate(-9 440 198)">200 M / CROSSING</text><text x="430" y="282">SECTION A—A</text><text x="740" y="148">ABUTMENT A2</text><text x="100" y="322">ABUTMENT A1</text></g></svg>
        <dl className="geo-quantity-strip">{[["Deck plan area","1,920 m²"],["Grade / rise","2.0% / +4 m"],["Approach cut",earthwork.cut.toLocaleString()+" m³"],["Approach fill",earthwork.fill.toLocaleString()+" m³"]].map(([label,value])=><div key={label}><dt>{label}</dt><dd>{value}</dd></div>)}</dl><WorkflowIndicator stage={5}/>
      </section>

      <section id="platform" data-chapter="7" className="geo-chapter geo-workspace-section"><div className="geo-section-top"><Eyebrow n="03">THE ENGINEERING WORKSPACE</Eyebrow><span>FROM EXPLORATION TO INSPECTION</span></div><h2>SEE THE SITE <em>LIKE AN ENGINEER.</em></h2><div className="geo-workspace"><div className="geo-workspace-bar"><Brand/><span className="geo-project-title">Valley crossing / Concept A—01 <small>DEMONSTRATION</small></span><div className="geo-view-toggle"><button onClick={()=>setTopDown(true)} aria-pressed={topDown}>2D</button><button onClick={()=>setTopDown(false)} aria-pressed={!topDown}>3D</button></div><button aria-label="Preview display settings" aria-expanded={settings} onClick={()=>setSettings(!settings)}><Settings2 size={16}/></button>{settings&&<div className="geo-preview-settings"><strong>Preview display</strong><button onClick={()=>setPaused(!paused)}>{paused?"Resume":"Pause"} camera movement</button><p>This is an interactive product illustration.</p></div>}</div><div className="geo-workspace-body"><aside className="geo-workspace-layers"><h3><Layers size={13}/> PROJECT LAYERS</h3>{([["Terrain","terrain"],["Alignment","alignment"],["Road & bridge","structure"],["Hydrology","hydrology"]] as const).map(([name,key])=><button key={key} aria-pressed={layers[key]} onClick={()=>setLayers(old=>({...old,[key]:!old[key]}))}><span className="geo-layer-swatch"/><span>{name}</span><Eye size={12}/></button>)}<div className="geo-empty-layers"><span>Restrictions <small>NOT LOADED</small></span><span>Utilities <small>NOT LOADED</small></span></div><p>Toggle each loaded layer to inspect the crossing.</p></aside><div className="geo-workspace-view"><span className="geo-tag">{topDown?"PLAN VIEW":"PERSPECTIVE"} / CONCEPT A—01</span><span className="geo-view-axis">Y ↑<br/>└ X →</span></div><aside className="geo-workspace-data"><h3>ENGINEERING DATA</h3>{[["Length","200 m"],["Elevation Δ","+4 m"],["Slope","2.0%"],["Deck area","1,920 m²"],["Approach cut",earthwork.cut.toLocaleString()+" m³"],["Approach fill",earthwork.fill.toLocaleString()+" m³"],["Pier bents","4"],["Material estimate","Preliminary"]].map(([k,v])=><div key={k}><span>{k}</span><strong>{v}</strong></div>)}<span className="geo-tag">PRELIMINARY / DEMO</span></aside></div><div className="geo-workspace-bottom"><span>LONGITUDINAL SECTION<br/><small>Concept alignment · A—A</small></span><Profile/><Link href={appEntryPath("/projects/new")}>Open GeoAI <ArrowUpRight size={15}/></Link></div></div></section>

      <section data-chapter="8" className="geo-chapter geo-ai geo-opaque"><Eyebrow n="04">HUMAN JUDGEMENT. AUGMENTED.</Eyebrow><h2>AI DOESN&apos;T REPLACE<br/>ENGINEERING<br/><em>JUDGEMENT.</em></h2><div className="geo-ai-bottom"><p>It helps explore possible concepts faster.<br/><span>You define the intent. Engineering expertise<br/>remains central to every decision.</span></p><span className="geo-ai-coordinate">INPUT → ANALYSIS → EXPLORATION</span></div><div className="geo-intelligence-network"><svg viewBox="0 0 1200 340" role="img" aria-label="Terrain, location, constraints, alignment, parameters and project intent converge into AI analysis, reviewed conceptual geometry"><g fill="none" stroke="#8b9c75" strokeOpacity=".35">{[40,92,144,196,248,300].map(y=><path key={y} d={`M210 ${y} C390 ${y} 390 170 560 170`}/>)}<path d="M680 170H970"/></g><g className="geo-signal-paths" fill="none" stroke="#c8ff32">{[40,92,144,196,248,300].map(y=><path key={y} d={`M210 ${y} C390 ${y} 390 170 560 170`}/>)}<path d="M680 170H970"/></g><circle cx="620" cy="170" r="59" fill="#10180e" stroke="#c8ff32"/><circle cx="620" cy="170" r="72" fill="none" stroke="#c8ff32" strokeOpacity=".15"/><g fill="#b7c3aa" fontFamily="monospace" fontSize="12">{["TERRAIN DATA","PROJECT LOCATION","SITE CONSTRAINTS","ALIGNMENT OPTIONS","DESIGN PARAMETERS","PROJECT INTENT"].map((name,i)=><g key={name}><text x="0" y={45+i*52}>{name}</text><circle cx="210" cy={40+i*52} r="3" fill="#c8ff32"/></g>)}<text x="620" y="165" textAnchor="middle" fill="#c8ff32">AI ANALYSIS</text><text x="620" y="184" textAnchor="middle" fontSize="8">EXPLORE / ITERATE</text><text x="990" y="166" fill="#e1e8d9">CONCEPTUAL LAYOUT</text><text x="990" y="187" fontSize="9">ENGINEER REVIEW REQUIRED</text></g></svg></div></section>

      <section id="accuracy" data-chapter="9" className="geo-chapter geo-verification geo-opaque"><div className="geo-verification-copy"><Eyebrow n="05">MEASURED EXPECTATIONS</Eyebrow><h2>DESIGNED FOR<br/>CONCEPT-STAGE<br/>DECISIONS.</h2><p>Useful context for the next conversation.<br/>Clear assumptions for the next design iteration.</p><div className="geo-verification-note"><Crosshair size={22}/><p>Concept-stage outputs require verification and detailed design by qualified engineering professionals before construction.</p></div></div><div className="geo-drawing-sheet"><div className="geo-drawing-title"><span>GEOAI / CONCEPT DRAWING</span><span>DWG. 042—C01</span></div><svg viewBox="0 0 600 370" role="img" aria-label="Concept plan showing boundary, alignment and section A-A"><defs><pattern id="geo-drawing-grid" width="30" height="30" patternUnits="userSpaceOnUse"><path d="M30 0H0V30" fill="none" stroke="currentColor" strokeOpacity=".1"/></pattern></defs><rect width="600" height="370" fill="url(#geo-drawing-grid)"/><path d="M75 70 490 45 535 270 100 315Z" fill="none" stroke="currentColor" strokeDasharray="7 5"/>{[0,1,2,3,4,5,6].map(i=><path key={i} d={`M20 ${90+i*28} Q140 ${i*23} 250 ${120+i*22} T580 ${40+i*35}`} fill="none" stroke="currentColor" strokeOpacity=".3"/>)}<path d="M45 270 Q190 260 280 180T555 100" fill="none" stroke="#c8ff32" strokeWidth="2"/><path d="M80 340H530 M80 333V347 M530 333V347 M300 70V305" fill="none" stroke="currentColor" strokeWidth=".8"/><circle cx="300" cy="65" r="12" fill="#0c120e" stroke="currentColor"/><circle cx="300" cy="310" r="12" fill="#0c120e" stroke="currentColor"/><g fill="currentColor" fontFamily="monospace" fontSize="10"><text x="296" y="69">A</text><text x="296" y="314">A</text><text x="265" y="359">340 M</text><text x="430" y="310">PLAN / SCHEMATIC</text><text x="90" y="55">SITE BOUNDARY</text><text x="365" y="170">R ≈ 2,000 M</text></g></svg><Profile detailed/><svg className="geo-cross-section" viewBox="0 0 600 150" role="img" aria-label="Cross section A-A showing two lanes, deck, barriers and girders with a 9.6 metre carriageway dimension"><g stroke="currentColor" fill="none" strokeWidth="1"><path d="M125 40H475 M125 32V48 M475 32V48 M120 65H480V80H120Z M112 52H120V80H112Z M480 52H488V80H480Z M170 80V100H183V80 M293 80V100H307V80 M417 80V100H430V80 M300 55V68" /></g><path d="M125 63H475" stroke="#c8ff32"/><g fill="currentColor" fontFamily="monospace" fontSize="9"><text x="260" y="30">9.6 M CARRIAGEWAY</text><text x="150" y="124">SECTION A—A / SCHEMATIC</text><text x="350" y="124">DECK AREA 1,920 M²</text></g></svg><div className="geo-drawing-footer"><span>ALIGNMENT GEOMETRY · SECTION A—A</span><span>NOT FOR CONSTRUCTION</span></div></div>      <div id="design-basis" className="geo-design-basis geo-verification-basis">
        <div><Eyebrow n="01">ENGINEERING INTENT, MADE VISIBLE</Eyebrow><h2>A design basis.<br/>Not just a model.</h2><p>The demonstration crossing is built from explicit geometric assumptions. Inspect the relationship between alignment, deck, supports and terrain before taking a concept into detailed design.</p><span className="geo-tag">ILLUSTRATIVE ASSUMPTIONS · NOT CODE-CHECKED</span></div>
        <div className="geo-rule-list">
          {[["01","Alignment & grade","A continuous horizontal curve and a constant 2% longitudinal grade. The road profile is designed independently of the terrain surface."],["02","Span arrangement","Five 40 m spans between two abutments, with four intermediate pier bents. The central span crosses the channel."],["03","Carriageway & deck","Two lanes on a 9.6 m carriageway, with edge markings, a centre line, concrete barriers, a deck slab and longitudinal girders."],["04","Ground connection","Pier caps, bearings and footings support the superstructure. Abutments, wing walls and graded approaches connect the deck to the site."]].map(([n,t,d])=><article key={n}><span>{n}</span><div><h3>{t}</h3><p>{d}</p></div></article>)}
          <p className="geo-rule-note">Loading, foundations, hydraulics, sight distance and jurisdiction-specific design checks remain subject to professional verification.</p>
        </div>
      </div></section>


      <section id="faq" data-chapter="11" className="geo-chapter geo-faq geo-opaque"><div><Eyebrow n="06">A FEW IMPORTANT DETAILS</Eyebrow><h2>TECHNICAL<br/>CLARITY.</h2></div><div className="geo-faq-list">{faqs.map(([q,a],i)=><div key={q}><button onClick={()=>setOpenFaq(openFaq===i?null:i)} aria-expanded={openFaq===i} aria-controls={`faq-answer-${i}`}><span><small>0{i+1}</small>{q}</span>{openFaq===i?<Minus size={17}/>:<Plus size={17}/>}</button><div id={`faq-answer-${i}`} hidden={openFaq!==i}><p>{a}</p></div></div>)}</div></section>

      <section data-chapter="12" className="geo-chapter geo-final"><Eyebrow n="07">YOUR NEXT PROJECT STARTS HERE</Eyebrow><h2>PLAN BEFORE<br/>YOU <em>BUILD.</em></h2><p>Turn real-world locations into explorable<br/>3D infrastructure concepts.</p><Launch label="Start planning"/><span className="geo-final-caption">MAPS · TERRAIN · AI · 3D · ENGINEERING QUANTITIES</span>{chapter.stage===12&&<div className="geo-survey-label geo-final-label"><span>CONCEPT A—01 / COMPLETE</span><strong>READY FOR EXPLORATION ↗</strong></div>}</section>
      <footer className="geo-footer geo-opaque"><div><a href="#earth" aria-label="Back to GeoAI home"><Brand/></a><p>Spatial intelligence for infrastructure planning.</p></div><nav aria-label="Footer"><a href="#platform">Product</a><a href="#projects">Projects</a><a href="#how-it-works">Workflow</a><Link href={appEntryPath("/dashboard")}>Dashboard</Link><a href="#faq">FAQ & data use</a></nav><div className="geo-footer-bottom"><span>© {new Date().getFullYear()} GeoAI</span><span>CONCEPTUAL PLANNING / PROFESSIONAL VERIFICATION REQUIRED</span><a href="#earth">BACK TO TOP ↑</a></div></footer>
    </div>
    <div className="geo-chapter-indicator"><span>{String(chapter.stage+1).padStart(2,"0")}</span><i/><span>{chapterNames[chapter.stage]}</span></div>
    <button className="geo-motion-toggle" onClick={()=>setPaused(!paused)} aria-label={paused?"Resume ambient motion":"Pause ambient motion"}>{paused?<Play size={12}/>:<Pause size={12}/>}<span>{paused?"MOTION PAUSED":"LIVE PERSPECTIVE"}</span></button>
  </div>;
}

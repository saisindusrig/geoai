"use client";

import { ArrowUpRight, Minus, Plus } from "lucide-react";
import { useState } from "react";

const basis = [
  ["Terrain", "Placement responds to real site elevation."],
  ["Alignment", "Roads, bridges and pipelines follow site geometry."],
  ["Clearance", "Inspect how proposed structures meet the land."],
  ["Constraints", "Keep boundaries, utilities and limitations in view."],
  ["Provenance", "Carry source evidence into every revision."],
];
const review = [
  ["Alignment", "Terrain evidence"],
  ["Geometry", "Clearance + constraints"],
  ["Layout alternatives", "Survey quality"],
  ["Parameter changes", "Design implications"],
];

export default function TechnicalOverview({ faqs }: { faqs: string[][] }) {
  const [open, setOpen] = useState<number | null>(null);
  return (
    <section id="design-basis" data-chapter="9" className="geo-chapter geo-technical-overview">
      <header className="geo-technical-header">
        <div><p className="geo-eyebrow"><span>04</span><i/> ENGINEERING INTENT, MADE EXPLICIT</p><h2>A DESIGN BASIS.<br/><em>NOT JUST A MODEL.</em></h2></div>
        <div><p>Grounded in the site. Assisted by AI. Reviewed by you.<br/>The geometry and the evidence belong together.</p><a className="geo-text-link" href="#how-it-works">Explore the workflow <ArrowUpRight size={15}/></a></div>
      </header>

      <div className="geo-technical-columns">
        <article className="geo-technical-basis">
          <p className="geo-technical-index">01 / DESIGN BASIS</p><h3>Start with the site.</h3>
          <ol>{basis.map(([title,description],i)=><li key={title}><span>0{i+1}</span><div><h4>{title}</h4><p>{description}</p></div></li>)}</ol>
        </article>
        <article className="geo-technical-review">
          <p className="geo-technical-index">02 / HUMAN JUDGEMENT</p><h3>AI proposes. You decide.</h3>
          <p className="geo-technical-description">Explore concepts faster, with engineering review explicit at every step.</p>
          <div className="geo-review-labels"><span>AI PROPOSES</span><span>ENGINEER REVIEWS</span></div>
          <dl>{review.map(([proposal,evidence])=><div key={proposal}><dt>{proposal}</dt><dd>{evidence}</dd></div>)}</dl>
          <p className="geo-technical-note">Concept outputs require professional verification before construction.</p>
        </article>
        <article id="accuracy" className="geo-technical-provenance">
          <p className="geo-technical-index">03 / DATA PROVENANCE</p><h3>Know your source.</h3>
          <div className="geo-evidence-label"><span className="geo-evidence-dot"/> EXAMPLE RECORD <span>A—01 / R12</span></div>
          <dl>{[["Terrain","Survey Terrain v4"],["CRS","EPSG:32643"],["Vertical datum","EGM96"],["Validation","Survey Ready"],["Model revision","R12"],["Status","Preliminary"]].map(([label,value])=><div key={label}><dt>{label}</dt><dd>{value}</dd></div>)}</dl>
          <p className="geo-technical-note">Illustrative metadata. Survey readiness describes data validation, not construction approval.</p>
        </article>
      </div>

      <div id="faq" className="geo-technical-faq">
        <div className="geo-technical-faq-heading"><div><p className="geo-technical-index">04 / TECHNICAL CLARITY</p><h3>A few important details.</h3></div><span>DATA · ACCURACY · CONTROL</span></div>
        <div className="geo-faq-list">{faqs.map(([question,answer],i)=><div key={question}><button onClick={()=>setOpen(open===i?null:i)} aria-expanded={open===i} aria-controls={`faq-answer-${i}`}><span><small>0{i+1}</small>{question}</span>{open===i?<Minus size={16}/>:<Plus size={16}/>}</button><div id={`faq-answer-${i}`} className="geo-faq-answer" inert={open!==i} aria-hidden={open!==i} data-open={open===i}><div><p>{answer}</p></div></div></div>)}</div>
      </div>
    </section>
  );
}

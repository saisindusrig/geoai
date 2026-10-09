"use client";

import { ArrowUpRight, Plus } from "lucide-react";
import { useState } from "react";

export default function TechnicalOverview({ faqs }: { faqs: string[][] }) {
  const [open, setOpen] = useState<number | null>(null);
  return (
    <section id="design-basis" data-chapter="9" className="geo-chapter geo-technical-overview">
      <header className="geo-technical-header">
        <p className="geo-eyebrow"><span>04</span><i /> TECHNICAL CLARITY</p>
        <h2>CLEAR ANSWERS.<br /><em>BETTER DECISIONS.</em></h2>
        <p className="geo-technical-intro">Understand the terrain, the tools and the limits behind every concept.</p>
        <a href="/dashboard" className="geo-technical-link">Explore your workspace <ArrowUpRight size={16} /></a>
        <div className="geo-clarity-lines" aria-hidden="true"><span /><span /><span /><span /><span /></div>
      </header>
      <div id="faq" className="geo-technical-faq">
        <div className="geo-technical-faq-heading"><span>THE DETAILS, EXPLAINED</span><span>{String(faqs.length).padStart(2, "0")} QUESTIONS</span></div>
        <div className="geo-faq-list">
          {faqs.map(([question, answer], i) => (
            <div key={question} className="geo-technical-question" data-open={open === i}>
              <button id={`faq-question-${i}`} type="button" onClick={() => setOpen(open === i ? null : i)} aria-expanded={open === i} aria-controls={`faq-answer-${i}`}>
                <span><small>{String(i + 1).padStart(2, "0")}</small>{question}</span>
                <span className="geo-faq-toggle" aria-hidden="true"><Plus size={17} /></span>
              </button>
              <div id={`faq-answer-${i}`} role="region" aria-labelledby={`faq-question-${i}`} className="geo-faq-answer" inert={open !== i} aria-hidden={open !== i} data-open={open === i}><div><p>{answer}</p></div></div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

import type { Metadata } from "next";

export const metadata: Metadata = { title: "Privacy", description: "How GeoAI handles project, map, and planning data." };

export default function PrivacyPage() {
  return <main id="main-content" className="app-canvas mx-auto w-full max-w-3xl px-8 py-16"><p className="font-data text-xs uppercase tracking-[0.16em] text-primary">GeoAI / data policy</p><h1 className="mt-3 text-3xl font-semibold tracking-[-0.045em]">Privacy and data use</h1><div className="mt-7 border-t border-border pt-6"><p className="text-sm leading-7 text-muted-foreground">GeoAI processes the project information, site context, and planning inputs needed to provide the features you use. Third-party map and AI services may receive requests required to render maps or generate a concept. Do not treat conceptual outputs as surveyed, certified, or construction-ready information.</p><p className="mt-5 text-sm leading-7 text-muted-foreground">For account or project-data requests, contact your GeoAI administrator or the support contact provided with your deployment.</p></div></main>;
}

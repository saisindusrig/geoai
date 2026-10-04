"use client";

import {
  Bot,
  Building2,
  Layers,
  MapPinned,
  Mountain,
  Shovel,
} from "lucide-react";
import { motion } from "framer-motion";
import FeatureStack from "./FeatureStack";
import { BRAND_COPILOT } from "./landing-theme";

const FEATURES = [
  {
    icon: MapPinned,
    title: "Site mapping",
    description: "Pin coordinates, search addresses, and draw boundaries on satellite basemaps.",
  },
  {
    icon: Mountain,
    title: "Terrain analysis",
    description: "Review elevation, slope, and contour context before committing to a layout.",
  },
  {
    icon: Building2,
    title: "3D infrastructure",
    description: "Model roads, flyovers, and building massing in a navigable concept scene.",
  },
  {
    icon: Shovel,
    title: "Earthworks",
    description: "Outline cut-fill zones with preliminary volumes tied to terrain geometry.",
  },
  {
    icon: Layers,
    title: "Material quantities",
    description: "Generate BOQ lines for concrete, steel, asphalt, and related labor bands.",
  },
  {
    icon: Bot,
    title: "AI reporting",
    description: `${BRAND_COPILOT} drafts risks, sequences, and exportable PDF / Excel reports.`,
  },
];

const HIGHLIGHTS = [
  "One workflow from map pin to quantities",
  "Built for consultants, authorities, and infra teams",
  "Preliminary outputs — engineer review required",
];

export default function FeaturesSection() {
  return (
    <section id="features" className="relative scroll-mt-20 border-t border-border py-16">
      <div className="mx-auto max-w-7xl px-8">
        <div className="grid grid-cols-[minmax(0,0.95fr)_minmax(0,1.05fr)] items-stretch gap-12">
          <motion.div
            initial={{ opacity: 0, x: -16 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true, margin: "-60px" }}
            transition={{ duration: 0.45 }}
            className="flex max-w-xl flex-col justify-center"
          >
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-[var(--info-text)]">
              Platform capabilities
            </p>
            <h2 className="mt-3 text-4xl font-bold tracking-tight text-foreground">
              Everything for concept-stage civil planning
            </h2>
            <p className="mt-4 max-w-lg text-base leading-7 text-muted-foreground">
              Map the site, analyze terrain, generate 3D layouts, and estimate materials in one
              dashboard — without switching tools.
            </p>
            <ul className="mt-6 space-y-3">
              {HIGHLIGHTS.map((item) => (
                <li key={item} className="flex items-start gap-3 text-sm leading-6 text-foreground-secondary">
                  <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-primary" />
                  {item}
                </li>
              ))}
            </ul>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, x: 16 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true, margin: "-60px" }}
            transition={{ duration: 0.45, delay: 0.08 }}
            className="relative flex flex-col justify-center"
          >
            <div className="pointer-events-none absolute -inset-6 rounded-[2rem] bg-[radial-gradient(ellipse_at_center,rgba(178,187,171,0.12),transparent_70%)]" />
            <FeatureStack features={FEATURES} />
          </motion.div>
        </div>
      </div>
    </section>
  );
}

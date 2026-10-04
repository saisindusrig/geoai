"use client";

import { motion } from "framer-motion";
import { ArrowRight, FileOutput, MapPin, Scan, Sparkles } from "lucide-react";
import type { LucideIcon } from "lucide-react";

const STEPS: { icon: LucideIcon; step: string; title: string; body: string }[] = [
  {
    icon: MapPin,
    step: "01",
    title: "Select location on map",
    body: "Search globally, drop a pin, and define boundaries or alignments on satellite imagery.",
  },
  {
    icon: Scan,
    step: "02",
    title: "Analyze terrain and surroundings",
    body: "Run site analysis for elevation, slope, roads, buildings, and planning constraints.",
  },
  {
    icon: Sparkles,
    step: "03",
    title: "Generate 3D layout",
    body: "AI-assisted design produces mesh layers, parameters, and a navigable 3D concept model.",
  },
  {
    icon: FileOutput,
    step: "04",
    title: "Export model, quantities, and report",
    body: "Download GLB, GeoJSON, CSV BOQ, and preliminary PDF reports for engineer review.",
  },
];

export default function Workflow() {
  return (
    <section id="workflow" className="relative scroll-mt-20 border-t border-border bg-background-secondary/50 py-28">
      <div className="mx-auto max-w-7xl px-8">
        <div className="mb-14 max-w-2xl">
          <h2 className="text-3xl font-bold tracking-tight text-foreground">
            From map pin to engineering insight in four steps
          </h2>
        </div>

        <div className="relative grid grid-cols-4 gap-6">
          <div className="absolute top-[2.75rem] left-[12%] right-[12%] h-px bg-gradient-to-r from-transparent via-primary/35 to-transparent" />

          {STEPS.map(({ icon: Icon, step, title, body }, i) => (
            <motion.div
              key={step}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.45, delay: i * 0.1 }}
              className="relative"
            >
              <div className="rounded-2xl border border-border bg-card p-6 backdrop-blur-xl h-full transition-all duration-300 hover:border-accent/30 hover:shadow-[0_16px_48px_-20px_rgba(142,160,163,0.25)]">
                <div className="mb-4 flex items-center justify-between">
                  <span className="text-[11px] font-mono font-semibold text-accent">{step}</span>
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-border bg-background-elevated">
                    <Icon className="h-5 w-5 text-[var(--info-text)]" strokeWidth={1.75} />
                  </div>
                </div>
                <h3 className="text-base font-semibold text-foreground">{title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{body}</p>
                {i < STEPS.length - 1 && (
                  <ArrowRight className="absolute -right-3 top-11 z-10 h-5 w-5 text-accent/40" />
                )}
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}

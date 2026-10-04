"use client";

import { motion } from "framer-motion";
import { CheckCircle2 } from "lucide-react";

const POINTS = [
  "Uses high-resolution satellite and terrain context for site selection",
  "Supports precise road, corridor, and structure overlays on mapped coordinates",
  "Designed for civil engineering pre-planning — not final construction approval",
  "Calculates elevation, slope, area, distance, and preliminary material quantities",
];

export default function AccuracySection() {
  return (
    <section id="accuracy" className="relative scroll-mt-20 py-28">
      <div className="mx-auto max-w-7xl px-8">
        <div className="grid grid-cols-2 items-center gap-12">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
          >
            <h2 className="text-3xl font-bold tracking-tight text-foreground">
              Built for Mapping Accuracy
            </h2>
            <p className="mt-4 text-muted-foreground leading-relaxed">
              sitegeoai is built for teams who need trustworthy spatial context before detailed
              design — combining GIS precision with AI-assisted layout generation and deterministic
              quantity engines.
            </p>

            <ul className="mt-8 space-y-4">
              {POINTS.map((point, i) => (
                <motion.li
                  key={point}
                  initial={{ opacity: 0, x: -12 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: i * 0.08 }}
                  className="flex gap-3 text-sm text-foreground-secondary"
                >
                  <CheckCircle2 className="h-5 w-5 shrink-0 text-primary" strokeWidth={1.75} />
                  {point}
                </motion.li>
              ))}
            </ul>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, x: 20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
            className="relative rounded-2xl border border-border bg-card p-6 backdrop-blur-xl"
          >
            <div className="grid grid-cols-2 gap-3">
              {[
                { label: "Elevation range", value: "842 – 861 m" },
                { label: "Site area", value: "4.2 ha" },
                { label: "Alignment length", value: "648 m" },
                { label: "Avg. slope", value: "4.2%" },
                { label: "Cut volume", value: "8,200 m³" },
                { label: "Fill volume", value: "4,180 m³" },
              ].map(({ label, value }) => (
                <div
                  key={label}
                  className="rounded-xl border border-border bg-background-secondary px-4 py-3"
                >
                  <p className="text-[10px] uppercase tracking-wide text-muted-foreground">{label}</p>
                  <p className="mt-1 text-sm font-semibold font-mono text-[var(--info-text)]">{value}</p>
                </div>
              ))}
            </div>
            <div className="mt-4 h-24 rounded-xl border border-accent/20 bg-gradient-to-r from-primary/10 to-accent/10 flex items-end px-4 pb-3 gap-1">
              {[40, 55, 48, 72, 65, 80, 58, 90, 75, 68].map((h, i) => (
                <div
                  key={i}
                  style={{ height: `${h}%` }}
                  className="flex-1 rounded-t-sm bg-gradient-to-t from-primary/60 to-accent/50"
                />
              ))}
            </div>
            <p className="mt-3 text-center text-[10px] text-muted-foreground font-mono">
              Elevation profile · preliminary GIS analysis
            </p>
          </motion.div>
        </div>
      </div>
    </section>
  );
}

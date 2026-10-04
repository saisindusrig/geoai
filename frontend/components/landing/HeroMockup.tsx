"use client";

import { motion } from "framer-motion";
import { Layers, TrendingUp } from "lucide-react";

const METRICS = [
  { label: "Terrain accuracy", value: "±0.8 m", accent: "text-primary" },
  { label: "Road length", value: "648 m", accent: "text-[var(--info-text)]" },
  { label: "Cut / fill", value: "12.4k m³", accent: "text-muted-foreground" },
  { label: "Concrete volume", value: "3,820 m³", accent: "text-muted-foreground" },
  { label: "Steel estimate", value: "412 MT", accent: "text-muted-foreground" },
  { label: "Cost range", value: "₹42–58 Cr", accent: "text-accent" },
];

export default function HeroMockup() {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.96, y: 24 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      transition={{ duration: 0.7, delay: 0.15 }}
      className="relative w-full"
    >
      <div className="absolute -inset-4 rounded-3xl bg-gradient-to-br from-[rgba(142,160,163,0.15)] via-transparent to-[rgba(75,92,88,0.12)] blur-2xl pointer-events-none" />

      <div className="relative overflow-hidden rounded-2xl border border-[rgba(142,160,163,0.2)] bg-[#0c0e0d]/90 shadow-[0_24px_80px_-20px_rgba(0,0,0,0.8)] backdrop-blur-xl">
        <div className="flex items-center justify-between border-b border-white/[0.06] px-4 py-2.5 bg-[#060706]/80">
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-mono text-muted-foreground">Site · 12.9716°N, 77.5946°E</span>
          </div>
        </div>

        <div className="grid lg:grid-cols-[1fr_220px] min-h-[340px] sm:min-h-[400px]">
          {/* Map / 3D viewport */}
          <div className="relative overflow-hidden border-b lg:border-b-0 lg:border-r border-white/[0.06]">
            <div
              className="absolute inset-0 opacity-60"
              style={{
                backgroundImage: `
                  linear-gradient(rgba(142,160,163,0.06) 1px, transparent 1px),
                  linear-gradient(90deg, rgba(142,160,163,0.06) 1px, transparent 1px)
                `,
                backgroundSize: "28px 28px",
              }}
            />
            {/* Contour lines */}
            <svg className="absolute inset-0 w-full h-full opacity-30" preserveAspectRatio="none">
              {[20, 35, 50, 65, 80].map((y) => (
                <path
                  key={y}
                  d={`M0 ${y * 4} Q120 ${y * 4 - 20} 240 ${y * 4} T480 ${y * 4 + 10} T720 ${y * 4 - 5}`}
                  fill="none"
                  stroke="rgba(142,160,163,0.35)"
                  strokeWidth="1"
                />
              ))}
            </svg>

            {/* Terrain gradient */}
            <div className="absolute inset-0 bg-gradient-to-t from-[#060706] via-transparent to-[rgba(75,92,88,0.08)]" />

            {/* Road alignment */}
            <svg className="absolute inset-0 w-full h-full" viewBox="0 0 400 300" preserveAspectRatio="none">
              <path
                d="M 20 220 Q 120 180 200 160 T 380 120"
                fill="none"
                stroke="#8ea0a3"
                strokeWidth="3"
                strokeLinecap="round"
                className="drop-shadow-[0_0_8px_rgba(142,160,163,0.8)]"
              />
              <path
                d="M 20 220 Q 120 180 200 160 T 380 120"
                fill="none"
                stroke="rgba(142,160,163,0.3)"
                strokeWidth="12"
                strokeLinecap="round"
              />
            </svg>

            {/* Flyover blocks */}
            <div className="absolute top-[28%] left-[42%] h-8 w-24 rounded-sm border border-[rgba(178,187,171,0.5)] bg-[rgba(178,187,171,0.15)] shadow-[0_0_20px_rgba(178,187,171,0.3)] rotate-[-8deg]" />
            <div className="absolute top-[38%] left-[52%] h-6 w-16 rounded-sm border border-[rgba(75,92,88,0.4)] bg-[rgba(75,92,88,0.12)] rotate-[-8deg]" />

            {/* Building mass */}
            <div className="absolute bottom-[22%] right-[18%] flex gap-1 items-end">
              {[32, 48, 40, 56].map((h, i) => (
                <div
                  key={i}
                  style={{ height: h }}
                  className="w-5 rounded-t-sm border border-white/10 bg-[rgba(148,163,184,0.12)]"
                />
              ))}
            </div>

            {/* Layer chips */}
            <div className="absolute bottom-3 left-3 flex flex-wrap gap-1.5">
              {["Terrain", "Roads", "Flyover", "Excavation"].map((l) => (
                <span
                  key={l}
                  className="rounded-md border border-[rgba(142,160,163,0.25)] bg-[#060706]/80 px-2 py-0.5 text-[9px] font-medium text-accent"
                >
                  {l}
                </span>
              ))}
            </div>
          </div>

          {/* Metrics panel */}
          <div className="flex flex-col bg-[#060706]/90 p-3 sm:p-4">
            <div className="mb-3 flex items-center gap-2">
              <TrendingUp className="h-3.5 w-3.5 text-primary" />
              <span className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
                Site metrics
              </span>
            </div>
            <div className="space-y-2.5 flex-1">
              {METRICS.map(({ label, value, accent }) => (
                <div
                  key={label}
                  className="rounded-lg border border-white/[0.06] bg-[#0c0e0d]/80 px-3 py-2"
                >
                  <p className="text-[10px] text-muted-foreground/70">{label}</p>
                  <p className={`text-sm font-semibold font-mono tabular-nums ${accent}`}>{value}</p>
                </div>
              ))}
            </div>
            <div className="mt-3 flex items-center gap-2 rounded-lg border border-primary/25 bg-primary/6 px-3 py-2">
              <Layers className="h-3.5 w-3.5 text-primary shrink-0" />
              <p className="text-[10px] leading-snug text-muted-foreground">
                Elevation Δ <span className="text-primary font-medium">18.4 m</span> · Slope avg{" "}
                <span className="text-foreground font-medium">4.2%</span>
              </p>
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
}

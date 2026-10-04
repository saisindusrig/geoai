"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Layers, Sparkles } from "lucide-react";

const LAYERS = [
  {
    name: "Terrain",
    summary: "Survey mesh, contours, and slope bands",
    metric: "0.8 m accuracy",
    accent: "bg-[var(--success)]",
    shapes: [
      "left-[8%] top-[22%] h-20 w-44 rotate-[-10deg] rounded-[55%] bg-primary/20",
      "left-[22%] top-[42%] h-24 w-56 rotate-[8deg] rounded-[50%] bg-[var(--info-text)]/15",
      "right-[12%] top-[28%] h-28 w-60 rotate-[-4deg] rounded-[48%] bg-warning/20",
    ],
  },
  {
    name: "Roads",
    summary: "Access roads, chainage, and turn geometry",
    metric: "3 alignments",
    accent: "bg-primary",
    shapes: [
      "left-[4%] top-[50%] h-10 w-[72%] rotate-[-8deg] rounded-full bg-foreground/10",
      "left-[34%] top-[30%] h-8 w-[46%] rotate-[28deg] rounded-full bg-primary/25",
      "right-[10%] bottom-[22%] h-7 w-[36%] rotate-[-18deg] rounded-full bg-foreground/10",
    ],
  },
  {
    name: "Flyover",
    summary: "Elevated span, piers, and clearance checks",
    metric: "620 m span",
    accent: "bg-[var(--info-text)]",
    shapes: [
      "left-[12%] top-[42%] h-12 w-[76%] rotate-[-5deg] rounded-full bg-[var(--info-text)]/20",
      "left-[20%] top-[56%] h-20 w-4 rounded-full bg-foreground/10",
      "left-[46%] top-[52%] h-24 w-4 rounded-full bg-foreground/10",
      "right-[22%] top-[48%] h-28 w-4 rounded-full bg-foreground/10",
    ],
  },
  {
    name: "Buildings",
    summary: "Plots, podiums, setbacks, and massing",
    metric: "14 blocks",
    accent: "bg-warning",
    shapes: [
      "left-[18%] top-[30%] h-28 w-20 rounded-lg bg-card shadow-lg",
      "left-[36%] top-[24%] h-36 w-24 rounded-lg bg-background-elevated shadow-lg",
      "right-[28%] top-[34%] h-24 w-20 rounded-lg bg-card shadow-lg",
      "right-[12%] top-[22%] h-32 w-24 rounded-lg bg-background-elevated shadow-lg",
    ],
  },
  {
    name: "Excavation",
    summary: "Cut-fill zones, haul routes, and pit volume",
    metric: "8,200 m³",
    accent: "bg-destructive",
    shapes: [
      "left-[18%] top-[36%] h-40 w-[54%] rotate-[-7deg] rounded-[32px] border-2 border-destructive/40 bg-destructive/10",
      "left-[26%] top-[44%] h-24 w-[36%] rotate-[-7deg] rounded-[28px] bg-background/50",
      "right-[16%] bottom-[24%] h-9 w-[32%] rotate-[12deg] rounded-full bg-warning/20",
    ],
  },
  {
    name: "Utilities",
    summary: "Water, drainage, power, and service corridors",
    metric: "6 networks",
    accent: "bg-[var(--info-text)]",
    shapes: [
      "left-[10%] top-[28%] h-2 w-[72%] rotate-[6deg] rounded-full bg-[var(--info-text)]/40",
      "left-[18%] top-[46%] h-2 w-[58%] rotate-[-13deg] rounded-full bg-primary/40",
      "left-[30%] bottom-[26%] h-2 w-[46%] rotate-[18deg] rounded-full bg-warning/40",
      "right-[18%] top-[24%] h-16 w-16 rounded-full border-2 border-[var(--info-text)]/40",
    ],
  },
] as const;

const BOQ_ROWS = [
  { item: "Concrete M35", qty: 3820, unit: "m³" },
  { item: "Steel Fe500", qty: 412, unit: "MT" },
  { item: "Asphalt AC", qty: 1240, unit: "m³" },
  { item: "Excavation", qty: 8200, unit: "m³" },
];

function useCountUp(target: number, active: boolean, duration = 1200) {
  const [value, setValue] = useState(0);

  useEffect(() => {
    if (!active) return;
    const t0 = performance.now();
    let frame: number;

    const tick = (now: number) => {
      const p = Math.min((now - t0) / duration, 1);
      const eased = 1 - (1 - p) ** 3;
      setValue(Math.round(target * eased));
      if (p < 1) frame = requestAnimationFrame(tick);
    };

    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [target, active, duration]);

  return value;
}

function BoqRow({
  item,
  qty,
  unit,
  index,
  inView,
}: {
  item: string;
  qty: number;
  unit: string;
  index: number;
  inView: boolean;
}) {
  const count = useCountUp(qty, inView, 1000 + index * 150);
  const formatted = count.toLocaleString();

  return (
    <motion.tr
      initial={{ opacity: 0, x: 12 }}
      animate={inView ? { opacity: 1, x: 0 } : {}}
      transition={{ delay: 0.3 + index * 0.1, duration: 0.4 }}
      className="border-b border-border/60 last:border-0"
    >
      <td className="px-3 py-2 text-foreground-secondary">{item}</td>
      <td className="px-3 py-2 text-right font-mono text-foreground tabular-nums">{formatted}</td>
      <td className="px-3 py-2 text-right text-muted-foreground">{unit}</td>
    </motion.tr>
  );
}

function LayerPreview({ activeLayer }: { activeLayer: number }) {
  const layer = LAYERS[activeLayer];

  return (
    <div className="absolute inset-0 overflow-hidden">
      <div className="absolute inset-x-8 top-10 h-px bg-gradient-to-r from-transparent via-primary/25 to-transparent" />
      <div className="absolute inset-y-8 left-1/2 w-px bg-gradient-to-b from-transparent via-primary/20 to-transparent" />

      <AnimatePresence mode="wait">
        <motion.div
          key={layer.name}
          initial={{ opacity: 0, scale: 0.98, y: 12 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 1.02, y: -12 }}
          transition={{ duration: 0.45, ease: "easeOut" }}
          className="absolute inset-0"
        >
          <div className="absolute inset-6 rounded-[2rem] border border-primary/10 bg-gradient-to-br from-background/70 via-background-secondary/55 to-primary/10 shadow-inner" />
          <div className="absolute inset-x-[12%] bottom-[18%] h-24 rounded-[50%] bg-primary/10 blur-2xl" />

          {layer.shapes.map((shape) => (
            <div key={shape} className={`absolute ${shape}`} />
          ))}

          <div className="absolute left-[24%] top-[18%] hidden h-2 w-2 rounded-full bg-primary shadow-[0_0_18px_rgba(178,187,171,0.8)] sm:block" />
          <div className="absolute right-[18%] top-[52%] hidden h-2 w-2 rounded-full bg-[var(--info-text)] shadow-[0_0_18px_rgba(93,122,126,0.7)] sm:block" />
          <div className="absolute bottom-[28%] left-[48%] hidden h-2 w-2 rounded-full bg-warning shadow-[0_0_18px_rgba(201,165,90,0.55)] sm:block" />

          <div className="absolute left-1/2 top-1/2 w-[min(76%,520px)] -translate-x-1/2 -translate-y-1/2 rounded-2xl border border-border bg-background/88 p-4 shadow-xl backdrop-blur-md sm:p-5">
            <div className="flex items-start justify-between gap-4">
              <div>
                <div className="mb-3 flex items-center gap-2">
                  <span className={`h-2.5 w-2.5 rounded-full ${layer.accent}`} />
                  <span className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                    {layer.name} Layer
                  </span>
                </div>
                <p className="max-w-[18rem] text-sm font-semibold text-foreground sm:text-base">{layer.summary}</p>
              </div>
              <div className="rounded-xl border border-primary/15 bg-primary/10 px-3 py-2 text-right">
                <p className="text-[9px] uppercase tracking-wider text-muted-foreground">Status</p>
                <p className="mt-1 text-xs font-semibold text-foreground">{layer.metric}</p>
              </div>
            </div>

            <div className="mt-5 grid grid-cols-3 gap-2">
              {["Scan", "Classify", "Estimate"].map((step, index) => (
                <div key={step} className="rounded-lg border border-border bg-card/80 px-2.5 py-2">
                  <div className="mb-2 h-1 rounded-full bg-muted">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${72 + index * 9}%` }}
                      transition={{ delay: 0.12 + index * 0.08, duration: 0.5 }}
                      className="h-full rounded-full bg-primary"
                    />
                  </div>
                  <p className="text-[10px] font-medium text-muted-foreground">{step}</p>
                </div>
              ))}
            </div>
          </div>
        </motion.div>
      </AnimatePresence>
    </div>
  );
}

export default function DemoPreview() {
  const [activeLayer, setActiveLayer] = useState(0);
  const [inView, setInView] = useState(false);

  useEffect(() => {
    const id = setInterval(() => {
      setActiveLayer((i) => (i + 1) % LAYERS.length);
    }, 2200);
    return () => clearInterval(id);
  }, []);

  return (
    <section className="relative border-t border-border bg-background-secondary/60 py-28">
      <div className="mx-auto max-w-7xl px-8">
        <div className="mx-auto mb-12 max-w-2xl text-center">
          <h2 className="text-3xl font-bold tracking-tight text-foreground">
            One dashboard for map, AI, 3D, and quantities
          </h2>
        </div>

        <motion.div
          initial={{ opacity: 0, y: 24 }}
          whileInView={{ opacity: 1, y: 0 }}
          onViewportEnter={() => setInView(true)}
          viewport={{ once: true, margin: "-80px" }}
          transition={{ duration: 0.55 }}
          className="relative overflow-hidden rounded-2xl border border-primary/20 bg-card shadow-[0_32px_80px_-24px_rgba(0,39,11,0.15)]"
        >
          {/* Window chrome */}
          <div className="relative z-10 flex items-center gap-2 border-b border-border bg-background-elevated/95 px-4 py-2.5 backdrop-blur-md">
            <div className="flex gap-1.5">
              <span className="h-2.5 w-2.5 rounded-full bg-destructive/60" />
              <span className="h-2.5 w-2.5 rounded-full bg-warning/70" />
              <span className="h-2.5 w-2.5 rounded-full bg-primary/70" />
            </div>
            <span className="text-[10px] font-mono text-muted-foreground ml-2">
              sitegeoai · AI Design Studio
            </span>
          </div>

          {/* Lightweight workspace preview */}
          <div className="relative min-h-[480px]">
            <div className="absolute inset-0 bg-gradient-to-br from-background-secondary via-background to-primary/5" />
            <div className="absolute inset-0">
              <LayerPreview activeLayer={activeLayer} />
            </div>
            <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_center,transparent_30%,var(--background)_95%)] opacity-40" />

            {/* Layer panel */}
            <motion.div
              initial={{ opacity: 0, x: -16 }}
              animate={inView ? { opacity: 1, x: 0 } : {}}
              transition={{ delay: 0.2, duration: 0.45 }}
              className="absolute left-4 top-4 z-10 w-40 rounded-xl border border-border bg-background/90 p-2.5 shadow-md backdrop-blur-md"
            >
              <p className="mb-2 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                Layers
              </p>
              <ul className="space-y-0.5">
                {LAYERS.map((layer, i) => (
                  <li
                    key={layer.name}
                    className={`flex items-center gap-2 rounded-md px-2 py-1.5 text-[11px] transition-colors ${
                      activeLayer === i
                        ? "bg-primary/15 text-foreground font-medium"
                        : "text-muted-foreground"
                    }`}
                  >
                    <span
                      className={`h-2 w-2 rounded-sm transition-colors ${
                        activeLayer === i ? "bg-primary shadow-[0_0_6px_rgba(178,187,171,0.6)]" : "bg-muted"
                      }`}
                    />
                    {layer.name}
                  </li>
                ))}
              </ul>
            </motion.div>

            {/* BOQ panel */}
            <motion.div
              initial={{ opacity: 0, x: 16 }}
              animate={inView ? { opacity: 1, x: 0 } : {}}
              transition={{ delay: 0.25, duration: 0.45 }}
              className="absolute right-4 bottom-16 z-10 w-[240px] rounded-xl border border-border bg-background/92 p-2.5 shadow-md backdrop-blur-md"
            >
              <div className="mb-2 flex items-center gap-1.5">
                <Layers className="h-3.5 w-3.5 text-primary" />
                <span className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                  Quantities
                </span>
              </div>
              <div className="overflow-hidden rounded-lg border border-border">
                <table className="w-full text-[11px]">
                  <thead>
                    <tr className="border-b border-border bg-background-secondary/80">
                      <th className="px-3 py-1.5 text-left font-medium text-muted-foreground">Item</th>
                      <th className="px-3 py-1.5 text-right font-medium text-muted-foreground">Qty</th>
                      <th className="px-3 py-1.5 text-right font-medium text-muted-foreground">Unit</th>
                    </tr>
                  </thead>
                  <tbody>
                    {BOQ_ROWS.map((row, i) => (
                      <BoqRow key={row.item} {...row} index={i} inView={inView} />
                    ))}
                  </tbody>
                </table>
              </div>
              <p className="mt-1.5 text-[9px] text-muted-foreground">Preliminary BOQ · engineer review required</p>
            </motion.div>

            {/* AI prompt */}
            <motion.div
              initial={{ opacity: 0, y: 16 }}
              animate={inView ? { opacity: 1, y: 0 } : {}}
              transition={{ delay: 0.4, duration: 0.45 }}
              className="absolute bottom-3 left-4 right-4 z-10"
            >
              <div className="flex items-center gap-2 rounded-2xl border border-primary/25 bg-background/92 px-3 py-2.5 shadow-md backdrop-blur-md">
                <Sparkles className="h-4 w-4 shrink-0 text-[var(--info-text)]" />
                <AnimatePresence mode="wait">
                  <motion.span
                    key={activeLayer}
                    initial={{ opacity: 0, y: 4 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -4 }}
                    transition={{ duration: 0.25 }}
                    className="text-[11px] text-muted-foreground"
                  >
                    Analyzing <span className="text-foreground font-medium">{LAYERS[activeLayer].name}</span> layer
                    — generate road layout and estimate materials
                  </motion.span>
                </AnimatePresence>
                <motion.span
                  animate={{ scale: [1, 1.08, 1] }}
                  transition={{ duration: 1.6, repeat: Infinity }}
                  className="ml-auto flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary text-[var(--palette-text)] text-xs font-bold"
                >
                  ↑
                </motion.span>
              </div>
            </motion.div>

            {/* Coordinates ticker */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={inView ? { opacity: 1 } : {}}
              transition={{ delay: 0.55 }}
              className="absolute bottom-[4.5rem] left-4 z-10 rounded-md border border-border bg-background/80 px-2 py-1 font-mono text-[9px] text-muted-foreground backdrop-blur-sm"
            >
              <motion.span
                animate={{ opacity: [0.6, 1, 0.6] }}
                transition={{ duration: 3, repeat: Infinity }}
              >
                12.9716°N, 77.5946°E · ±0.8 m
              </motion.span>
            </motion.div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}

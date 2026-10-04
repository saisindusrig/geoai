"use client";

import { AnimatePresence, motion } from "framer-motion";
import dynamic from "next/dynamic";
import { useEffect, useState } from "react";

const SoftAurora = dynamic(() => import("@/components/ui/SoftAurora"), { ssr: false });

const FEATURES = [
  "3D Terrain",
  "Satellite Mapping",
  "Road & Layout Planning",
  "Material Estimation",
] as const;

const ROTATE_MS = 3200;

export default function TrustMetrics() {
  const [index, setIndex] = useState(0);
  const feature = FEATURES[index];

  useEffect(() => {
    const timer = window.setInterval(() => {
      setIndex((i) => (i + 1) % FEATURES.length);
    }, ROTATE_MS);
    return () => window.clearInterval(timer);
  }, []);

  return (
    <section className="relative overflow-hidden border-y border-border">
      <div className="absolute inset-0 bg-background-secondary/90">
        <SoftAurora
          speed={0.45}
          scale={1.6}
          brightness={0.42}
          color1="#b2bbab"
          color2="#4b5c58"
          noiseFrequency={2.2}
          noiseAmplitude={0.95}
          bandHeight={0.48}
          bandSpread={0.85}
          octaveDecay={0.12}
          layerOffset={0.35}
          colorSpeed={0.7}
          enableMouseInteraction
          mouseInfluence={0.18}
        />
      </div>

      <div
        className="pointer-events-none absolute inset-0 bg-gradient-to-b from-background/55 via-background-secondary/25 to-background/60"
        aria-hidden
      />

      <div className="relative z-10 mx-auto max-w-5xl px-8 py-14 text-center">
        <p className="text-lg font-medium leading-relaxed tracking-wide text-muted-foreground">
          Turn any site on real-world maps into build-ready infrastructure plans with
        </p>

        <div
          aria-live="polite"
          aria-atomic="true"
          className="relative mx-auto mt-4 overflow-hidden text-5xl font-bold leading-tight tracking-tight"
        >
          <div className="relative h-[1.15em]">
            <AnimatePresence mode="wait" initial={false}>
              <motion.h2
                key={feature}
                initial={{ y: "110%", opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                exit={{ y: "-110%", opacity: 0 }}
                transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
                className="absolute inset-x-0 leading-tight"
              >
                <span className="bg-gradient-to-r from-primary via-foreground to-accent bg-clip-text text-transparent">
                  {feature}
                </span>
              </motion.h2>
            </AnimatePresence>
          </div>
        </div>
      </div>
    </section>
  );
}

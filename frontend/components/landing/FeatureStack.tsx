"use client";

import { useEffect, useRef, useState } from "react";
import { motion, useInView } from "framer-motion";
import type { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

const CYCLE_MS = 2800;

export type StackFeature = {
  icon: LucideIcon;
  title: string;
  description: string;
};

function stackOffset(position: number) {
  return {
    y: position * 15,
    scale: 1 - position * 0.038,
    rotate: position * -1.4,
    opacity: Math.max(0.44, 1 - position * 0.12),
  };
}

/* Inline SVG base64 noise texture (64×64, 1-channel, low-contrast grain) */
const NOISE_SVG = `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='64' height='64'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.75' numOctaves='4' stitchTiles='stitch'/%3E%3CfeColorMatrix type='saturate' values='0'/%3E%3C/filter%3E%3Crect width='64' height='64' filter='url(%23n)' opacity='0.06'/%3E%3C/svg%3E")`;

function StackCard({
  feature,
  position,
  isFront,
}: {
  feature: StackFeature;
  position: number;
  isFront: boolean;
}) {
  const { icon: Icon, title, description } = feature;
  const offset = stackOffset(position);

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 56, scale: 0.92 }}
      animate={{
        opacity: offset.opacity,
        y: offset.y,
        scale: offset.scale,
        rotate: offset.rotate,
        zIndex: 10 - position,
      }}
      transition={{ type: "spring", stiffness: 300, damping: 28 }}
      className={cn(
        "absolute inset-x-0 top-0 origin-top",
        !isFront && "pointer-events-none",
      )}
    >
      {/* Card shell — dark matte base + grain + bevel + 3-D shadow */}
      <div
        className="relative overflow-hidden rounded-2xl"
        style={{
          /* layered shadows: close sharp + mid diffuse + far ambient */
          boxShadow: isFront
            ? "0 2px 0 0 rgba(255,255,255,0.06) inset, 0 -1px 0 0 rgba(0,0,0,0.55) inset, 0 4px 8px -2px rgba(0,0,0,0.55), 0 12px 28px -4px rgba(0,0,0,0.50), 0 28px 56px -8px rgba(0,0,0,0.40), 0 0 0 1px rgba(255,255,255,0.07)"
            : "0 4px 12px -2px rgba(0,0,0,0.45), 0 0 0 1px rgba(255,255,255,0.05)",
          background: "linear-gradient(158deg, #161a18 0%, #0e1210 55%, #0a0e0c 100%)",
        }}
      >
        {/* Noise grain layer */}
        <div
          aria-hidden="true"
          className="pointer-events-none absolute inset-0 rounded-2xl"
          style={{
            backgroundImage: NOISE_SVG,
            backgroundRepeat: "repeat",
            backgroundSize: "64px 64px",
            opacity: 0.5,
            mixBlendMode: "overlay",
          }}
        />

        {/* Top-left specular catch-light */}
        <div
          aria-hidden="true"
          className="pointer-events-none absolute -left-10 -top-10 h-44 w-64 rotate-[-22deg] rounded-full"
          style={{
            background: "radial-gradient(ellipse at 30% 30%, rgba(178,187,171,0.13) 0%, transparent 65%)",
            filter: "blur(2px)",
          }}
        />

        {/* Subtle brand-colour accent stripe along top edge */}
        <div
          aria-hidden="true"
          className="pointer-events-none absolute inset-x-0 top-0 h-px"
          style={{
            background:
              "linear-gradient(90deg, transparent 5%, rgba(178,187,171,0.28) 35%, rgba(142,160,163,0.32) 65%, transparent 95%)",
          }}
        />

        {/* Card content */}
        <div className="relative z-10 flex min-h-[230px] flex-col justify-center p-5 sm:min-h-[246px] sm:p-6">
          {/* Icon badge */}
          <div
            className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl sm:h-12 sm:w-12"
            style={{
              background: "linear-gradient(135deg, rgba(178,187,171,0.18) 0%, rgba(75,92,88,0.22) 100%)",
              border: "1px solid rgba(178,187,171,0.18)",
              boxShadow: "0 2px 6px rgba(0,0,0,0.35), inset 0 1px 0 rgba(255,255,255,0.08)",
            }}
          >
            <Icon className="h-5 w-5 text-[var(--info-text)]" strokeWidth={1.75} />
          </div>

          <h3 className="mt-5 text-xl font-semibold leading-tight tracking-tight text-foreground sm:text-[1.35rem]">
            {title}
          </h3>
          <p className="mt-3 max-w-[28rem] text-base leading-7 text-muted-foreground">
            {description}
          </p>
        </div>
      </div>
    </motion.div>
  );
}

export default function FeatureStack({ features }: { features: StackFeature[] }) {
  const ref = useRef<HTMLDivElement>(null);
  const inView = useInView(ref, { once: true, margin: "-80px" });
  const [activeIndex, setActiveIndex] = useState(0);
  const [started, setStarted] = useState(false);

  useEffect(() => {
    if (!inView) return;
    const timer = globalThis.setTimeout(() => setStarted(true), 500);
    return () => globalThis.clearTimeout(timer);
  }, [inView]);

  useEffect(() => {
    if (!started) return;
    const id = globalThis.setInterval(() => {
      setActiveIndex((i) => (i + 1) % features.length);
    }, CYCLE_MS);
    return () => globalThis.clearInterval(id);
  }, [started, features.length]);

  return (
    <div ref={ref} className="relative mx-auto h-[322px] w-full max-w-xl">
      {features.map((feature, i) => {
        const position = (i - activeIndex + features.length) % features.length;
        return (
          <StackCard
            key={feature.title}
            feature={feature}
            position={position}
            isFront={position === 0}
          />
        );
      })}
    </div>
  );
}

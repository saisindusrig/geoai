"use client";

import { motion } from "framer-motion";
import type { LucideIcon } from "lucide-react";
import { BorderGlow } from "@/components/ui/BorderGlow";
import { cn } from "@/lib/utils";

const BRAND_GRADIENT = ["#b2bbab", "#4b5c58", "#8ea0a3"] as const;

export default function FeatureCard({
  icon: Icon,
  title,
  description,
  index = 0,
  className,
}: {
  icon: LucideIcon;
  title: string;
  description: string;
  index?: number;
  className?: string;
}) {
  return (
    <motion.article
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-40px" }}
      transition={{ duration: 0.45, delay: index * 0.06 }}
      whileHover={{ y: -4 }}
      className={cn("group", className)}
    >
      <BorderGlow
        edgeSensitivity={30}
        glowColor="155 90 65"
        backgroundColor="#0c0e0d"
        borderRadius={16}
        glowRadius={32}
        glowIntensity={1.0}
        coneSpread={25}
        colors={[...BRAND_GRADIENT]}
        className="h-full backdrop-blur-xl"
      >
        <div className="p-6">
          <div
            className={cn(
              "mb-4 flex h-11 w-11 items-center justify-center rounded-xl border border-primary/20",
              "bg-gradient-to-br from-primary/15 to-accent/10",
              "transition-colors group-hover:border-primary/40",
            )}
          >
            <Icon className="h-5 w-5 text-[var(--info-text)]" strokeWidth={1.75} />
          </div>
          <h3 className="text-base font-semibold tracking-tight text-foreground">{title}</h3>
          <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{description}</p>
        </div>
      </BorderGlow>
    </motion.article>
  );
}

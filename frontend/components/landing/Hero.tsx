"use client";

import Link from "next/link";
import { Play } from "lucide-react";
import { motion } from "framer-motion";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import HeroEarthAnimation from "./HeroEarthAnimation";
import { useDemoProjectId } from "@/lib/useDemoProjectId";

export default function Hero() {
  const demoId = useDemoProjectId();

  return (
    <section
      id="home"
      className="relative flex min-h-svh scroll-mt-20 items-center justify-center overflow-hidden"
    >
      <div className="absolute inset-0">
        <HeroEarthAnimation />
      </div>

      <div
        className="pointer-events-none absolute inset-0"
        style={{
          background:
            "radial-gradient(ellipse 85% 65% at 50% 48%, rgba(6,7,6,0.18) 0%, rgba(6,7,6,0.42) 55%, rgba(6,7,6,0.68) 100%)",
        }}
      />
      <div className="pointer-events-none absolute inset-0 bg-gradient-to-b from-background/35 via-transparent to-background/55" />
      <div
        className="pointer-events-none absolute inset-0 opacity-25"
        style={{
          background:
            "radial-gradient(ellipse 50% 40% at 50% -10%, rgba(178,187,171,0.22), transparent 60%)",
        }}
      />

      <div className="relative z-10 mx-auto flex w-full max-w-4xl flex-col items-center px-8 py-32 text-center">
        <motion.h1
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.55 }}
          className="text-6xl font-bold leading-[1.06] tracking-tight text-foreground"
        >
          AI-Powered 3D Infrastructure Planning From Real-World Maps
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.55, delay: 0.1 }}
          className="mt-6 max-w-2xl text-lg leading-relaxed text-muted-foreground"
        >
          Select any location, analyze terrain, map roads, plan structures, estimate materials,
          and generate accurate 3D layouts for construction and civil engineering projects.
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.55, delay: 0.15 }}
          className="mt-10 flex items-center justify-center"
        >
          <Link
            href={`/projects/${demoId}/workspace?demo=1`}
            className={cn(
              buttonVariants({ variant: "marketing", size: "lg" }),
              "min-w-60 justify-center gap-2 px-8 font-semibold",
            )}
          >
            <Play className="h-4 w-4" />
            View demo project
          </Link>
        </motion.div>
      </div>
    </section>
  );
}

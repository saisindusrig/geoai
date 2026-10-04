"use client";

import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { motion } from "framer-motion";
import { appEntryPath } from "@/lib/auth-routes";
import { BorderGlow } from "@/components/ui/BorderGlow";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export default function CTASection() {
  return (
    <section id="pricing" className="relative scroll-mt-20 overflow-hidden py-28">
      <div
        className="pointer-events-none absolute inset-0"
        style={{
          background:
            "radial-gradient(ellipse 60% 50% at 50% 100%, rgba(142,160,163,0.15), transparent 60%)",
        }}
      />
      <div className="relative mx-auto max-w-3xl px-8 text-center">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
        >
          <BorderGlow
            edgeSensitivity={28}
            glowColor="155 90 65"
            backgroundColor="#0c0e0d"
            borderRadius={24}
            glowRadius={40}
            glowIntensity={1.1}
            coneSpread={25}
            animated
            colors={["#b2bbab", "#4b5c58", "#8ea0a3"]}
            className="backdrop-blur-xl"
          >
            <div className="p-14 text-center">
              <h2 className="text-3xl font-bold tracking-tight text-foreground">
                Plan Smarter Before Construction Starts
              </h2>
              <p className="mt-4 text-muted-foreground leading-relaxed max-w-lg mx-auto">
                Turn real-world location data into 3D layouts, material estimates, and engineering-ready
                planning insights.
              </p>
              <Link
                href={appEntryPath("/projects/new")}
                className={cn(buttonVariants({ variant: "marketing", size: "lg" }), "mt-8 gap-2 font-semibold")}
              >
                Launch sitegeoai
                <ArrowRight className="h-4 w-4" />
              </Link>
              <p className="mt-6 text-xs text-muted-foreground">
                Free to start · 14 project types · Export PDF, Excel & GLB
              </p>
            </div>
          </BorderGlow>
        </motion.div>
      </div>
    </section>
  );
}

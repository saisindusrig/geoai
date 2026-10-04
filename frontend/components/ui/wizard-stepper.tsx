"use client";

import { Check } from "lucide-react";
import { cn } from "@/lib/utils";

export default function WizardStepper({
  steps,
  current,
  onStepClick,
}: {
  steps: readonly string[];
  current: number;
  onStepClick?: (index: number) => void;
}) {
  return (
    <div className="flex items-center gap-1 overflow-x-auto pb-0.5 scrollbar-thin">
      {steps.map((label, i) => {
        const done = i < current;
        const active = i === current;
        const future = i > current;
        return (
          <div key={label} className="flex items-center gap-1 shrink-0">
            {i > 0 && (
              <div
                className={cn(
                  "hidden sm:block h-px w-6 mx-0.5 transition-colors",
                  done ? "bg-[#10B981]/50" : "bg-[rgba(148,163,184,0.2)]",
                )}
              />
            )}
            <button
              type="button"
              disabled={future}
              onClick={() => done && onStepClick?.(i)}
              className={cn(
                "flex items-center gap-2 rounded-lg px-2.5 py-1.5 text-xs font-medium transition-all duration-200",
                active &&
                  "bg-[rgba(59,130,246,0.15)] text-primary border border-primary/35 shadow-[var(--shadow-glow-primary)]",
                done && "text-[#10B981] hover:bg-[rgba(16,185,129,0.08)] cursor-pointer",
                future && "text-muted-foreground cursor-default",
              )}
            >
              <span
                className={cn(
                  "flex h-6 w-6 items-center justify-center rounded-full text-[10px] border transition-all",
                  done && "bg-[rgba(16,185,129,0.15)] border-[rgba(16,185,129,0.4)]",
                  active && "border-[var(--primary)] bg-[rgba(59,130,246,0.12)]",
                  future && "border-[rgba(148,163,184,0.2)]",
                )}
              >
                {done ? <Check className="h-3.5 w-3.5" /> : i + 1}
              </span>
              <span className="whitespace-nowrap">{label}</span>
            </button>
          </div>
        );
      })}
    </div>
  );
}

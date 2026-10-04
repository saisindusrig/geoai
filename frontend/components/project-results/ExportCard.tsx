"use client";

import type { LucideIcon } from "lucide-react";
import { Download } from "lucide-react";
import { GlassCard } from "@/components/ui/glass-card";
import { StatusPill } from "@/components/project-results/StatusPill";
import { cn } from "@/lib/utils";

export default function ExportCard({
  title,
  description,
  preview,
  fileType,
  icon: Icon,
  href,
  available = true,
  unavailableReason,
  onPreview,
}: {
  title: string;
  description: string;
  preview?: string;
  fileType: string;
  icon: LucideIcon;
  href?: string;
  available?: boolean;
  unavailableReason?: string;
  onPreview?: () => void;
}) {
  const inner = (
    <GlassCard
      hover={available}
      className={cn(
        "h-full p-4 transition-all duration-200 group",
        !available && "opacity-55 cursor-not-allowed",
        available && "hover:border-primary/30",
      )}
    >
      <div className="flex items-start gap-3">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border border-primary/20 bg-primary/10">
          <Icon className="h-5 w-5 text-primary" strokeWidth={1.75} />
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2 flex-wrap">
            <h3 className="text-sm font-semibold text-foreground">{title}</h3>
            <StatusPill label={fileType} variant="muted" />
            {available ? (
              <StatusPill label="Available" variant="success" />
            ) : (
              <StatusPill label="Unavailable" variant="muted" />
            )}
          </div>
          <p className="mt-1 text-xs leading-relaxed text-muted-foreground">{description}</p>
          {preview && (
            <p className="mt-2 text-[10px] text-muted-foreground rounded-md border border-border bg-background-secondary px-2 py-1 inline-block">
              {preview}
            </p>
          )}
          {!available && unavailableReason && (
            <p className="mt-2 text-[10px] text-muted-foreground">{unavailableReason}</p>
          )}
          {available && (
            <div className="mt-3 flex items-center gap-3">
              <span className="inline-flex items-center gap-1 text-[11px] font-medium text-primary group-hover:underline">
                <Download className="h-3 w-3" />
                Download
              </span>
              {onPreview && (
                <button
                  type="button"
                  onClick={(e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    onPreview();
                  }}
                  className="text-[11px] text-muted-foreground hover:text-foreground"
                >
                  Preview
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    </GlassCard>
  );

  if (!available || !href) return inner;
  return (
    <a href={href} className="block h-full" download>
      {inner}
    </a>
  );
}

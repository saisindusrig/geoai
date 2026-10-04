import type { ReactNode } from "react";
import { GlassCard } from "@/components/ui/glass-card";
import { cn } from "@/lib/utils";

export default function ChartCard({
  title,
  subtitle,
  children,
  className,
  height = "h-56 sm:h-64",
  trailing,
}: {
  title: string;
  subtitle?: string;
  children: ReactNode;
  className?: string;
  height?: string;
  trailing?: ReactNode;
}) {
  return (
    <GlassCard className={cn("flex flex-col overflow-hidden", className)}>
      <div className="flex items-start justify-between gap-2 border-b border-border px-4 py-3">
        <div>
          <h3 className="text-sm font-semibold text-foreground">{title}</h3>
          {subtitle && <p className="mt-0.5 text-[11px] text-muted-foreground">{subtitle}</p>}
        </div>
        {trailing}
      </div>
      <div className={cn("flex-1 min-h-0 p-3 sm:p-4", height)}>{children}</div>
    </GlassCard>
  );
}

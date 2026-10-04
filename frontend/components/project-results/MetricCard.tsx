import type { LucideIcon } from "lucide-react";
import { GlassCard } from "@/components/ui/glass-card";
import { cn } from "@/lib/utils";

export default function MetricCard({
  label,
  value,
  unit,
  icon: Icon,
  highlight,
  className,
}: {
  label: string;
  value: string;
  unit?: string;
  icon?: LucideIcon;
  highlight?: boolean;
  className?: string;
}) {
  return (
    <GlassCard
      className={cn(
        "p-3.5 sm:p-4",
        highlight && "border-t-primary border-t-2",
        className,
      )}
    >
      <div className="flex items-start justify-between gap-2">
        <p className="font-mono text-[9px] uppercase tracking-[0.08em] text-muted-foreground">{label}</p>
        {Icon && <Icon className="h-3.5 w-3.5 shrink-0 text-accent opacity-90" strokeWidth={1.75} />}
      </div>
      <p className={cn("mt-3 font-data text-lg font-medium tracking-tight text-foreground sm:text-2xl", highlight && "text-primary")}>
        {value}
      </p>
      {unit && <p className="mt-0.5 text-[10px] text-muted-foreground">{unit}</p>}
    </GlassCard>
  );
}

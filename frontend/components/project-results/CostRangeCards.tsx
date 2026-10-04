import { GlassCard } from "@/components/ui/glass-card";
import { formatCurrency } from "@/lib/utils";
import { cn } from "@/lib/utils";

export default function CostRangeCards({
  low,
  medium,
  high,
  currency = "INR",
}: {
  low: number;
  medium: number;
  high: number;
  currency?: string;
}) {
  const items = [
    { key: "low", label: "Low", value: low, helper: "Conservative scope & rates" },
    { key: "medium", label: "Medium", value: medium, helper: "Most likely planning estimate", highlight: true },
    { key: "high", label: "High", value: high, helper: "Includes contingency & risk buffer" },
  ] as const;

  return (
    <GlassCard className="p-4 sm:p-5">
      <h3 className="text-sm font-semibold text-foreground mb-4">Cost range</h3>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        {items.map((item) => {
          const { key, label, value, helper } = item;
          const highlight = "highlight" in item && item.highlight;
          return (
            <div
              key={key}
              className={cn(
                "rounded-lg border p-3 text-center transition-colors",
                highlight
                  ? "border-primary/40 bg-primary/10"
                  : "border-border bg-background-secondary/50",
              )}
            >
              <p className="text-[10px] font-medium text-muted-foreground">{label}</p>
              <p className={cn("mt-1 font-data text-sm font-bold sm:text-base", highlight ? "text-primary" : "text-foreground")}>
                {formatCurrency(value, currency)}
              </p>
              <p className="mt-1.5 text-[10px] leading-snug text-muted-foreground">{helper}</p>
            </div>
          );
        })}
      </div>
    </GlassCard>
  );
}

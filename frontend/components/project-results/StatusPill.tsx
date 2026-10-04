import { cn } from "@/lib/utils";

const VARIANTS = {
  warning: "border-warning/35 bg-warning-muted text-warning-text",
  success: "border-success/35 bg-success-muted text-success-text",
  accent: "border-primary/35 bg-primary/10 text-foreground-secondary",
  muted: "border-border bg-muted/50 text-muted-foreground",
  critical: "border-destructive/35 bg-destructive-muted text-destructive-text",
} as const;

export function StatusPill({
  label,
  variant = "muted",
  className,
}: {
  label: string;
  variant?: keyof typeof VARIANTS;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-md border px-2 py-0.5 text-[10px] font-medium",
        VARIANTS[variant],
        className,
      )}
    >
      {label}
    </span>
  );
}

import { cn } from "@/lib/utils";

const variants = {
  default: "bg-muted text-foreground-secondary border-border",
  primary: "badge-info",
  secondary: "bg-muted text-muted-foreground border-border",
  outline: "bg-transparent text-muted-foreground border-border",
  accent: "bg-info-muted text-info-text border-[rgba(142,160,163,0.3)]",
  success: "badge-success",
  warning: "badge-warning",
  destructive: "badge-error",
};

export function Badge({
  className,
  variant = "default",
  children,
}: {
  className?: string;
  variant?: keyof typeof variants;
  children: React.ReactNode;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-sm border px-2 py-0.5 font-mono text-[10px] font-medium uppercase tracking-[0.08em]",
        variants[variant],
        className,
      )}
    >
      {children}
    </span>
  );
}

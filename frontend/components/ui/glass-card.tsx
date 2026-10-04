import { cn } from "@/lib/utils";

export function GlassCard({
  className,
  children,
  hover,
}: {
  className?: string;
  children: React.ReactNode;
  hover?: boolean;
}) {
  return (
    <div
      className={cn(
        "rounded-none border border-border bg-card",
        hover && "transition-colors duration-200 hover:border-primary/45 hover:bg-background-elevated",
        className,
      )}
    >
      {children}
    </div>
  );
}

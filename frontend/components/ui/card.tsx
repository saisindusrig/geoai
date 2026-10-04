import { cn } from "@/lib/utils";

export function Card({
  className,
  children,
  glow = false,
  float = false,
}: {
  className?: string;
  children: React.ReactNode;
  glow?: boolean;
  float?: boolean;
}) {
  return (
    <div
      className={cn(
        "text-card-foreground bg-card/90 transition-colors duration-200 hover:border-primary/45",
        float ? "panel-elevated" : "panel",
        glow && "border-primary/40",
        className,
      )}
    >
      {children}
    </div>
  );
}

export function CardHeader({ className, children }: { className?: string; children: React.ReactNode }) {
  return <div className={cn("flex flex-col gap-1 p-5 pb-2", className)}>{children}</div>;
}

export function CardTitle({ className, children }: { className?: string; children: React.ReactNode }) {
  return (
    <h3 className={cn("font-semibold text-[15px] tracking-[-0.02em] text-foreground", className)}>
      {children}
    </h3>
  );
}

export function CardDescription({ className, children }: { className?: string; children: React.ReactNode }) {
  return <p className={cn("text-[14px] text-muted-foreground leading-relaxed", className)}>{children}</p>;
}

export function CardContent({ className, children }: { className?: string; children: React.ReactNode }) {
  return <div className={cn("p-5 pt-2", className)}>{children}</div>;
}

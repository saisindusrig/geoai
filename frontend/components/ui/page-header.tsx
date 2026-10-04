import { cn } from "@/lib/utils";

export function PageHeader({
  title,
  description,
  actions,
  className,
}: {
  title: string;
  description?: string;
  actions?: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("flex flex-wrap items-start justify-between gap-4 border-b border-border pb-6", className)}>
      <div>
        <p className="font-mono text-[10px] uppercase tracking-[0.16em] text-primary">GeoAI / workspace</p>
        <h1 className="mt-3 text-3xl font-medium tracking-[-0.045em] sm:text-[40px]">{title}</h1>
        {description && <p className="mt-2 text-sm text-muted-foreground">{description}</p>}
      </div>
      {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
    </div>
  );
}

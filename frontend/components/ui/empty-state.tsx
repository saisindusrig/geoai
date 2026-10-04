import type { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

export default function EmptyState({
  icon: Icon,
  title,
  description,
  className,
}: {
  icon?: LucideIcon;
  title: string;
  description?: string;
  className?: string;
}) {
  return (
    <div className={cn("flex flex-col items-center justify-center text-center px-4 py-8", className)}>
      {Icon && (
        <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-xl border border-border bg-background-secondary">
          <Icon className="h-5 w-5 text-muted-foreground" strokeWidth={1.75} />
        </div>
      )}
      <p className="text-sm font-medium text-foreground">{title}</p>
      {description && (
        <p className="mt-1.5 max-w-xs text-xs leading-relaxed text-muted-foreground">{description}</p>
      )}
    </div>
  );
}

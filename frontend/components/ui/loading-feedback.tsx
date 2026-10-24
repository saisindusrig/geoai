import { Loader2 } from "lucide-react";
import { Skeleton } from "./skeleton";

/** Pair with visible action text; the parent owns the accessible status. */
export function InlineSpinner() {
  return <Loader2 aria-hidden="true" className="inline size-4 shrink-0 animate-spin motion-reduce:animate-none" />;
}

export function ContentSkeleton({ label = "Loading content…", layout = "cards" }: { label?: string; layout?: "cards" | "rows" }) {
  return <div role="status" aria-busy="true" className="w-full space-y-4 p-6">
    <span className="sr-only">{label}</span>
    <Skeleton className="h-8 w-48" />
    <Skeleton className="h-4 w-2/3" />
    {layout === "rows"
      ? <div className="space-y-3">{[0, 1, 2, 3, 4, 5].map(key => <Skeleton key={key} className="h-10 w-full" />)}</div>
      : <div className="grid gap-4 sm:grid-cols-3">{[0, 1, 2].map(key => <Skeleton key={key} className="h-40" />)}</div>}
  </div>;
}

/** Indeterminate unless the caller has a measured fraction of completed work. */
export function OperationProgress({ label, value }: { label: string; value?: number }) {
  const measured = value !== undefined && Number.isFinite(value);
  const percent = measured ? Math.min(100, Math.max(0, value)) : undefined;
  return <div className="w-full space-y-1">
    <p role="status" className="text-xs text-muted-foreground">{label}{percent !== undefined ? ` · ${Math.round(percent)}%` : " · In progress"}</p>
    <div role="progressbar" aria-label={label} aria-valuemin={0} aria-valuemax={100} aria-valuenow={percent} className="h-1.5 overflow-hidden bg-muted">
      <div className={measured ? "h-full bg-primary" : "h-full w-1/3 animate-pulse bg-primary motion-reduce:animate-none"} style={measured ? { width: `${percent}%` } : undefined} />
    </div>
  </div>;
}

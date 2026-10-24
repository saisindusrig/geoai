import type { ReactNode } from "react";

export function TableScrollRegion({ label, children }: { label: string; children: ReactNode }) {
  return <div>
    <p className="px-3 py-2 text-xs text-muted-foreground sm:hidden">Scroll horizontally to view all columns.</p>
    <div role="region" aria-label={label} tabIndex={0} className="overflow-x-auto focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-primary">{children}</div>
  </div>;
}

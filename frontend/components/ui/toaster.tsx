"use client";

import { CheckCircle2, Loader2, X, XCircle } from "lucide-react";
import { useToastStore } from "@/lib/toast";
import { cn } from "@/lib/utils";

export default function Toaster() {
  const toasts = useToastStore((s) => s.toasts);
  const dismiss = useToastStore((s) => s.dismiss);

  if (!toasts.length) return null;

  return (
    <div className="fixed bottom-20 md:bottom-6 right-4 z-[100] flex flex-col gap-2 max-w-sm w-full pointer-events-none">
      {toasts.map((t) => (
        <div
          key={t.id}
          className={cn(
            "pointer-events-auto panel-glass border px-4 py-3 shadow-lg animate-in fade-in slide-in-from-bottom-2 duration-200",
            t.variant === "success" && "border-success/30",
            t.variant === "error" && "border-destructive/30",
            t.variant === "loading" && "border-primary/30",
          )}
        >
          <div className="flex items-start gap-2">
            {t.variant === "loading" && (
              <Loader2 className="h-4 w-4 shrink-0 animate-spin text-primary mt-0.5" />
            )}
            {t.variant === "success" && (
              <CheckCircle2 className="h-4 w-4 shrink-0 text-success mt-0.5" />
            )}
            {t.variant === "error" && (
              <XCircle className="h-4 w-4 shrink-0 text-destructive mt-0.5" />
            )}
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium">{t.title}</p>
              {t.description && (
                <p className="text-xs text-muted-foreground mt-0.5">{t.description}</p>
              )}
            </div>
            <button
              title="Dismiss"
              type="button"
              onClick={() => dismiss(t.id)}
              className="text-muted-foreground hover:text-foreground shrink-0"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}

"use client";

import { useState } from "react";
import type { ParsedApiError } from "@/lib/api-errors";
import { apiErrorTitle } from "@/lib/api-errors";

export default function ApiErrorDetails({ error }: { error: ParsedApiError }) {
  const [open, setOpen] = useState(false);
  const title = apiErrorTitle(error.status, error.code);

  return (
    <div className="space-y-1 text-sm">
      <p className="font-medium">{title}</p>
      <p className="text-muted-foreground">{error.message}</p>
      {(error.requestId || error.code) && (
        <div>
          <button
            type="button"
            onClick={() => setOpen((v) => !v)}
            className="text-xs text-primary hover:underline"
          >
            {open ? "Hide details" : "Show details"}
          </button>
          {open && (
            <dl className="mt-1 space-y-1 rounded-md border bg-muted/30 p-2 text-xs">
              {error.code && (
                <div className="flex gap-2">
                  <dt className="text-muted-foreground">Code</dt>
                  <dd className="font-mono">{error.code}</dd>
                </div>
              )}
              {error.requestId && (
                <div className="flex gap-2">
                  <dt className="text-muted-foreground">Request ID</dt>
                  <dd className="font-mono break-all">{error.requestId}</dd>
                </div>
              )}
              <div className="flex gap-2">
                <dt className="text-muted-foreground">Status</dt>
                <dd>{error.status}</dd>
              </div>
            </dl>
          )}
        </div>
      )}
    </div>
  );
}

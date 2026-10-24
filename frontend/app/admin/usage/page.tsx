"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { ContentSkeleton, InlineSpinner } from "@/components/ui/loading-feedback";
import { Badge } from "@/components/ui/badge";
import { TableScrollRegion } from "@/components/ui/table-scroll-region";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import ApiErrorDetails from "@/components/ui/api-error-details";
import { loginPath } from "@/lib/auth-routes";
import { api, ApiError } from "@/lib/api";
import type { ParsedApiError } from "@/lib/api-errors";
import { useAuthUser } from "@/lib/useAuthUser";

interface UsageEntry {
  id: number;
  user_id: number | null;
  project_id: number | null;
  event_type: string;
  units: number | null;
  metadata: Record<string, unknown> | null;
  created_at: string | null;
}

interface UsageResponse {
  total: number;
  limit: number;
  offset: number;
  entries: UsageEntry[];
}

export default function UsageAdminPage() {
  const { isAdmin, loading: authLoading } = useAuthUser();
  const pending = useRef(false);
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<UsageResponse | null>(null);
  const [error, setError] = useState<ParsedApiError | null>(null);

  const load = useCallback((offset = 0) => {
    if (pending.current) return;
    pending.current = true;
    setLoading(true);
    api
      .get<UsageResponse>(`/api/admin/usage?limit=100&offset=${offset}`)
      .then((next) => {
        setData(next);
        setError(null);
      })
      .catch((e) => {
        if (e instanceof ApiError) setError(e.toParsed());
        else setError({ status: 0, message: String(e instanceof Error ? e.message : e) });
      }).finally(() => { pending.current = false; setLoading(false); });
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="max-w-6xl mx-auto w-full px-6 py-8 space-y-5">
        <div>
          <p className="font-mono text-[10px] uppercase tracking-[0.16em] text-primary">StruvoCivil / administration</p>
          <h1 className="mt-3 border-b border-border pb-5 text-[36px] font-medium tracking-[-0.045em]">Usage Admin</h1>
          <p className="mt-2 text-sm text-muted-foreground">
            Metered usage events across projects and users.
            {!isAdmin && !authLoading ? " Read-only view." : ""}
          </p>
        </div>

        {error && <p role="alert" className="text-sm text-destructive">Could not load usage events. Retry to reconnect.</p>}
        {loading && !data && <ContentSkeleton label="Loading usage events…" layout="rows" />}
        {error && (
          <Card className="border-destructive/30 bg-destructive/5 p-4 space-y-3">
            <ApiErrorDetails error={error} />
            {error.status === 401 && (
              <Link href={loginPath("/admin/usage")}>
                <Button size="sm" variant="secondary">
                  Sign in
                </Button>
              </Link>
            )}
            {error.status === 0 && (
              <p className="text-xs text-muted-foreground">
                Check that the API is running and `NEXT_PUBLIC_API_URL` is correct, then retry.
              </p>
            )}
            <Button size="sm" variant="outline" onClick={() => load(data?.offset ?? 0)} disabled={loading}>
              Retry
            </Button>
          </Card>
        )}

        <Card float className="overflow-hidden">
          <CardContent className="p-0">
            <TableScrollRegion label="Usage events table">
            <table className="data-table w-full min-w-[640px]">
              <thead>
                <tr>
                  {["Time", "User", "Project", "Event", "Units"].map((h) => (
                    <th key={h}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data?.entries.map((entry) => (
                  <tr key={entry.id}>
                    <td className="text-xs font-data whitespace-nowrap">
                      {entry.created_at ? new Date(entry.created_at).toLocaleString() : "—"}
                    </td>
                    <td className="text-xs">{entry.user_id ?? "—"}</td>
                    <td className="text-xs">{entry.project_id ?? "—"}</td>
                    <td>
                      <Badge variant="accent" className="text-[10px]">
                        {entry.event_type}
                      </Badge>
                    </td>
                    <td className="text-xs font-data">{entry.units ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </TableScrollRegion>
            {data && !loading && !data.entries.length && !error && (
              <p className="p-6 text-sm text-muted-foreground text-center">No usage events recorded.</p>
            )}
          </CardContent>
        </Card>
        {data && <nav aria-label="Event pages" aria-busy={loading} className="flex flex-wrap items-center gap-3">
          <Button variant="outline" disabled={loading || data.offset === 0} onClick={() => load(Math.max(0, data.offset - data.limit))}>Previous</Button>
          <span role="status" className="text-sm text-muted-foreground">{loading ? <><InlineSpinner /> Loading events…</> : `${data.total ? data.offset + 1 : 0}–${data.offset + data.entries.length} of ${data.total}`}</span>
          <Button variant="outline" disabled={loading || data.offset + data.limit >= data.total} onClick={() => load(data.offset + data.limit)}>Next</Button>
        </nav>}
      </div>
    </div>
  );
}

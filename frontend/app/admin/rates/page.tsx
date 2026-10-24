"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { ContentSkeleton, InlineSpinner } from "@/components/ui/loading-feedback";
import { TableScrollRegion } from "@/components/ui/table-scroll-region";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { api } from "@/lib/api";
import { toastPromise } from "@/lib/toast";
import { useAuthUser } from "@/lib/useAuthUser";
import type { RateItem } from "@/lib/types";

const EMPTY = { region: "default", item_code: "", item_name: "", unit: "m3", rate: 0, currency: "INR" };

export default function RatesPage() {
  const { isAdmin, loading: authLoading } = useAuthUser();
  const deleting = useRef(new Set<number>());
  const [pendingDeletes, setPendingDeletes] = useState<Set<number>>(new Set());
  const loadPending = useRef(false);
  const [loading, setLoading] = useState(true);
  const [rates, setRates] = useState<RateItem[]>([]);
  const [draft, setDraft] = useState({ ...EMPTY });
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    if (loadPending.current) return;
    loadPending.current = true;
    setLoading(true);
    try {
      const list = await api.get<RateItem[]>("/api/admin/rates");
      setRates(list);
      setError("");
    } catch (error) {
      setError(error instanceof Error ? error.message : "Could not load rates.");
    } finally { loadPending.current = false; setLoading(false); }
  }, []);
  useEffect(() => {
    const timer = window.setTimeout(() => void load(), 0);
    return () => window.clearTimeout(timer);
  }, [load]);

  const updateRate = async (r: RateItem, rate: number) => {
    await toastPromise(api.put(`/api/admin/rates/${r.id}`, { ...r, rate }), {
      loading: "Updating rate…",
      success: "Rate updated",
    });
    load();
  };

  const add = async () => {
    if (!draft.item_code || !draft.item_name) return;
    await toastPromise(api.post("/api/admin/rates", draft), {
      loading: "Adding rate…",
      success: "Rate added",
    });
    setDraft({ ...EMPTY });
    load();
  };

  const remove = async (item: RateItem) => {
    if (deleting.current.has(item.id)) return;
    if (!window.confirm(`Delete rate “${item.item_name}”? Future cost estimates will no longer use this rate. This cannot be undone here.`)) return;
    deleting.current.add(item.id);
    setPendingDeletes(new Set(deleting.current));
    try {
      await toastPromise(api.delete(`/api/admin/rates/${item.id}`), {
        loading: "Removing rate…", success: "Rate removed",
      });
      await load();
    } catch {
      setError("The rate could not be deleted. Please retry.");
    } finally {
      deleting.current.delete(item.id);
      setPendingDeletes(new Set(deleting.current));
    }
  };

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="max-w-5xl mx-auto w-full px-6 py-8 space-y-5">
        <div>
          <p className="font-mono text-[10px] uppercase tracking-[0.16em] text-primary">StruvoCivil / administration</p>
          <h1 className="mt-3 border-b border-border pb-5 text-[36px] font-medium tracking-[-0.045em]">Material & Labor Rates</h1>
          <p className="mt-2 text-sm text-muted-foreground">
            Regional rates drive all cost estimates.
            {isAdmin ? " Edit inline — new designs pick up changes immediately." : " Read-only view."}
          </p>
        </div>
        {!authLoading && !isAdmin && (
          <p className="text-xs text-amber-600/90">Admin access is required to edit rates.</p>
        )}
        {loading && <ContentSkeleton label="Loading rates…" layout="rows" />}
        {!loading && !error && rates.length === 0 && <p role="status" className="text-sm text-muted-foreground">No rates recorded yet.</p>}
        {error && <Button variant="outline" disabled={loading} onClick={() => void load()}>Retry rates</Button>}
        {error && <p role="alert" className="text-sm text-destructive">{error}</p>}

        <Card className="overflow-hidden">
          <TableScrollRegion label="Material and labor rates table">
          <table className="data-table w-full min-w-[640px] text-sm">
            <thead className="sticky top-0 bg-background-secondary z-10">
              <tr>
                {["Code", "Item", "Unit", "Rate", "Currency", ""].map((h) => (
                  <th key={h} className="text-left px-3 py-2 font-medium text-xs text-muted-foreground">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rates.map((r) => (
                <tr key={r.id} className="border-t border-border">
                  <td className="px-3 py-2 font-data text-xs">{r.item_code}</td>
                  <td className="px-3 py-2">{r.item_name}</td>
                  <td className="px-3 py-2 text-xs">{r.unit}</td>
                  <td className="px-3 py-2">
                    {isAdmin ? (
                      <input
                        type="number"
                        aria-label={`Update rate for ${r.item_name}`}
                        defaultValue={r.rate}
                        onBlur={(e) => {
                          const v = parseFloat(e.target.value);
                          if (v !== r.rate && !Number.isNaN(v)) updateRate(r, v);
                        }}
                        className="w-28 rounded border border-border bg-background px-2 py-1 text-xs font-data focus:border-primary focus:shadow-[var(--shadow-focus)] focus:outline-none"
                      />
                    ) : (
                      <span className="font-data text-xs">{r.rate}</span>
                    )}
                  </td>
                  <td className="px-3 py-2 text-xs">{r.currency}</td>
                  <td className="px-3 py-2">
                    {isAdmin && (
                      <button
                        type="button"
                        onClick={() => void remove(r)}
                        disabled={pendingDeletes.has(r.id)}
                        aria-busy={pendingDeletes.has(r.id)}
                        aria-label={`Delete rate for ${r.item_name}`}
                        className="text-destructive text-xs hover:underline"
                      >
                        {pendingDeletes.has(r.id) ? <InlineSpinner /> : "Delete"}
                      </button>
                    )}
                  </td>
                </tr>
              ))}
              {isAdmin && (
              <tr className="border-t border-border bg-muted/20">
                <td className="px-3 py-2">
                  <input
                    aria-label="Item code"
                    placeholder="CODE"
                    value={draft.item_code}
                    onChange={(e) => setDraft({ ...draft, item_code: e.target.value })}
                    className="w-28 rounded border border-border bg-background px-2 py-1 text-xs font-data focus:border-primary focus:shadow-[var(--shadow-focus)] focus:outline-none"
                  />
                </td>
                <td className="px-3 py-2">
                  <input
                    aria-label="Item name"
                    placeholder="Item name"
                    value={draft.item_name}
                    onChange={(e) => setDraft({ ...draft, item_name: e.target.value })}
                    className="w-full rounded border border-border bg-background px-2 py-1 text-xs focus:border-primary focus:shadow-[var(--shadow-focus)] focus:outline-none"
                  />
                </td>
                <td className="px-3 py-2">
                  <input
                    aria-label="Unit"
                    placeholder="Unit"
                    value={draft.unit}
                    onChange={(e) => setDraft({ ...draft, unit: e.target.value })}
                    className="w-16 rounded border border-border bg-background px-2 py-1 text-xs focus:border-primary focus:shadow-[var(--shadow-focus)] focus:outline-none"
                  />
                </td>
                <td className="px-3 py-2">
                  <input
                    aria-label="Rate"
                    type="number"
                    value={draft.rate}
                    onChange={(e) => setDraft({ ...draft, rate: parseFloat(e.target.value) || 0 })}
                    className="w-28 rounded border border-border bg-background-secondary px-2 py-1 text-xs"
                  />
                </td>
                <td className="px-3 py-2">
                  <input
                    aria-label="Currency"
                    placeholder="INR"
                    value={draft.currency}
                    onChange={(e) => setDraft({ ...draft, currency: e.target.value })}
                    className="w-16 rounded border border-border bg-background px-2 py-1 text-xs focus:border-primary focus:shadow-[var(--shadow-focus)] focus:outline-none"
                  />
                </td>
                <td className="px-3 py-2">
                  <Button size="sm" onClick={add} className="h-7 text-xs">
                    Add
                  </Button>
                </td>
              </tr>
              )}
            </tbody>
          </table>
          </TableScrollRegion>
        </Card>
      </div>
    </div>
  );
}

"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";

interface Props {
  projectId: number;
  adjustment: {
    offset_e_m: number;
    offset_n_m: number;
    horizontal_rmse_m: number | null;
    vertical_rmse_m: number | null;
  } | null;
  onApplied: () => void;
  compact?: boolean;
}

export default function OffsetCorrectionTool({ projectId, adjustment, onApplied, compact }: Props) {
  const [e, setE] = useState(String(adjustment?.offset_e_m?.toFixed(4) ?? "0"));
  const [n, setN] = useState(String(adjustment?.offset_n_m?.toFixed(4) ?? "0"));
  const [busy, setBusy] = useState(false);

  if (!adjustment) return null;

  const apply = async () => {
    setBusy(true);
    try {
      await api.post(`/api/projects/${projectId}/survey/gcp/apply-offset`, {
        offset_e_m: parseFloat(e),
        offset_n_m: parseFloat(n),
        offset_h_m: 0,
      });
      onApplied();
    } finally {
      setBusy(false);
    }
  };

  if (compact) {
    return (
      <div className="space-y-1.5 rounded border border-border p-2">
        <p className="text-[10px] font-medium">GCP offset</p>
        {adjustment.horizontal_rmse_m != null && (
          <p className="text-[10px] text-muted-foreground">
            RMSE H {adjustment.horizontal_rmse_m.toFixed(3)} m
          </p>
        )}
        <div className="grid grid-cols-2 gap-1.5">
          <Input value={e} onChange={(ev) => setE(ev.target.value)} className="h-7 text-xs" placeholder="ΔE" />
          <Input value={n} onChange={(ev) => setN(ev.target.value)} className="h-7 text-xs" placeholder="ΔN" />
        </div>
        <Button size="sm" className="w-full h-7 text-xs" disabled={busy} onClick={apply}>
          Apply
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-2 rounded border border-border p-2">
      <p className="text-xs font-semibold">GCP offset correction</p>
      {adjustment.horizontal_rmse_m != null && (
        <p className="text-[10px] text-muted-foreground">
          H RMSE: {adjustment.horizontal_rmse_m.toFixed(4)} m
          {adjustment.vertical_rmse_m != null && ` · V RMSE: ${adjustment.vertical_rmse_m.toFixed(4)} m`}
        </p>
      )}
      <div className="grid grid-cols-2 gap-2">
        <div>
          <label className="text-[10px] text-muted-foreground">ΔE (m)</label>
          <Input value={e} onChange={(ev) => setE(ev.target.value)} className="h-7 text-xs" />
        </div>
        <div>
          <label className="text-[10px] text-muted-foreground">ΔN (m)</label>
          <Input value={n} onChange={(ev) => setN(ev.target.value)} className="h-7 text-xs" />
        </div>
      </div>
      <Button size="sm" className="w-full h-7 text-xs" disabled={busy} onClick={apply}>
        Apply offset
      </Button>
    </div>
  );
}

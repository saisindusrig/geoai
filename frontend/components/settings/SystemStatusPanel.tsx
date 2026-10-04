"use client";

import { useCallback, useEffect, useState } from "react";
import { Loader2, RefreshCw } from "lucide-react";
import { api } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import type { SystemStatus } from "@/lib/types";

function Dot({ ok }: { ok: boolean }) {
  return <span className={`inline-block h-2 w-2 shrink-0 rounded-full ${ok ? "bg-primary" : "bg-warning"}`} />;
}

function StatusRow({
  label,
  ok,
  okText,
  badText,
  detail,
}: {
  label: string;
  ok: boolean;
  okText: string;
  badText?: string;
  detail?: string;
}) {
  return (
    <div className="flex items-center justify-between gap-4 py-2.5">
      <div className="min-w-0">
        <div className="text-sm text-foreground">{label}</div>
        {detail && <div className="truncate text-xs text-muted-foreground">{detail}</div>}
      </div>
      <div className="flex shrink-0 items-center gap-2">
        <Dot ok={ok} />
        <span className={`text-xs ${ok ? "text-foreground-secondary" : "text-[var(--warning-text)]"}`}>
          {ok ? okText : (badText ?? okText)}
        </span>
      </div>
    </div>
  );
}

export default function SystemStatusPanel() {
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [updatedAt, setUpdatedAt] = useState<Date | null>(null);

  const load = useCallback(async (silent = false) => {
    if (silent) setRefreshing(true);
    else setLoading(true);
    try {
      const s = await api.get<SystemStatus>("/api/system/status");
      setStatus(s);
      setUpdatedAt(new Date());
    } catch {
      if (!silent) setStatus(null);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void load();
    }, 0);
    return () => window.clearTimeout(timer);
  }, [load]);

  if (loading) {
    return (
      <Card>
        <CardContent className="flex items-center gap-2 py-6 text-sm text-muted-foreground">
          <Loader2 className="h-4 w-4 animate-spin" />
          Loading system status…
        </CardContent>
      </Card>
    );
  }

  if (!status) {
    return (
      <Card>
        <CardContent className="py-6 text-sm text-muted-foreground">
          Could not reach backend system status. Is the API running on port 8000?
        </CardContent>
      </Card>
    );
  }

  const core = [
    status.postgis_available,
    status.redis_available,
    true, // storage
    status.survey_mode_available,
    !status.ai.mock_mode,
  ];
  const activeCount = core.filter(Boolean).length;

  const mapsList = [
    status.maps.google_maps_configured && "Google",
    status.maps.cesium_ion_configured && "Cesium Ion",
    status.maps.mapbox_configured && "Mapbox",
    status.maps.osm_fallback && "OSM fallback",
  ].filter(Boolean);
  const mapsOk = mapsList.length > 0;

  return (
    <Card float>
      <CardContent className="p-5">
        <div className="flex items-center justify-between gap-3 border-b border-border pb-3">
          <div className="flex items-center gap-2.5">
            <span className="relative flex h-2.5 w-2.5">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-primary opacity-60" />
              <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-primary" />
            </span>
            <span className="text-sm font-semibold text-foreground">
              {activeCount}/{core.length} core services active
            </span>
          </div>
          <button
            type="button"
            onClick={() => void load(true)}
            disabled={refreshing}
            className="inline-flex items-center gap-1.5 rounded-md border border-border px-2.5 py-1.5 text-xs text-muted-foreground transition hover:text-foreground disabled:opacity-50"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${refreshing ? "animate-spin" : ""}`} />
            Refresh
          </button>
        </div>

        <div className="divide-y divide-border">
          <StatusRow label="Database" ok={status.postgis_available} okText="PostGIS" badText="SQLite fallback" detail={status.database_mode_label} />
          <StatusRow label="Jobs & queue" ok={status.redis_available} okText="Redis" badText={status.job_store} detail={`Queue: ${status.job_store}`} />
          <StatusRow label="Storage" ok okText={status.storage_mode} detail="File & export storage" />
          <StatusRow label="Survey mode" ok={status.survey_mode_available} okText="Survey-grade" badText="Limited GIS" detail={status.survey_mode_available ? "Survey-grade geometry available" : "SQLite limited GIS mode"} />
          <StatusRow
            label="AI provider"
            ok={!status.ai.mock_mode}
            okText={status.ai.active_provider}
            badText="Mock / demo"
            detail={status.ai.mock_mode ? "No provider configured — deterministic mock" : status.ai.configured_provider ? `Configured: ${status.ai.configured_provider}` : undefined}
          />
          <StatusRow
            label="Map & 3D"
            ok={mapsOk}
            okText={mapsList.join(" · ") || "Available"}
            badText="OSM fallback only"
            detail="Satellite, terrain and 3D building sources"
          />
        </div>

        {status.ai.ollama && (
          <div className="mt-3 border-t border-border pt-1">
            <StatusRow
              label="Ollama (local)"
              ok={status.ai.ollama.available && status.ai.ollama.model_ready}
              okText={status.ai.ollama.model_ready ? status.ai.ollama.model : "Running"}
              badText={status.ai.ollama.available ? "Model not pulled" : "Offline"}
              detail={status.ai.ollama.available ? "Local model endpoint" : status.ai.ollama.base_url}
            />
          </div>
        )}

        {status.production && (
          <div className="mt-3 flex flex-wrap items-center gap-2 border-t border-border pt-3">
            <Badge variant={status.production.deployment_ready ? "success" : "warning"}>
              {status.production.deployment_ready ? "Deployment ready" : "Needs attention"}
            </Badge>
            {status.production.critical_count > 0 && (
              <Badge variant="destructive">{status.production.critical_count} critical</Badge>
            )}
            {status.production.warning_count > 0 && (
              <Badge variant="warning">{status.production.warning_count} warnings</Badge>
            )}
            {status.production.auth_required && <Badge variant="outline">Auth required</Badge>}
          </div>
        )}

        <div className="mt-3 flex items-center justify-between gap-3 border-t border-border pt-3 text-[11px] text-muted-foreground">
          <span className="border-l-2 border-primary pl-2">{status.disclaimer}</span>
          {updatedAt && <span className="shrink-0 font-mono">{updatedAt.toLocaleTimeString()}</span>}
        </div>
      </CardContent>
    </Card>
  );
}

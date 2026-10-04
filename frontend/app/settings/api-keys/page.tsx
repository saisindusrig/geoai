"use client";

import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { api } from "@/lib/api";
import type { SatelliteTileConfig, TerrainTileConfig } from "@/lib/map-imagery";
import type { SystemStatus } from "@/lib/types";

interface Providers {
  cesium_ion_available: boolean;
  google_3d_tiles_available: boolean;
  mapbox_available: boolean;
  satellite_config: SatelliteTileConfig;
  terrain_config: TerrainTileConfig;
}

const PROVIDERS = [
  { env: "GOOGLE_MAPS_API_KEY", label: "Google Maps Platform", use: "Photorealistic 3D Tiles + geocoding" },
  { env: "CESIUM_ION_READ_TOKEN", label: "Cesium ion (restricted read)", use: "Browser access to world terrain & OSM 3D buildings; keep upload/write keys on the server" },
  { env: "MAPBOX_TOKEN", label: "Mapbox", use: "Geocoding + HD satellite imagery" },
  { env: "OPENAI_API_KEY", label: "OpenAI", use: "AI design generation" },
  { env: "ANTHROPIC_API_KEY", label: "Anthropic", use: "AI design generation" },
  { env: "GEMINI_API_KEY", label: "Google Gemini", use: "Not implemented yet — key stored for future use" },
];

export default function ProviderStatusPage() {
  const [providers, setProviders] = useState<Providers | null>(null);
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.get<Providers>("/api/geocode/tile-providers").catch(() => null),
      api.get<SystemStatus>("/api/system/status").catch(() => null),
    ]).then(([tileProviders, status]) => {
      setProviders(tileProviders);
      setSystemStatus(status);
      setLoading(false);
    });
  }, []);

  const status = (env: string): boolean | null => {
    if (systemStatus) {
      if (env === "OPENAI_API_KEY") return systemStatus.ai.openai_configured;
      if (env === "ANTHROPIC_API_KEY") return systemStatus.ai.anthropic_configured;
      if (env === "GEMINI_API_KEY") return systemStatus.ai.gemini_configured;
    }
    if (!providers) return null;
    if (env === "CESIUM_ION_READ_TOKEN") return providers.cesium_ion_available;
    if (env === "GOOGLE_MAPS_API_KEY") return providers.google_3d_tiles_available;
    if (env === "MAPBOX_TOKEN") return providers.mapbox_available;
    return null;
  };

  const satelliteLabel =
    providers?.satellite_config.provider === "mapbox"
      ? "Mapbox HD satellite (512px, zoom 22)"
      : "Esri World Imagery (zoom 22 fallback)";

  const terrainLabel = `Esri World Topo (tiles to z${providers?.terrain_config.max_zoom ?? 17}, overzoom to z20)`;

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="max-w-3xl mx-auto w-full px-6 py-8 space-y-5">
        <div>
          <p className="font-mono text-[10px] uppercase tracking-[0.16em] text-primary">GeoAI / system</p>
          <h1 className="mt-3 border-b border-border pb-5 text-[36px] font-medium tracking-[-0.045em]">Provider Status</h1>
          <p className="mt-2 text-sm text-muted-foreground">
            Live status from <code className="font-data text-xs">/api/system/status</code> and tile providers.
            Keys are configured in backend <code className="font-data text-xs">.env</code> — not entered in this UI.
          </p>
        </div>

        <Card float className="border-primary/25 bg-primary/[0.04]">
          <CardContent className="space-y-3 p-5">
            <div><h2 className="text-base font-semibold">Connect Cesium World Terrain</h2><p className="mt-1 text-xs leading-relaxed text-muted-foreground">The current map uses a flat ellipsoid because no Cesium read token is configured. Your ion account already has World Terrain (asset 1) and OSM Buildings (asset 96188).</p></div>
            <ol className="space-y-1.5 text-xs text-muted-foreground"><li>1. Create an app token with <code className="text-foreground">assets:read</code> only.</li><li>2. Restrict it to assets <code className="text-foreground">1</code> and <code className="text-foreground">96188</code>; allow <code className="text-foreground">http://localhost:3000</code>.</li><li>3. Add <code className="text-foreground">CESIUM_ION_READ_TOKEN=your_token</code> to the project root <code className="text-foreground">.env</code> and restart the backend.</li></ol>
            <a className="inline-flex items-center rounded-lg bg-primary px-3 py-2 text-xs font-semibold text-primary-foreground" href="https://ion.cesium.com/tokens" target="_blank" rel="noreferrer">Create Cesium ion token</a>
          </CardContent>
        </Card>

        {loading && (
          <Card>
            <CardContent className="py-6 flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              Loading system status…
            </CardContent>
          </Card>
        )}

        {systemStatus && (
          <Card float className="divide-y divide-border">
            <CardContent className="py-3 px-4 flex items-center justify-between gap-4">
              <div>
                <div className="text-sm font-medium">Database</div>
                <div className="text-xs text-muted-foreground">{systemStatus.database_mode_label}</div>
              </div>
              <Badge variant={systemStatus.postgis_available ? "success" : "warning"}>
                {systemStatus.postgis_available ? "PostGIS" : "SQLite"}
              </Badge>
            </CardContent>
            <CardContent className="py-3 px-4 flex items-center justify-between gap-4">
              <div>
                <div className="text-sm font-medium">Jobs & storage</div>
                <div className="text-xs text-muted-foreground">
                  {systemStatus.job_store} · {systemStatus.storage_mode}
                </div>
              </div>
              <Badge variant={systemStatus.redis_available ? "success" : "secondary"}>
                Redis {systemStatus.redis_available ? "on" : "off"}
              </Badge>
            </CardContent>
            <CardContent className="py-3 px-4 flex items-center justify-between gap-4">
              <div>
                <div className="text-sm font-medium">AI provider</div>
                <div className="text-xs text-muted-foreground">
                  Active: {systemStatus.ai.active_provider}
                  {systemStatus.ai.mock_mode ? " (mock)" : ""}
                </div>
              </div>
              <Badge variant={systemStatus.ai.mock_mode ? "warning" : "success"}>
                {systemStatus.ai.configured_provider || "default"}
              </Badge>
            </CardContent>
            {systemStatus.production && (
              <CardContent className="py-3 px-4">
                <div className="flex flex-wrap gap-2">
                  <Badge variant={systemStatus.production.deployment_ready ? "success" : "warning"}>
                    {systemStatus.production.deployment_ready ? "Deployment ready" : "Needs attention"}
                  </Badge>
                  {systemStatus.production.critical_count > 0 && (
                    <Badge variant="destructive">{systemStatus.production.critical_count} critical</Badge>
                  )}
                </div>
              </CardContent>
            )}
          </Card>
        )}

        {providers && (
          <Card float className="divide-y divide-border">
            <CardContent className="py-3 px-4 flex items-center justify-between gap-4">
              <div>
                <div className="text-sm font-medium">Satellite imagery</div>
                <div className="text-xs text-muted-foreground">{satelliteLabel}</div>
              </div>
              <Badge variant={providers.satellite_config.provider === "mapbox" ? "success" : "default"}>
                {providers.satellite_config.provider === "mapbox" ? "HD" : "standard"}
              </Badge>
            </CardContent>
            <CardContent className="py-3 px-4 flex items-center justify-between gap-4">
              <div>
                <div className="text-sm font-medium">Terrain basemap</div>
                <div className="text-xs text-muted-foreground">{terrainLabel}</div>
              </div>
              <Badge variant="success">HD</Badge>
            </CardContent>
            <CardContent className="py-3 px-4 flex items-center justify-between gap-4">
              <div>
                <div className="text-sm font-medium">3D buildings</div>
                <div className="text-xs text-muted-foreground">
                  {providers.google_3d_tiles_available
                    ? "Google Photorealistic 3D Tiles"
                    : providers.cesium_ion_available
                      ? "Cesium OSM Buildings (Ion)"
                      : "Procedural OSM extrusions only"}
                </div>
              </div>
              <Badge
                variant={
                  providers.google_3d_tiles_available || providers.cesium_ion_available
                    ? "success"
                    : "warning"
                }
              >
                {providers.google_3d_tiles_available
                  ? "Google"
                  : providers.cesium_ion_available
                    ? "Cesium"
                    : "fallback"}
              </Badge>
            </CardContent>
          </Card>
        )}

        <Card float className="divide-y divide-border">
          {PROVIDERS.map((k) => {
            const s = status(k.env);
            return (
              <CardContent key={k.env} className="flex items-center gap-4 py-3 px-4">
                <div className="flex-1">
                  <div className="text-sm font-medium">{k.label}</div>
                  <div className="text-xs text-muted-foreground">
                    <code className="font-data">{k.env}</code> — {k.use}
                  </div>
                </div>
                {s === null ? (
                  <Badge variant="default">server-side</Badge>
                ) : s ? (
                  <Badge variant="success">active</Badge>
                ) : (
                  <Badge variant="warning">fallback</Badge>
                )}
              </CardContent>
            );
          })}
        </Card>
      </div>
    </div>
  );
}

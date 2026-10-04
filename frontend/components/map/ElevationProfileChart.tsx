"use client";

import { useEffect, useState } from "react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { CHART } from "@/lib/chart-theme";
import { api } from "@/lib/api";
import type { Project } from "@/lib/types";

interface Point {
  distance_m: number;
  elevation_m: number | null;
}

interface Props {
  project: Project;
}

export default function ElevationProfileChart({ project }: Props) {
  const [points, setPoints] = useState<Point[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!project.alignment_geojson) return;
    let cancelled = false;
    api
      .get<{ points: Point[] }>(`/api/projects/${project.id}/site-analysis/elevation-profile`)
      .then((res) => {
        if (cancelled) return;
        setPoints(res.points);
        setError("");
      })
      .catch((e) => {
        if (cancelled) return;
        setPoints([]);
        setError(e instanceof Error ? e.message : String(e));
      });
    return () => {
      cancelled = true;
    };
  }, [project.id, project.alignment_geojson]);

  if (!project.alignment_geojson) return null;
  if (error) {
    return (
      <div className="absolute bottom-16 left-3 right-3 z-20 panel-glass rounded-md px-3 py-2 text-[10px] text-muted-foreground">
        Elevation profile: {error}
      </div>
    );
  }
  if (points.length === 0) return null;

  return (
    <div className="absolute bottom-16 left-3 right-3 z-20 panel-glass rounded-lg p-2 max-w-xl pointer-events-auto">
      <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground mb-1">
        Elevation Profile · VISUAL REFERENCE
      </p>
      {points.every((p) => p.elevation_m === null) && <p className="text-[10px] text-amber-200">Terrain samples unavailable — elevations are unknown.</p>}
      <div className="h-24">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={points}>
            <CartesianGrid strokeDasharray="3 3" stroke={CHART.grid} />
            <XAxis
              dataKey="distance_m"
              tick={{ fontSize: 9, fill: CHART.tick }}
              tickFormatter={(v) => `${v}m`}
            />
            <YAxis tick={{ fontSize: 9, fill: CHART.tick }} unit="m" width={32} />
            <Tooltip contentStyle={CHART.tooltip} />
            <Line type="monotone" dataKey="elevation_m" stroke={CHART.accent} dot={false} strokeWidth={2} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

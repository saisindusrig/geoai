"use client";

import { Upload } from "lucide-react";
import { useRef } from "react";
import { Button } from "@/components/ui/button";
import type { GeoJSONGeometry } from "@/lib/types";
import { toast } from "@/lib/toast";
import { parseKmlToGeometry } from "@/lib/map-draw";

interface Props {
  onImportBoundary?: (g: GeoJSONGeometry) => void | Promise<void>;
  onImportAlignment?: (g: GeoJSONGeometry) => void | Promise<void>;
  boundary?: GeoJSONGeometry | null;
  alignment?: GeoJSONGeometry | null;
}

function extractGeometry(raw: unknown): GeoJSONGeometry | null {
  if (!raw || typeof raw !== "object") return null;
  const obj = raw as Record<string, unknown>;
  if (obj.type === "FeatureCollection") {
    const feats = obj.features as { geometry?: GeoJSONGeometry }[] | undefined;
    const geom = feats?.[0]?.geometry;
    return geom?.type === "Polygon" || geom?.type === "LineString" ? geom : null;
  }
  if (obj.type === "Feature") {
    const geom = (obj as { geometry?: GeoJSONGeometry }).geometry;
    return geom?.type === "Polygon" || geom?.type === "LineString" ? geom : null;
  }
  if (obj.type === "Polygon" || obj.type === "LineString") {
    return obj as unknown as GeoJSONGeometry;
  }
  return null;
}

export default function GeoJsonImport({ onImportBoundary, onImportAlignment }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFile = async (file: File) => {
    try {
      const text = await file.text();
      const isKml = file.name.toLowerCase().endsWith(".kml");
      const geom = isKml ? parseKmlToGeometry(text) : extractGeometry(JSON.parse(text) as unknown);
      if (!geom) {
        toast("Invalid file", { description: "Need Polygon or LineString geometry", variant: "error" });
        return;
      }
      if (geom.type === "Polygon") {
        await onImportBoundary?.(geom);
        toast("Boundary imported", { variant: "success" });
      } else {
        await onImportAlignment?.(geom);
        toast("Alignment imported", { variant: "success" });
      }
    } catch (e) {
      toast("Import failed", {
        description: e instanceof Error ? e.message : String(e),
        variant: "error",
      });
    }
  };

  return (
    <>
      <input
        title="Import GeoJSON / KML"
        ref={inputRef}
        type="file"
        accept=".geojson,.json,.kml"
        className="hidden"
        onChange={(e) => {
          const f = e.target.files?.[0];
          if (f) handleFile(f);
          e.target.value = "";
        }}
      />
      <Button
        variant="ghost"
        size="sm"
        className="w-full justify-start gap-2 h-8 text-[11px]"
        onClick={() => inputRef.current?.click()}
      >
        <Upload className="h-3.5 w-3.5" />
        Import GeoJSON / KML
      </Button>
    </>
  );
}

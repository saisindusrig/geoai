"use client";

import { useEffect, useRef, useState } from "react";
import { Search, X, MapPin } from "lucide-react";
import type { GeocodeResult } from "@/lib/types";
import { api } from "@/lib/api";

export default function WorkspaceSearch({ onClose, onNavigate }: { onClose: () => void; onNavigate: (lng: number, lat: number) => void }) {
  const [query, setQuery] = useState("");
  const [places, setPlaces] = useState<GeocodeResult[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [active, setActive] = useState(0);
  const request = useRef(0);
  useEffect(() => {
    const dismiss = (event: PointerEvent) => {
      if (!(event.target instanceof Element) || !event.target.closest('[data-workspace-popup="search"]')) onClose();
    };
    document.addEventListener("pointerdown", dismiss);
    return () => document.removeEventListener("pointerdown", dismiss);
  }, [onClose]);
  const resultList = useRef<HTMLDivElement>(null);
  useEffect(() => () => { request.current++; }, []);
  useEffect(() => { resultList.current?.querySelector('[aria-current="true"]')?.scrollIntoView({ block: "nearest" }); }, [active]);
  const coordinate = query.trim().match(/^(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)$/);
  const lat = coordinate ? Number(coordinate[1]) : NaN, lng = coordinate ? Number(coordinate[2]) : NaN;
  const validCoordinate = !!coordinate && Math.abs(lat) <= 90 && Math.abs(lng) <= 180;
  const searchPlaces = async () => {
    const sequence = ++request.current;
    setError(""); setPlaces([]);
    if (validCoordinate) { onNavigate(lng, lat); onClose(); return; }
    if (coordinate) { setError("Latitude must be −90 to 90 and longitude −180 to 180."); return; }
    if (query.trim().length < 2) { setError("Enter at least two characters or latitude, longitude."); return; }
    setBusy(true);
    try { const data = await api.get<{ results: GeocodeResult[] }>(`/api/geocode?q=${encodeURIComponent(query.trim())}`); if (sequence === request.current) { setPlaces(data.results); setActive(0); if (!data.results.length) setError("No places found. Try a city, address or coordinates."); } }
    catch { if (sequence === request.current) setError("Location search is unavailable. Try again or enter coordinates."); }
    finally { if (sequence === request.current) setBusy(false); }
  };
  const choose = (index: number) => {
    const place = places[index];
    if (!place) return;
    onNavigate(place.lng, place.lat);
    onClose();
  };
  const count = places.length;
  return <section data-workspace-popup="search" aria-label="Workspace search" className="absolute left-1/2 top-16 z-50 w-[480px] max-w-[calc(100%-5rem)] -translate-x-1/2 ">
    <div className="flex items-center gap-3 rounded-lg bg-[#101914]/95 px-4 shadow-lg backdrop-blur-md"><Search className="size-4 shrink-0 text-muted-foreground" /><input autoFocus aria-label="Search workspace query" className="h-12 min-w-0 flex-1 !border-0 !bg-transparent !shadow-none text-sm outline-none !ring-0 !outline-none" placeholder="City, address or latitude, longitude…" value={query} onChange={event => { request.current++; setBusy(false); setQuery(event.target.value); setActive(0); setPlaces([]); setError(""); }} onKeyDown={event => {
      if (event.key === "Escape") { event.stopPropagation(); onClose(); }
      if (event.key === "ArrowDown" || event.key === "ArrowUp") { event.preventDefault(); setActive(previous => Math.max(0, Math.min(count - 1, previous + (event.key === "ArrowDown" ? 1 : -1)))); }
      if (event.key === "Enter") { event.preventDefault(); if (!places.length) void searchPlaces(); else choose(active); }
    }} /><button className="text-xs text-primary disabled:opacity-40" disabled={busy} onClick={() => void searchPlaces()}>{busy ? "Searching…" : "Find"}</button><button type="button" aria-label="Close workspace search" className="shrink-0 p-1 text-muted-foreground hover:text-foreground" onClick={onClose}><X className="size-4" /></button></div>
    {error && <p role="alert" className="px-4 py-3 text-xs text-amber-200">{error}</p>}
    {places.length > 0 && <div ref={resultList} className="mt-2 max-h-64 overflow-y-auto rounded-lg bg-[#101914]/95 px-2 py-2 shadow-lg backdrop-blur-md" aria-label="Search results">{places.map((place, index) => <button key={`${place.name}-${index}`} aria-current={active === index ? "true" : undefined} className={`flex w-full items-center gap-2 px-2 py-2 text-left text-xs ${active === index ? "bg-primary/10" : "hover:bg-white/5"}`} onClick={() => choose(index)}><MapPin className="size-4 shrink-0" /><span>{place.name}<span className="block text-[10px] text-muted-foreground">{place.lat.toFixed(5)}, {place.lng.toFixed(5)} · {place.provider}</span></span></button>)}</div>}
  </section>;
}






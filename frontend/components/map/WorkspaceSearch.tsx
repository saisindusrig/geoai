"use client";

import { useEffect, useRef, useState } from "react";
import { Search, X, MapPin, Box } from "lucide-react";
import type { EditableModelEditor } from "@/hooks/useEditableModelEditor";
import type { GeocodeResult } from "@/lib/types";
import { api } from "@/lib/api";

export default function WorkspaceSearch({ editor, onClose, onNavigate }: { editor?: EditableModelEditor; onClose: () => void; onNavigate: (lng: number, lat: number) => void }) {
  const [query, setQuery] = useState("");
  const [scope, setScope] = useState<"scene" | "places">("scene");
  const [places, setPlaces] = useState<GeocodeResult[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [active, setActive] = useState(0);
  const request = useRef(0);
  const resultList = useRef<HTMLDivElement>(null);
  useEffect(() => () => { request.current++; }, []);
  useEffect(() => { resultList.current?.querySelector('[aria-current="true"]')?.scrollIntoView({ block: "nearest" }); }, [active]);
  const tokens = query.toLowerCase().trim().split(/\s+/).filter(Boolean);
  const components = (editor?.document?.components ?? []).filter(component => tokens.every(token => {
    if (token.startsWith("layer:")) return component.category.toLowerCase().includes(token.slice(6));
    if (token === "is:hidden") return !component.visible;
    if (token === "is:visible") return component.visible;
    if (token === "is:locked") return component.locked;
    if (token === "is:selected") return !!editor?.selectedIds.includes(component.id);
    const text = `${component.name} ${component.category} ${component.material.name}`.toLowerCase();
    if (text.includes(token)) return true;
    let index = 0;
    for (const character of text) if (character === token[index]) index++;
    return index === token.length;
  })).sort((a, b) => Number(b.name.toLowerCase().startsWith(query.toLowerCase())) - Number(a.name.toLowerCase().startsWith(query.toLowerCase())) || a.name.localeCompare(b.name, undefined, { numeric: true }));
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
    if (scope === "scene") { const component = components[index]; if (!component) return; editor?.select(component.id); window.dispatchEvent(new CustomEvent("geoai:locate-component", { detail: component.id })); }
    else { const place = places[index]; if (!place) return; onNavigate(place.lng, place.lat); }
    onClose();
  };
  const displayedComponents = query.trim() ? components : components.slice(0, 6);
  const count = scope === "scene" ? displayedComponents.length : places.length;
  const toggleFilter = (token: string) => { setQuery(previous => previous.split(/\s+/).includes(token) ? previous.split(/\s+/).filter(value => value !== token).join(" ") : `${previous} ${token}`.trim()); setActive(0); };
  return <section aria-label="Workspace search" className="absolute left-1/2 top-16 z-50 w-[480px] max-w-[calc(100%-5rem)] -translate-x-1/2 overflow-hidden rounded-xl border border-white/15 bg-[#101914]/98 shadow-2xl backdrop-blur-xl">
    <div className="flex items-center justify-between px-4 pt-4"><div><h2 className="text-sm font-semibold">Find in workspace</h2><p className="mt-1 text-[11px] text-muted-foreground">Locate an object or explore a place</p></div><button aria-label="Close workspace search" className="p-2 text-muted-foreground hover:text-foreground" onClick={onClose}><X className="size-4" /></button></div>
    <div className="mx-4 mb-3 mt-3 flex gap-5 border-b border-white/10 text-xs">{(["scene", "places"] as const).map(value => <button key={value} aria-pressed={scope === value} className={`flex items-center gap-2 border-b-2 py-2 ${scope === value ? "border-primary text-primary" : "border-transparent text-muted-foreground"}`} onClick={() => { request.current++; setBusy(false); setScope(value); setQuery(""); setActive(0); setPlaces([]); setError(""); }}>{value === "scene" ? <Box className="size-3.5" /> : <MapPin className="size-3.5" />}{value === "scene" ? "Objects" : "Places"}</button>)}</div>
    <div className="mx-4 flex items-center gap-2 rounded-lg border border-white/15 bg-black/20 px-3 focus-within:border-primary/60"><Search className="size-4 shrink-0 text-muted-foreground" /><input autoFocus aria-label="Search workspace query" className="h-11 min-w-0 flex-1 bg-transparent text-sm outline-none" placeholder={scope === "scene" ? "Search objects, layers or materials…" : "City, address or latitude, longitude…"} value={query} onChange={event => { request.current++; setBusy(false); setQuery(event.target.value); setActive(0); setPlaces([]); setError(""); }} onKeyDown={event => {
      if (event.key === "Escape") { event.stopPropagation(); onClose(); }
      if (event.key === "ArrowDown" || event.key === "ArrowUp") { event.preventDefault(); setActive(previous => Math.max(0, Math.min(count - 1, previous + (event.key === "ArrowDown" ? 1 : -1)))); }
      if (event.key === "Enter") { event.preventDefault(); if (scope === "places" && !places.length) void searchPlaces(); else choose(active); }
    }} />{scope === "places" && <button className="text-xs text-primary disabled:opacity-40" disabled={busy} onClick={() => void searchPlaces()}>{busy ? "Searching…" : "Find"}</button>}</div>
    {scope === "scene" && <div className="mx-4 mt-3 flex flex-wrap gap-1.5">{([ ["Selected", "is:selected"], ["Hidden", "is:hidden"], ["Locked", "is:locked"] ] as const).map(([label, token]) => <button key={token} aria-pressed={tokens.includes(token)} onClick={() => toggleFilter(token)} className={`rounded-full border px-2.5 py-1 text-[11px] ${tokens.includes(token) ? "border-primary/50 bg-primary/10 text-primary" : "border-white/10 text-muted-foreground hover:border-white/30"}`}>{label}</button>)}<select aria-label="Filter search by layer" value={tokens.find(token => token.startsWith("layer:"))?.slice(6) ?? ""} onChange={event => { setQuery(previous => [...previous.split(/\s+/).filter(token => !token.startsWith("layer:")), ...(event.target.value ? [`layer:${event.target.value}`] : [])].join(" ").trim()); setActive(0); }} className="min-w-0 rounded-full border border-white/10 bg-[#101914] px-2 text-[11px] text-muted-foreground"><option value="">All layers</option>{[...new Set(editor?.document?.components.map(component => component.category) ?? [])].map(category => <option key={category} value={category}>{category}</option>)}</select>{query && <button className="ml-auto text-[11px] text-muted-foreground" onClick={() => { setQuery(""); setActive(0); }}>Clear</button>}</div>}
    <p className="mx-4 mb-2 mt-3 text-[10px] uppercase tracking-wider text-muted-foreground">{scope === "scene" ? query.trim() ? `${components.length} matching objects` : `Browse objects · ${components.length} in scene` : "Search places or paste coordinates"}</p>
    {error && <p role="alert" className="py-2 text-xs text-amber-200">{error}</p>}
    <div ref={resultList} className="max-h-64 overflow-y-auto px-2" aria-label="Search results">{scope === "scene" ? displayedComponents.map((component, index) => <button key={component.id} aria-current={active === index ? "true" : undefined} className={`flex w-full items-center gap-3 rounded-md px-3 py-3 text-left text-xs ${active === index ? "bg-primary/10" : "hover:bg-white/5"}`} onClick={() => choose(index)}><Box className="size-3.5 shrink-0" /><span className="min-w-0 flex-1 truncate">{component.name}<span className="mt-0.5 block text-[10px] text-muted-foreground">{component.category} · {component.material.name}</span></span><span className="text-[9px] text-muted-foreground">{!component.visible && "Hidden "}{component.locked && "Locked"}</span></button>) : places.map((place, index) => <button key={`${place.name}-${index}`} aria-current={active === index ? "true" : undefined} className={`flex w-full items-center gap-2 px-2 py-2 text-left text-xs ${active === index ? "bg-primary/10" : "hover:bg-white/5"}`} onClick={() => choose(index)}><MapPin className="size-4 shrink-0" /><span>{place.name}<span className="block text-[10px] text-muted-foreground">{place.lat.toFixed(5)}, {place.lng.toFixed(5)} · {place.provider}</span></span></button>)}</div>
    {scope === "scene" && !components.length && <p className="py-4 text-center text-xs text-muted-foreground">No matching objects. Try a shorter name or remove a filter.</p>}
    {scope === "places" && !places.length && !error && !busy && <div className="px-6 py-6 text-center"><MapPin className="mx-auto mb-2 size-5 text-muted-foreground" /><p className="text-xs text-muted-foreground">Find a city, street or landmark.</p><p className="mt-1 text-[11px] text-muted-foreground">Coordinates: 12.9716, 77.5946</p></div>}
    <div className="mt-2 flex justify-between border-t border-white/10 px-4 py-2.5 text-[10px] text-muted-foreground"><span>↑ ↓ Navigate · ↵ Locate · Esc Close</span><span>{scope === "scene" ? "Search names or use filters" : "Camera only"}</span></div>
  </section>;
}


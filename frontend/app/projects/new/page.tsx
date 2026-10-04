"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState, type KeyboardEvent } from "react";
import { Anchor, ArrowRight, Box, Building2, Check, Droplets, Factory, LandPlot, Leaf, Loader2, Network, Radio, Route, Search, Sprout, X, Zap, type LucideIcon } from "lucide-react";
import BrandWordmark from "@/components/landing/BrandWordmark";
import { ASSET_CATEGORIES, ASSET_TYPES, assetDefinition, searchAssets } from "@/lib/asset-types";
import { UNIT_OPTIONS, unitLabel } from "@/lib/project-catalog";
import { api } from "@/lib/api";
import { toastPromise } from "@/lib/toast";
import type { Project } from "@/lib/types";
import styles from "./workspace.module.css";

const ICONS: Record<string, LucideIcon> = { route: Route, building: Building2, droplets: Droplets, network: Network, zap: Zap, anchor: Anchor, land: LandPlot, factory: Factory, leaf: Leaf, sprout: Sprout, radio: Radio, box: Box };
const categoryLabel = (id: string) => ASSET_CATEGORIES.find((category) => category.id === id)?.label ?? id;

export default function NewProjectPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [assetId, setAssetId] = useState("flyover");
  const [units, setUnits] = useState("metric");
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState("all");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const searchRef = useRef<HTMLInputElement>(null);
  const resultsRef = useRef<HTMLDivElement>(null);
  const submissionRef = useRef(false);
  const selected = assetDefinition(assetId);
  const results = searchAssets(query, category);
  const ready = Boolean(name.trim() && selected && units && !saving);

  useEffect(() => {
    const requested = new URLSearchParams(window.location.search).get("template");
    const frame = window.requestAnimationFrame(() => {
      if (requested && assetDefinition(requested)?.status === "available") setAssetId(requested);
    });
    const shortcut = (event: globalThis.KeyboardEvent) => {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        searchRef.current?.focus();
        searchRef.current?.select();
      }
    };
    window.addEventListener("keydown", shortcut);
    return () => { window.cancelAnimationFrame(frame); window.removeEventListener("keydown", shortcut); };
  }, []);

  const updateSearch = (value: string) => {
    setQuery(value);
    setCategory("all"); // Search is always the fastest route across the entire catalogue.
    resultsRef.current?.scrollTo({ top: 0 });
  };
  const focusResult = (index: number) => {
    const buttons = resultsRef.current?.querySelectorAll<HTMLButtonElement>('[role="radio"]');
    if (!buttons?.length) return;
    const button = buttons[Math.max(0, Math.min(index, buttons.length - 1))];
    button.focus({ preventScroll: true });
    button.scrollIntoView({ block: "nearest" });
  };
  const navigateResults = (event: KeyboardEvent<HTMLButtonElement>, index: number) => {
    const movements: Record<string, number> = { ArrowDown: 2, ArrowUp: -2, ArrowRight: 1, ArrowLeft: -1 };
    if (event.key in movements) {
      event.preventDefault();
      focusResult(index + movements[event.key]);
    } else if (event.key === "Home" || event.key === "End") {
      event.preventDefault();
      focusResult(event.key === "Home" ? 0 : results.length - 1);
    } else if (event.key === "Escape") {
      updateSearch("");
      searchRef.current?.focus();
    }
  };
  const create = async () => {
    if (!ready || submissionRef.current) return;
    submissionRef.current = true;
    setSaving(true);
    setError("");
    try {
      const project = await toastPromise(api.post<Project>("/api/projects", {
        name: name.trim(), project_type: assetId, units,
        location_name: "", center_lat: 12.9716, center_lng: 77.5946,
        boundary_geojson: null, alignment_geojson: null,
      }), { loading: "Creating project…", success: "Project created" });
      router.push(`/projects/${project.id}/workspace`);
    } catch (error) {
      setError(error instanceof Error ? error.message : "Unable to create project.");
      submissionRef.current = false;
      setSaving(false);
    }
  };
  const tabIndex = Math.max(0, results.findIndex((asset) => asset.id === assetId));

  return (
    <div className={styles.workspace}>
      <header className={styles.header}>
        <Link href="/" aria-label="GeoAI home"><BrandWordmark size="nav" /></Link>
        <span className={styles.headerTitle}>NEW PROJECT <span>/ WORKSPACE SETUP</span></span>
        <Link href="/dashboard" className={styles.exit}>Exit to projects <ArrowRight size={14} /></Link>
      </header>
      <div className={styles.notice}><span aria-hidden="true">⚠</span><strong>CONCEPT-STAGE PLANNING</strong><span>Final construction drawings and quantities require verified engineering and survey data.</span></div>
      <main id="main-content" className={styles.columns}>
        <nav className={styles.rail} aria-label="Asset categories">
          <p className={styles.label}>CATEGORIES</p>
          <div className={styles.railSearch}><Search size={14} /><input aria-label="Search all assets" placeholder="Search all assets…" value={query} onChange={(event) => updateSearch(event.target.value)} onKeyDown={(event) => { if (event.key === "Escape") updateSearch(""); if (event.key === "ArrowDown") { event.preventDefault(); focusResult(0); } }} /></div>
          <div className={styles.categoryList}>
            {[{ id: "all", label: "All assets", icon: "box" }, ...ASSET_CATEGORIES].map((item) => {
              const Icon = ICONS[item.icon] ?? Box;
              const count = item.id === "all" ? ASSET_TYPES.length : ASSET_TYPES.filter((asset) => asset.category === item.id).length;
              return <button key={item.id} type="button" aria-current={category === item.id ? "true" : undefined} onClick={() => { setCategory(item.id); setQuery(""); resultsRef.current?.scrollTo({ top: 0 }); }} className={category === item.id ? styles.activeCategory : ""}><Icon size={15} strokeWidth={1.6} /><span>{item.label}</span><small>{count}</small></button>;
            })}
          </div>
          <div className={styles.railFoot}><span className={styles.dot} />Infrastructure catalogue<p>{ASSET_TYPES.length} asset types · {ASSET_CATEGORIES.length} categories</p></div>
        </nav>
        <section className={styles.center} aria-labelledby="new-project-title">
          <div className={styles.basics}>
            <div className={styles.titleLine}><h1 id="new-project-title">New project</h1><span className={styles.label}>01 / DEFINE THE ASSET</span></div>
            <p className={styles.intro}>Define the project asset. Site, terrain and alignment are configured inside the workspace.</p>
            <label htmlFor="project-name" className={styles.label}>PROJECT NAME</label>
            <input id="project-name" className={styles.nameInput} required maxLength={255} placeholder="NH-48 Junction Flyover" value={name} onChange={(event) => setName(event.target.value)} disabled={saving} autoFocus />
          </div>
          <div className={styles.libraryHeader}>
            <div className={styles.libraryTitle}><h2 className={styles.label}>ASSET TYPE</h2><span>{categoryLabel(category === "all" ? "All assets" : category)} <span className={styles.resultCount}>{results.length}</span></span></div>
            <div className={styles.search}><Search size={17} /><input ref={searchRef} aria-label="Search asset types" placeholder="Search bridges, roads, dams, pipelines, airports…" value={query} onChange={(event) => updateSearch(event.target.value)} onKeyDown={(event) => { if (event.key === "Escape") updateSearch(""); if (event.key === "ArrowDown") { event.preventDefault(); focusResult(0); } }} />{query ? <button type="button" aria-label="Clear asset search" onClick={() => updateSearch("")}><X size={15} /></button> : <kbd>Ctrl / ⌘ K</kbd>}</div>
          </div>
          <div className={styles.results} ref={resultsRef} role="radiogroup" aria-label="Asset types" aria-busy={saving}>
            {results.length ? <div className={styles.assetGrid}>{results.map((asset, index) => {
              const Icon = ICONS[asset.icon] ?? Box;
              const checked = assetId === asset.id;
              return <button key={asset.id} type="button" role="radio" aria-checked={checked} tabIndex={index === tabIndex ? 0 : -1} disabled={saving || asset.status === "planned"} onKeyDown={(event) => navigateResults(event, index)} onClick={() => setAssetId(asset.id)} className={`${styles.asset} ${checked ? styles.selectedAsset : ""}`} title={`${asset.description}. ${categoryLabel(asset.category)}. ${asset.maturity.toLowerCase()}${asset.supportsGeneration ? ": conceptual tools only" : ": site reference only; engineering generation unavailable"}.`}><Icon size={19} strokeWidth={1.5} /><span className={styles.assetText}><strong>{asset.name}</strong><span>{asset.description}</span><small>{categoryLabel(asset.category)}{asset.maturity !== "SUPPORTED" && <em> · {asset.maturity.toLowerCase()}</em>}</small></span><span className={styles.selection} aria-hidden="true">{checked && <Check size={10} strokeWidth={3} />}</span></button>;
            })}</div> : <div className={styles.empty}><Search size={24} /><strong>No assets match “{query}”</strong><p>Try a shorter name, or browse a category.</p><button type="button" onClick={() => updateSearch("")}>Clear search</button></div>}
          </div>
          <div className={styles.units}><label className={styles.label} htmlFor="project-units">UNITS</label><select id="project-units" value={units} disabled={saving} onChange={(event) => setUnits(event.target.value)}>{UNIT_OPTIONS.map((unit) => <option key={unit.id} value={unit.id}>{unit.label} — {unit.desc}{["metric", "indian"].includes(unit.id) ? " · Recommended" : ""}</option>)}</select><span>Change display units later</span></div>
        </section>
        <aside className={styles.summary} aria-label="Project summary">
          <h2 className={styles.label}>PROJECT SUMMARY</h2>
          <dl className={styles.details}>
            <div><dt>NAME</dt><dd className={styles.summaryName} title={name.trim()}>{name.trim() || "Untitled project"}</dd></div>
            <div><dt>ASSET</dt><dd>{selected?.name || "Select an asset"}</dd></div>
            <div className={styles.paired}><div><dt>CATEGORY</dt><dd>{selected ? categoryLabel(selected.category) : "—"}</dd></div><div><dt>UNITS</dt><dd>{unitLabel(units)}</dd></div></div>
          </dl>
          <div className={styles.capabilityNotice}><span className={styles.maturity}>{selected?.maturity.toLowerCase()}</span><p>{selected?.supportsGeneration ? "Concept tools available. Verify engineering inputs before using outputs." : "Site reference only. Engineering generation and asset-specific quantities are unavailable."}</p></div>
          <dl className={styles.later}>{["Location", "Terrain", "Boundary", "Alignment"].map((label) => <div key={label}><dt>{label}</dt><dd>Set in workspace</dd></div>)}</dl>
          <div className={styles.next}><h3 className={styles.label}>WHAT HAPPENS NEXT</h3><ol>{["Select site", "Load terrain", "Define boundary", "Create alignment", selected?.supportsGeneration ? "Generate / edit concept" : "Place / edit site references"].map((step, index) => <li key={step}><span>{String(index + 1).padStart(2, "0")}</span>{step}</li>)}</ol></div>
          <div className={styles.createArea}>{error && <p className={styles.error} role="alert">{error}</p>}<p className={styles.readyHint} aria-live="polite">{saving ? "Opening your workspace…" : name.trim() ? "Project definition ready" : "Name your project to continue"}</p><button type="button" className={styles.create} disabled={!ready} onClick={create}>{saving ? <><Loader2 size={16} className={styles.spinner} />Creating project…</> : <>CREATE PROJECT <ArrowRight size={17} /></>}</button></div>
        </aside>
      </main>
      <footer className={styles.footer}><span>Site, terrain, boundary and alignment are configured inside the workspace.</span><span>CONCEPT → WORKSPACE</span></footer>
    </div>
  );
}

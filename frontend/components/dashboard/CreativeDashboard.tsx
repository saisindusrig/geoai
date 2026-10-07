"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  ArrowRight,
  Building2,
  Route,
  Network,
  Droplets,
  Box,
  Clock3,
  Folder,
  MapPinned,
  MoreHorizontal,
  SearchX,
  Search,
  Plus,
  Settings,
  Shapes,
  Trash2,
  X,
} from "lucide-react";
import DashboardSidebar from "./DashboardSidebar";
import "./dashboard-hub.css";
import ConstructionPreview from "@/components/dashboard/ConstructionPreview";
import { api } from "@/lib/api";
import {
  CONSTRUCTION_LABELS,
  CONSTRUCTION_TYPES,
  type ConstructionType,
} from "@/lib/construction";
import { ASSET_CATEGORIES, ASSET_TYPES, assetDefinition, searchAssets } from "@/lib/asset-types";
import type { Project, ProjectFolder } from "@/lib/types";
import { LOCAL_SANDBOX_PATH } from "@/lib/local-sandbox";

type FolderFilter = "all" | "unfiled" | number;
type SortOption = "recent" | "name";

const QUICK_ASSETS = [
  {type: "bridge", title: "Bridge", category: "Transport", icon: Route},
  {type: "road", title: "Road", category: "Transport", icon: Route},
  {type: "pipeline", title: "Pipeline", category: "Utilities", icon: Network},
  {type: "dam", title: "Dam", category: "Water", icon: Droplets},
  {type: "building", title: "Building", category: "Structure", icon: Building2},
  {type: "flyover", title: "Flyover", category: "Transport", icon: Route},
];

function isConstructionType(value: string): value is ConstructionType {
  return CONSTRUCTION_TYPES.includes(value as ConstructionType);
}

function projectLocation(project: Project) {
  if (project.location_name) return project.location_name;
  return project.center_lat != null && project.center_lng != null
    ? `${project.center_lat.toFixed(4)}, ${project.center_lng.toFixed(4)}`
    : "Location not saved";
}

function relativeUpdate(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Recently updated";
  return new Intl.RelativeTimeFormat("en", { numeric: "auto" }).format(
    Math.round((date.getTime() - Date.now()) / 86_400_000),
    "day",
  );
}

function typeLabel(type: ConstructionType) {
  return assetDefinition(type)?.name ?? CONSTRUCTION_LABELS[type] ?? type;
}

export default function CreativeDashboard() {
  const searchRef = useRef<HTMLInputElement>(null);
  const [assetQuery, setAssetQuery] = useState("");
  const [assetCategory, setAssetCategory] = useState("all");
  const [assetSheet, setAssetSheet] = useState(false);

  const [collapsed,setCollapsed] = useState(false);
  const [section,setSection] = useState<"overview"|"concepts"|"templates">("overview");
  const [recentOnly,setRecentOnly] = useState(false);

  const [projects, setProjects] = useState<Project[] | null>(null);
  const [folders, setFolders] = useState<ProjectFolder[]>([]);
  const [query, setQuery] = useState("");
  const [typeFilter, setTypeFilter] = useState<"all" | ConstructionType>("all");
  const [folderFilter, setFolderFilter] = useState<FolderFilter>("all");
  const [sort, setSort] = useState<SortOption>("recent");
  const [error, setError] = useState<string | null>(null);
  const [activeMenu, setActiveMenu] = useState<number | null>(null);

  const [folderDialog, setFolderDialog] = useState<
    { kind: "create" } | { kind: "rename"; folder: ProjectFolder } | null
  >(null);
  const [folderName, setFolderName] = useState("");
  const [folderError, setFolderError] = useState<string | null>(null);
  const [savingFolder, setSavingFolder] = useState(false);

  const navigate = (target:"overview"|"concepts"|"templates") => { setSection(target); setActiveMenu(null); };
  useEffect(()=>{const key=(event:KeyboardEvent)=>{if((event.ctrlKey||event.metaKey)&&event.key.toLowerCase()==="k"){event.preventDefault();searchRef.current?.focus();}if(event.key==="Escape"){setActiveMenu(null);setAssetSheet(false);setFolderDialog(null);}};window.addEventListener("keydown",key);return()=>window.removeEventListener("keydown",key);},[]);
  useEffect(() => {
    if (!assetSheet && !folderDialog) return;
    const previous = document.activeElement as HTMLElement | null;
    const trapFocus = (event: KeyboardEvent) => {
      if (event.key !== "Tab") return;
      const dialog = document.querySelector<HTMLElement>('[role="dialog"]');
      const controls = dialog?.querySelectorAll<HTMLElement>('a[href], button:not([disabled]), input, select');
      if (!controls?.length) return;
      const first = controls[0];
      const last = controls[controls.length - 1];
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
    };
    window.addEventListener("keydown", trapFocus);
    return () => { window.removeEventListener("keydown", trapFocus); previous?.focus(); };
  }, [assetSheet, folderDialog]);

  const load = useCallback(async () => {
    try {
      const [savedProjects, savedFolders] = await Promise.all([
        api.get<Project[]>("/api/projects"),
        api.get<ProjectFolder[]>("/api/project-folders"),
      ]);
      setProjects(savedProjects);
      setFolders(savedFolders);
      setError(null);
    } catch {
      setProjects([]);
      setFolders([]);
      setError(
        "Saved concepts are unavailable while the local backend is offline. You can still start a new concept.",
      );
    }
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => void load(), 0);
    return () => window.clearTimeout(timer);
  }, [load]);

  // The desktop product bar owns global search; the dashboard owns the result set.
  useEffect(() => {
    const onSearch = (event: Event) => {
      setQuery((event as CustomEvent<string>).detail ?? "");
    };
    window.addEventListener("geoai:project-search", onSearch);
    return () =>
      window.removeEventListener("geoai:project-search", onSearch);
  }, []);

  const constructionProjects = useMemo(
    () =>
      (projects ?? []),
    [projects],
  );

  const visibleProjects = useMemo(() => {
    const search = query.trim().toLowerCase();
    return constructionProjects
      .filter((project) =>
        typeFilter === "all" ? true : project.project_type === typeFilter,
      )
      .filter((project) => {
        if (folderFilter === "all") return true;
        if (folderFilter === "unfiled") return project.folder_id == null;
        return project.folder_id === folderFilter;
      })
      .filter((project) =>
        search
          ? `${project.name} ${projectLocation(project)} ${project.project_type}`
              .toLowerCase()
              .includes(search)
          : true,
      )
      .sort((a, b) =>
        sort === "name"
          ? a.name.localeCompare(b.name)
          : new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime(),
      );
  }, [constructionProjects, folderFilter, query, sort, typeFilter]);

  const hasActiveFilter =
    Boolean(query.trim()) || typeFilter !== "all" || folderFilter !== "all";

  const moveProject = async (project: Project, folderId: number | null) => {
    setActiveMenu(null);
    try {
      const updated = await api.put<Project>(`/api/projects/${project.id}`, {
        folder_id: folderId,
      });
      setProjects(
        (current) =>
          current?.map((item) => (item.id === project.id ? updated : item)) ??
          current,
      );
    } catch {
      setError("The project folder could not be updated. Please try again.");
    }
  };

  const removeProject = async (project: Project) => {
    if (!window.confirm(`Delete “${project.name}”? This cannot be undone.`))
      return;
    try {
      await api.delete(`/api/projects/${project.id}`);
      setProjects(
        (current) =>
          current?.filter((item) => item.id !== project.id) ?? current,
      );
      setActiveMenu(null);
    } catch {
      setError("The project could not be deleted. Please try again.");
    }
  };

  const openFolderDialog = (folder?: ProjectFolder) => {
    setFolderError(null);
    setFolderName(folder?.name ?? "");
    setFolderDialog(folder ? { kind: "rename", folder } : { kind: "create" });
  };

  const saveFolder = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!folderDialog) return;
    setFolderError(null);
    setSavingFolder(true);
    try {
      if (folderDialog.kind === "create") {
        const folder = await api.post<ProjectFolder>("/api/project-folders", {
          name: folderName,
        });
        setFolders((current) =>
          [...current, folder].sort((a, b) => a.name.localeCompare(b.name)),
        );
      } else {
        const folder = await api.put<ProjectFolder>(
          `/api/project-folders/${folderDialog.folder.id}`,
          { name: folderName },
        );
        setFolders((current) =>
          current
            .map((item) => (item.id === folder.id ? folder : item))
            .sort((a, b) => a.name.localeCompare(b.name)),
        );
      }
      setFolderDialog(null);
    } catch {
      setFolderError("That folder name is unavailable. Try another name.");
    } finally {
      setSavingFolder(false);
    }
  };

  const deleteFolder = async (folder: ProjectFolder) => {
    if (
      !window.confirm(
        `Delete “${folder.name}”? Its projects will stay available as Unfiled.`,
      )
    )
      return;
    try {
      await api.delete(`/api/project-folders/${folder.id}`);
      setFolders((current) => current.filter((item) => item.id !== folder.id));
      setProjects(
        (current) =>
          current?.map((project) =>
            project.folder_id === folder.id
              ? { ...project, folder_id: null }
              : project,
          ) ?? current,
      );
      if (folderFilter === folder.id) setFolderFilter("all");
    } catch {
      setError("The folder could not be deleted. Please try again.");
    }
  };

  const showLibrary = section === "templates" || assetSheet;

  return (
    <div className={`geo-dashboard-hub ${collapsed?"hub-collapsed":""}`}>
      <DashboardSidebar folders={folders} selected={folderFilter} collapsed={collapsed} onCollapse={()=>setCollapsed(!collapsed)} onFolder={id=>{setFolderFilter(id);setRecentOnly(false);navigate("concepts");}} onManage={openFolderDialog} onNavigate={navigate} section={section}/>
      <div className="hub-main">
        <header className="hub-toolbar"><label className="hub-search"><Search size={16}/><input ref={searchRef} type="search" aria-label="Search concepts" placeholder="Search concepts..." value={query} onChange={event=>{setQuery(event.target.value); if(event.target.value) navigate("concepts");}}/><kbd>Ctrl K</kbd></label><div className="hub-toolbar-actions"><Link href={LOCAL_SANDBOX_PATH}><Box size={15}/>Open sandbox</Link><Link className="hub-primary" href="/projects/new"><Plus size={16}/>New concept</Link><Link href="/settings" title="Settings" aria-label="Open settings"><Settings size={17}/></Link></div></header>
        <div className={`hub-content ${section === "overview" ? "hub-command-center" : "hub-library-view"}`}>
          <section className="hub-overview"><span className="hub-micro">WORKSPACE / {section.toUpperCase()}</span><h1>{section === "overview" ? "Your concepts" : section === "concepts" ? "Concepts" : "Infrastructure templates"}</h1><p>{section === "templates" ? "Choose an asset from the complete infrastructure library." : "Your saved infrastructure work, together in one place."}</p></section>
          {section === "overview" && <>
          <section className="hub-assets"><div className="hub-section-heading"><div><h2>Start a new concept</h2><p>Choose an infrastructure type.</p></div><button onClick={()=>setAssetSheet(true)}>More assets <ArrowRight size={13}/></button></div><div className="hub-asset-row">{QUICK_ASSETS.map(({type,title,category,icon:Icon},index)=><Link className={index === 5 ? "hub-wide-asset" : ""} key={type} href={`/projects/new?template=${type}`}><Icon size={24}/><div><h3>{title}</h3><span className="hub-micro">{category}</span></div></Link>)}<button onClick={()=>setAssetSheet(true)}><Shapes size={24}/><div><h3>More assets →</h3><span className="hub-micro">{ASSET_TYPES.length} assets</span></div></button></div></section>
          </>}
          {section !== "templates" && <section id="hub-concepts" className="hub-all-concepts" aria-label="Saved concepts">
          <div className="hub-filters"><span className="hub-collection-count">{projects===null?"—":visibleProjects.length} concepts</span><div className="hub-filter-tabs"><button aria-pressed={folderFilter==="all"&&!recentOnly} onClick={()=>{setFolderFilter("all");setRecentOnly(false);}}>All</button><button aria-pressed={recentOnly} onClick={()=>{setRecentOnly(true);setSort("recent");setFolderFilter("all");}}>Recent</button><button aria-pressed={folderFilter==="unfiled"} onClick={()=>{setFolderFilter("unfiled");setRecentOnly(false);}}>Unfiled</button></div><select aria-label="Filter by concept type" value={typeFilter} onChange={e=>setTypeFilter(e.target.value as "all"|ConstructionType)}><option value="all">All types</option>{ASSET_TYPES.map(asset=><option key={asset.id} value={asset.id}>{asset.name}</option>)}</select>{typeof folderFilter==="number"&&<button className="hub-folder-chip" onClick={()=>setFolderFilter("all")}>{folders.find(f=>f.id===folderFilter)?.name}<X size={12}/></button>}<label className="hub-sort">Sort <select aria-label="Sort concepts" value={sort} onChange={e=>setSort(e.target.value as SortOption)}><option value="recent">Recently updated</option><option value="name">Name A–Z</option></select></label></div>
          {error && (
            <div className="mt-5 flex items-center justify-between rounded-xl border border-warning/25 bg-warning/10 px-4 py-3 text-sm text-warning-text">
              <span>{error}</span>
              <button
                type="button"
                onClick={() => void load()}
                className="font-semibold underline underline-offset-2"
              >
                Retry
              </button>
            </div>
          )}

          {projects === null && (
            <div
              className="hub-concept-grid"
              aria-label="Loading saved concepts"
            >
              {[0, 1, 2].map((item) => (
                <div
                  key={item}
                  className="h-72 animate-pulse rounded-2xl border border-border bg-card"
                />
              ))}
            </div>
          )}

          {projects !== null && visibleProjects.length === 0 && !error && (
            <div className="mt-5 rounded-2xl border border-dashed border-border bg-card px-7 py-14 text-center">
              {hasActiveFilter ? (
                <SearchX className="mx-auto size-6 text-primary" />
              ) : (
                <Folder className="mx-auto size-6 text-primary" />
              )}
              <h3 className="mt-3 font-semibold text-foreground">
                {hasActiveFilter
                  ? "No matching concepts"
                  : "No saved concepts yet"}
              </h3>
              <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-muted-foreground">
                {hasActiveFilter
                  ? "Adjust the search, type, or folder filters to see other saved workspaces."
                  : "Start from a location, create a concept, and save it here when you are ready to return."}
              </p>
              {hasActiveFilter ? (
                <button
                  type="button"
                  onClick={() => {
                    setQuery("");
                    setTypeFilter("all");
                    setFolderFilter("all");
                  }}
                  className="mt-5 inline-flex rounded-xl border border-border bg-background px-4 py-2.5 text-sm font-semibold text-foreground transition hover:border-primary/45"
                >
                  Clear filters
                </button>
              ) : (
                <Link
                  href="/projects/new"
                  className="mt-5 inline-flex rounded-xl bg-primary px-4 py-2.5 text-sm font-semibold text-primary-foreground"
                >
                  New concept
                </Link>
              )}
            </div>
          )}

          {visibleProjects.length > 0 && (
            <div className="hub-concept-grid">
              {(recentOnly ? visibleProjects.slice(0,6) : visibleProjects).map((project) => {
                const type = project.project_type as ConstructionType;
                const folder = folders.find(
                  (item) => item.id === project.folder_id,
                );
                return (
                  <article
                    key={project.id}
                    className="hub-concept-card group"
                  >
                    <Link
                      href={`/projects/${project.id}/workspace`}
                      className="hub-concept-link"
                    >
                      <div className="hub-concept-preview">
                        {isConstructionType(type) ? <ConstructionPreview type={type} className="h-full w-full" /> : <div className="hub-reference-preview"><Shapes size={32}/></div>}
                        <span className="absolute top-3 left-3 rounded-md border border-border bg-background/90 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wide text-foreground-secondary">
                          {typeLabel(type)}
                        </span>
                      </div>
                      <div className="p-4">
                        <div className="flex items-center gap-2">
                          <h3 className="min-w-0 flex-1 truncate font-semibold text-foreground">
                            {project.name}
                          </h3>
                          {project.status && <span className="hub-card-status">{project.status.replaceAll("_", " ")}</span>}
                          <ArrowRight className="size-4 shrink-0 text-primary transition-transform group-hover:translate-x-0.5" />
                        </div>
                        <p className="mt-2 flex items-center gap-1.5 truncate text-xs text-muted-foreground">
                          <MapPinned className="size-3.5 shrink-0" />
                          {projectLocation(project)}
                        </p>
                        
                        <p className="mt-2 flex items-center gap-1.5 text-xs text-muted-foreground">
                          <Clock3 className="size-3.5" />
                          Updated {relativeUpdate(project.updated_at)}
                          <span className="mx-1 text-border">•</span>
                          {folder?.name ?? "Unfiled"}
                        </p>
                      </div>
                    </Link>
                    <div className="flex items-center border-t border-border px-4 py-3">
                      <Link
                        href={`/projects/${project.id}/workspace`}
                        className="text-xs font-semibold text-primary hover:text-primary-hover"
                      >
                        Open workspace
                      </Link>
                      <button
                        type="button"
                        onClick={() =>
                          setActiveMenu((current) =>
                            current === project.id ? null : project.id,
                          )
                        }
                        aria-label={`Project options for ${project.name}`}
                        title={`Project options for ${project.name}`}
                        aria-expanded={activeMenu === project.id}
                        className="ml-auto rounded-lg p-1 text-muted-foreground transition hover:bg-surface-hover hover:text-foreground"
                      >
                        <MoreHorizontal className="size-4" />
                      </button>
                    </div>
                    {activeMenu === project.id && (
                      <div className="absolute bottom-10 right-3 z-20 w-52 rounded-xl border border-border bg-card p-2 shadow-[var(--shadow-lg)]">
                        <p className="px-2 pb-1 text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
                          Move to folder
                        </p>
                        <button
                          type="button"
                          onClick={() => void moveProject(project, null)}
                          className="flex w-full items-center rounded-lg px-2 py-2 text-left text-xs text-foreground transition hover:bg-surface-hover"
                        >
                          Unfiled
                        </button>
                        {folders.map((item) => (
                          <button
                            key={item.id}
                            type="button"
                            onClick={() => void moveProject(project, item.id)}
                            className="flex w-full items-center rounded-lg px-2 py-2 text-left text-xs text-foreground transition hover:bg-surface-hover"
                          >
                            {item.name}
                          </button>
                        ))}
                        <div className="my-1 border-t border-border" />
                        <button
                          type="button"
                          onClick={() => void removeProject(project)}
                          className="flex w-full items-center gap-2 rounded-lg px-2 py-2 text-left text-xs text-destructive transition hover:bg-destructive/10"
                        >
                          <Trash2 className="size-3.5" />
                          Delete concept
                        </button>
                      </div>
                    )}
                  </article>
                );
              })}
            </div>
          )}

          </section>}
          {section === "templates" && <AssetLibrary query={assetQuery} category={assetCategory} onQuery={setAssetQuery} onCategory={setAssetCategory}/>}
        </div>
      </div>
      {assetSheet && showLibrary && <div className="hub-sheet-backdrop" onClick={()=>setAssetSheet(false)}><section className="hub-asset-sheet" role="dialog" aria-modal="true" aria-labelledby="asset-sheet-title" onClick={e=>e.stopPropagation()}><header><h2 id="asset-sheet-title">All assets</h2><button autoFocus onClick={()=>setAssetSheet(false)} aria-label="Close asset library"><X size={20}/></button></header><AssetLibrary query={assetQuery} category={assetCategory} onQuery={setAssetQuery} onCategory={setAssetCategory}/></section></div>}
      {folderDialog && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-8"
          role="dialog"
          aria-modal="true"
          aria-labelledby="folder-dialog-title"
        >
          <form
            onSubmit={saveFolder}
            className="w-[420px] rounded-2xl border border-border bg-card p-6 shadow-[var(--shadow-lg)]"
          >
            <div className="flex items-center justify-between gap-4">
              <div>
                <h2
                  id="folder-dialog-title"
                  className="font-semibold text-foreground"
                >
                  {folderDialog.kind === "create"
                    ? "Create folder"
                    : "Rename folder"}
                </h2>
                <p className="mt-1 text-xs text-muted-foreground">
                  Folders are private to your account.
                </p>
              </div>
              <button
                type="button"
                onClick={() => setFolderDialog(null)}
                aria-label="Close folder dialog"
                className="rounded-lg p-1.5 text-muted-foreground hover:bg-surface-hover hover:text-foreground"
              >
                <X className="size-4" />
              </button>
            </div>
            <label className="mt-5 block text-xs font-semibold text-foreground-secondary">
              Folder name
              <input
                autoFocus
                value={folderName}
                onChange={(event) => setFolderName(event.target.value)}
                maxLength={80}
                className="mt-2 h-10 w-full rounded-xl border border-border bg-background px-3 text-sm text-foreground outline-none focus:border-primary"
              />
            </label>
            {folderError && (
              <p className="mt-3 text-xs text-destructive">{folderError}</p>
            )}
            <div className="mt-6 flex items-center justify-between">
              {folderDialog.kind === "rename" ? (
                <button
                  type="button"
                  onClick={() => void deleteFolder(folderDialog.folder)}
                  className="inline-flex items-center gap-1.5 text-xs font-semibold text-destructive hover:underline"
                >
                  <Trash2 className="size-3.5" />
                  Delete folder
                </button>
              ) : (
                <span />
              )}
              <button
                disabled={savingFolder || !folderName.trim()}
                className="rounded-xl bg-primary px-4 py-2.5 text-sm font-semibold text-primary-foreground disabled:cursor-not-allowed disabled:opacity-50"
              >
                {savingFolder
                  ? "Saving…"
                  : folderDialog.kind === "create"
                    ? "Create folder"
                    : "Save name"}
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}

function AssetLibrary({query,category,onQuery,onCategory}:{query:string;category:string;onQuery:(value:string)=>void;onCategory:(value:string)=>void}) {
  const assets = searchAssets(query,category);
  return <div className="hub-asset-library"><div className="hub-asset-controls"><label><Search size={16}/><input aria-label="Search asset library" placeholder="Search assets…" value={query} onChange={e=>onQuery(e.target.value)}/></label><select aria-label="Asset category" value={category} onChange={e=>onCategory(e.target.value)}><option value="all">All categories</option>{ASSET_CATEGORIES.map(item=><option key={item.id} value={item.id}>{item.label}</option>)}</select></div><div className="hub-full-assets">{assets.map(asset=>asset.status === "planned" ? <div key={asset.id} className="hub-planned-asset"><strong>{asset.name}</strong><small>Planned</small></div> : <Link key={asset.id} href={`/projects/new?template=${encodeURIComponent(asset.id)}`}><strong>{asset.name}<ArrowRight size={13}/></strong><small>{ASSET_CATEGORIES.find(c=>c.id===asset.category)?.label} · {asset.maturity.toLowerCase()}</small></Link>)}{!assets.length && <p>No matching assets. Try another search.</p>}</div></div>;
}

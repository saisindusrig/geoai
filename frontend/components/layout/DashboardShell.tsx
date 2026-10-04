"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  ChevronRight,
  Building2,
  Box,
  Download,
  Plus,
  Save,
  Search,
  Settings,
} from "lucide-react";
import { useEffect, useSyncExternalStore } from "react";
import { useRequireAuth } from "@/components/auth/RequireAuth";
import BrandWordmark from "@/components/landing/BrandWordmark";
import { Button } from "@/components/ui/button";
import { CollapsibleSection } from "@/components/ui/collapsible-section";
import DisclaimerBanner from "@/components/DisclaimerBanner";
import PageTransition from "@/components/motion/PageTransition";
import { ProjectHeaderContent } from "@/components/layout/ProjectHeader";
import { useDemoProjectId } from "@/lib/useDemoProjectId";
import {
  ENGINEERING_TOOLS,
  MAIN_NAV,
  PROJECT_NAV,
  projectPageSubtitle,
  SETTINGS_NAV,
} from "@/lib/navigation";
import { cn } from "@/lib/utils";
import { type MapTool, useProjectStore } from "@/stores/projectStore";
import { getAuthToken } from "@/lib/api";
import { loginPath, registrationPath } from "@/lib/auth-routes";
import { LOCAL_SANDBOX_PATH } from "@/lib/local-sandbox";

function NavLink({
  href,
  label,
  icon: Icon,
  active,
  onClick,
}: {
  href: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  active: boolean;
  onClick?: () => void;
}) {
  return (
    <Link
      href={href}
      onClick={onClick}
      className={cn(
        "group flex items-center gap-2.5 rounded-md px-2.5 py-2 text-[13px] font-medium transition-all duration-200 border",
        active
          ? "bg-primary/15 text-foreground border-primary"
          : "text-muted-foreground border-transparent hover:bg-[var(--nav-hover)] hover:text-foreground",
      )}
    >
      <Icon
        className={cn(
          "h-4 w-4 shrink-0",
          active
            ? "text-primary"
            : "text-muted-foreground group-hover:text-foreground",
        )}
      />
      <span className="truncate">{label}</span>
      {active && (
        <ChevronRight className="ml-auto h-3.5 w-3.5 text-primary/70" />
      )}
    </Link>
  );
}

function EngineeringToolButton({
  id,
  label,
  icon: Icon,
  toolHint,
  onClick,
}: {
  id: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  toolHint?: "flyover" | "pipeline" | "building" | "terrain";
  onClick?: () => void;
}) {
  const { activeTool, toolHint: activeHint, activateTool } = useProjectStore();
  const active = activeTool === id && (!toolHint || activeHint === toolHint);

  return (
    <button
      type="button"
      onClick={() => {
        if (toolHint === "terrain") {
          onClick?.();
          return;
        }
        activateTool(id as MapTool, toolHint ?? null);
        onClick?.();
      }}
      className={cn(
        "flex w-full items-center gap-2 rounded-md px-2.5 py-1.5 text-[12px] transition-all duration-200 border",
        active
          ? "bg-primary/15 text-foreground border-primary"
          : "text-muted-foreground border-transparent hover:bg-[var(--nav-hover)] hover:text-foreground",
      )}
    >
      <Icon className="h-3.5 w-3.5 shrink-0" />
      <span className="truncate text-left">{label}</span>
    </button>
  );
}

export function LegacySidebarContent({
  pathname,
  projectId,
  inProject,
  onNavigate,
  isAdmin,
}: {
  pathname: string | null;
  projectId: number | null;
  inProject: boolean;
  onNavigate?: () => void;
  isAdmin: boolean;
}) {
  const demoId = useDemoProjectId();

  return (
    <>
      <div className="flex h-14 shrink-0 items-center gap-2.5 border-b border-border bg-sidebar px-4">
        <div className="min-w-0 flex-1">
          <Link href="/" className="block leading-tight" onClick={onNavigate}>
            <BrandWordmark size="sm" />
          </Link>
          <p className="truncate text-[10px] text-muted-foreground">
            Construction concept studio
          </p>
        </div>
      </div>

      <nav className="flex-1 overflow-y-auto p-3 space-y-4">
        <CollapsibleSection title="Navigation" defaultOpen>
          {MAIN_NAV.map((item) => (
            <NavLink
              key={item.label}
              href={item.href}
              label={item.label}
              icon={item.icon}
              active={
                pathname === item.href ||
                !!(
                  "matchPrefix" in item &&
                  item.matchPrefix &&
                  pathname?.startsWith(item.matchPrefix)
                )
              }
              onClick={onNavigate}
            />
          ))}
        </CollapsibleSection>

        {projectId && (
          <CollapsibleSection title="Project Workflow" defaultOpen>
            {PROJECT_NAV(projectId).map((item) => (
              <NavLink
                key={item.href}
                {...item}
                active={pathname === item.href}
                onClick={onNavigate}
              />
            ))}
          </CollapsibleSection>
        )}

        {inProject && (
          <CollapsibleSection title="Engineering Tools" defaultOpen={false}>
            {ENGINEERING_TOOLS.map((tool, i) => (
              <EngineeringToolButton
                key={`${tool.id}-${i}`}
                id={tool.id}
                label={tool.label}
                icon={tool.icon}
                toolHint={"toolHint" in tool ? tool.toolHint : undefined}
                onClick={
                  "toolHint" in tool && tool.toolHint === "terrain" && projectId
                    ? () => {
                        window.location.href = `/projects/${projectId}/analysis`;
                      }
                    : onNavigate
                }
              />
            ))}
          </CollapsibleSection>
        )}

        <CollapsibleSection title="System" defaultOpen={false}>
          {SETTINGS_NAV.filter((item) => {
            if (item.href.startsWith("/admin") && !isAdmin) return false;
            return true;
          }).map((item) => (
            <NavLink
              key={item.href}
              {...item}
              active={!!pathname?.startsWith(item.href)}
              onClick={onNavigate}
            />
          ))}
          <NavLink
            href={`/projects/${demoId}/workspace`}
            label="Demo Project"
            icon={Building2}
            active={false}
            onClick={onNavigate}
          />
        </CollapsibleSection>
      </nav>

      <div className="border-t border-border p-3 shrink-0">
        <p className="text-center text-[10px] text-muted-foreground leading-relaxed">
          Preliminary planning only
        </p>
      </div>
    </>
  );
}

export default function DashboardShell({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const isLanding = pathname === "/";
  const isLogin = pathname === "/login";
  const isDirectWorkspace = pathname === "/projects/new";
  const isDashboard = pathname === "/dashboard";
  const clientReady = useSyncExternalStore(
    () => () => {},
    () => true,
    () => false,
  );
  useRequireAuth();
  const workspaceFullscreen = useProjectStore((s) => s.workspaceFullscreen);
  const project = useProjectStore((s) => s.project);

  const projectMatch = pathname?.match(/\/projects\/(\d+)/);
  const projectId = projectMatch ? Number(projectMatch[1]) : null;
  const inProject = !!projectId;
  const isDemoWorkspace =
    !!pathname &&
    /^\/projects\/\d+\/workspace$/.test(pathname) &&
    clientReady &&
    new URLSearchParams(window.location.search).get("demo") === "1";
  const isGuestDemo = isDemoWorkspace && !getAuthToken();
  const isLocalSandbox =
    !!pathname &&
    /^\/projects\/\d+\/workspace$/.test(pathname) &&
    clientReady &&
    new URLSearchParams(window.location.search).get("local") === "1";
  const returnPath =
    clientReady && typeof window !== "undefined"
      ? `${pathname ?? "/"}${window.location.search}`
      : pathname ?? "/";

  useEffect(() => {
    if (!inProject) {
      useProjectStore.getState().setProject(null);
    }
  }, [inProject]);

  if (isDirectWorkspace) {
    return <div className="flex h-dvh min-h-0 flex-1 flex-col overflow-hidden bg-background"><PageTransition>{children}</PageTransition></div>;
  }

  if (isLanding || isLogin) {
    return (
      <main
        id="main-content"
        className={cn("flex min-h-screen flex-1 flex-col bg-background", !isLanding && "app-canvas")}
      >
        <PageTransition>{children}</PageTransition>
      </main>
    );
  }

  return (
    <div className="app-canvas flex h-screen min-w-[1280px] overflow-hidden bg-background">
      <div className="flex min-h-0 w-full min-w-0 flex-1 flex-col overflow-hidden">
        {!workspaceFullscreen && !isDashboard && (
          <header className="app-header sticky top-0 z-30 flex min-h-12 items-center gap-3 border-b border-border px-4 py-1.5">
            {project && inProject && (
              <Link href="/" aria-label="GeoAI home" className="mr-1 shrink-0 border-r border-border pr-4">
                <BrandWordmark size="sm" />
              </Link>
            )}
            {project && inProject ? (
              <ProjectHeaderContent
                project={project}
                subtitle={projectPageSubtitle(pathname) ?? undefined}
                compact
                hideSubtitle={pathname?.endsWith("/workspace")}
              />
            ) : (
              <div className="min-w-0">
                <Link href="/" aria-label="GeoAI home"><BrandWordmark size="sm" /></Link>
                <p className="truncate text-[10px] text-muted-foreground">
                  AI-powered, site-aware construction concept visualization
                </p>
              </div>
            )}

            {isDashboard && (
              <label className="relative ml-6 block w-[340px]">
                <Search className="pointer-events-none absolute left-3 top-1/2 size-3.5 -translate-y-1/2 text-muted-foreground" />
                <input
                  type="search"
                  placeholder="Search your concepts"
                  onChange={(event) =>
                    window.dispatchEvent(
                      new CustomEvent("geoai:project-search", {
                        detail: event.target.value,
                      }),
                    )
                  }
                  className="h-8 w-full rounded-lg border border-border bg-card pl-8 pr-3 text-xs text-foreground outline-none transition focus:border-primary"
                  aria-label="Search your concepts"
                />
              </label>
            )}

            <div className="ml-auto flex shrink-0 items-center gap-2">
              {project && pathname?.endsWith("/workspace") && !isLocalSandbox && <Link href={LOCAL_SANDBOX_PATH} className="flex h-8 items-center gap-2 rounded-lg border border-primary/25 bg-primary/[0.06] px-3 text-[11px] font-semibold text-primary transition hover:bg-primary/15"><Box className="size-3.5" />3D Sandbox editor</Link>}
              <Link href="/dashboard" className="mr-2 border-r border-border pr-4 font-mono text-[10px] uppercase tracking-[0.1em] text-muted-foreground hover:text-primary">
                Projects
              </Link>
              {isGuestDemo ? (
                <>
                  <Link href={loginPath(returnPath)}>
                    <Button
                      variant="outline"
                      size="sm"
                      className="h-8 text-xs"
                    >
                      Sign in
                    </Button>
                  </Link>
                  <Link href={registrationPath(returnPath)}>
                    <Button size="sm" variant="default" className="h-8 text-xs">
                      Sign up
                    </Button>
                  </Link>
                </>
              ) : isLocalSandbox ? (
                <>
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    className="h-8 gap-1.5 text-xs"
                    onClick={() =>
                      window.dispatchEvent(
                        new CustomEvent("geoai:save-project"),
                      )
                    }
                  >
                    <Save className="h-3.5 w-3.5" />
                    Save locally
                  </Button>
                  <Link href="/dashboard">
                    <Button size="sm" variant="default" className="h-8 text-xs">
                      Exit sandbox
                    </Button>
                  </Link>
                </>
              ) : (
                <>
                  {project && projectId && (
                    <div className="flex items-center gap-1">
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        className="h-8 gap-1.5 px-2 text-[11px] text-muted-foreground hover:bg-surface-hover hover:text-foreground"
                        title="Save project geometry"
                        onClick={() =>
                          window.dispatchEvent(
                            new CustomEvent("geoai:save-project"),
                          )
                        }
                      >
                        <Save className="h-3.5 w-3.5" />
                        Save
                      </Button>
                      <Link href={`/projects/${projectId}/report`}>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-8 gap-1.5 px-2 text-[11px] text-muted-foreground hover:bg-surface-hover hover:text-foreground"
                        >
                          <Download className="h-3.5 w-3.5" />
                          Export
                        </Button>
                      </Link>
                    </div>
                  )}
                  <Link href="/projects/new">
                    <Button
                      size="sm"
                      variant="default"
                      className="h-8 gap-1.5 text-xs"
                    >
                      <Plus className="h-3.5 w-3.5" />
                      New concept
                    </Button>
                  </Link>
                  <Link
                    href="/settings"
                    aria-label="Open settings"
                    title="Settings"
                    className="grid size-8 place-items-center rounded-lg text-muted-foreground transition hover:bg-surface-hover hover:text-foreground"
                  >
                    <Settings className="size-4" />
                  </Link>
                </>
              )}
            </div>
          </header>
        )}

        <main
          id="main-content"
          className="flex min-h-0 flex-1 flex-col overflow-hidden"
        >
          <PageTransition>{children}</PageTransition>
        </main>

        {!pathname?.includes("/workspace") &&
          !pathname?.includes("/map") &&
          !pathname?.includes("/projects/new") &&
          pathname !== "/dashboard" && (
            <div className="panel border-t border-border px-4 py-2">
              <DisclaimerBanner compact />
            </div>
          )}
      </div>
    </div>
  );
}

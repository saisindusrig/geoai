import {
  BarChart3,
  Box,
  Building2,
  Clock,
  FileText,
  GitCompareArrows,
  Globe,
  LayoutDashboard,
  MapPin,
  Mountain,
  Package,
  Pipette,
  Ruler,
  Settings,
  Sparkles,
  SquareDashed,
  Waypoints,
  Wrench,
} from "lucide-react";

export const MAIN_NAV = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard, matchPrefix: "/dashboard" },
  { href: "/projects/new", label: "New Project", icon: MapPin },
];

export const PROJECT_NAV = (id: number) => [
  { href: `/projects/${id}/workspace`, label: "AI Design Studio", icon: Sparkles },
  { href: `/projects/${id}/map`, label: "GIS Workspace", icon: Globe },
  { href: `/projects/${id}/model`, label: "3D Models", icon: Box },
  { href: `/projects/${id}/estimate`, label: "Material Estimation", icon: Package },
  { href: `/projects/${id}/cost`, label: "Cost Analysis", icon: BarChart3 },
  { href: `/projects/${id}/scenarios`, label: "Compare Scenarios", icon: GitCompareArrows },
  { href: `/projects/${id}/timeline`, label: "Timeline", icon: Clock },
  { href: `/projects/${id}/analysis`, label: "Site Analysis", icon: Mountain },
  { href: `/projects/${id}/report`, label: "Reports", icon: FileText },
];

export const ENGINEERING_TOOLS = [
  { id: "draw-polygon", label: "Draw Boundary", icon: SquareDashed },
  { id: "measure-distance", label: "Measure Distance", icon: Ruler },
  { id: "measure-area", label: "Measure Area", icon: SquareDashed },
  { id: "draw-line", label: "Road Tool", icon: Waypoints },
  { id: "draw-corridor", label: "Flyover Tool", icon: Waypoints, toolHint: "flyover" as const },
  { id: "draw-corridor", label: "Pipeline Tool", icon: Pipette, toolHint: "pipeline" as const },
  { id: "draw-rectangle", label: "Building Tool", icon: Building2, toolHint: "building" as const },
  { id: "select", label: "Terrain Tool", icon: Mountain, toolHint: "terrain" as const },
] as const;

export const SETTINGS_NAV = [
  { href: "/settings", label: "Settings", icon: Settings },
  { href: "/settings/api-keys", label: "Providers", icon: Settings },
  { href: "/admin/rates", label: "Rates", icon: Wrench },
  { href: "/admin/templates", label: "Templates", icon: Settings },
  { href: "/admin/audit", label: "Audit Log", icon: FileText },
  { href: "/admin/usage", label: "Usage Admin", icon: BarChart3 },
];

export const DEMO_PROJECT_ID = 5;

/** Subtitle shown under project name in the shell header for each project route. */
export function projectPageSubtitle(pathname: string | null): string | null {
  if (!pathname) return null;
  const match = pathname.match(/\/projects\/\d+\/([^/?#]+)/);
  if (!match) return null;
  const segment = match[1];
  const labels: Record<string, string> = {
    workspace: "AI Design Studio",
    map: "Site Selection · GIS Workspace",
    model: "3D Model Viewer · BIM Inspection",
    estimate: "Material Estimation · BOQ",
    cost: "Cost Analysis",
    scenarios: "Scenario Comparison",
    timeline: "Construction Timeline",
    analysis: "Site Analysis",
    report: "Reports & Export Center",
  };
  return labels[segment] ?? null;
}

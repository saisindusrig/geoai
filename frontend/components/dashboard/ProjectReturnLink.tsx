"use client";

import Link from "next/link";
import { useSyncExternalStore } from "react";
import { projectReturnPath } from "@/lib/workspace-device";
import type { Project } from "@/lib/types";

const subscribe = (notify: () => void) => { window.addEventListener("popstate", notify); return () => window.removeEventListener("popstate", notify); };
export default function ProjectReturnLink({ projects }: { projects: Project[] | null }) {
  const search = useSyncExternalStore(subscribe, () => window.location.search, () => "");
  const path = projectReturnPath(search);
  if (!path) return null;
  const id = Number(path.match(/^\/projects\/(\d+)/)?.[1]);
  const project = projects?.find(item => item.id === id);
  return <p className="hub-project-return border-l-2 border-primary pl-3 text-sm leading-6"><Link className="text-primary underline underline-offset-4" href={path}>Return to {project?.name ?? `Project #${id}`}</Link><span className="block text-muted-foreground">Advanced editing is available on desktop.</span></p>;
}

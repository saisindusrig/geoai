"use client";

import Link from "next/link";
import { ArrowUpRight, Key, Server, Settings, Wrench } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import SystemStatusPanel from "@/components/settings/SystemStatusPanel";
import AuthStatusCard from "@/components/settings/AuthStatusCard";
import UsageCard from "@/components/settings/UsageCard";
import { useAuthUser } from "@/lib/useAuthUser";

type SectionLink = {
  href: string;
  icon: LucideIcon;
  title: string;
  description: string;
  admin?: boolean;
};

const BASE_SECTIONS: SectionLink[] = [
  {
    href: "/settings/api-keys",
    icon: Key,
    title: "Provider Status",
    description: "View which map and AI providers are active (configured server-side).",
  },
];

const ADMIN_SECTIONS: SectionLink[] = [
  {
    href: "/admin/rates",
    icon: Wrench,
    title: "Rate Library",
    description: "Edit regional material and labor rates used in cost estimates.",
    admin: true,
  },
  {
    href: "/admin/templates",
    icon: Settings,
    title: "Project Templates",
    description: "Manage default parameters for flyover, building, road, and pipeline types.",
    admin: true,
  },
];

function SectionHeading({ icon: Icon, children }: { icon: LucideIcon; children: React.ReactNode }) {
  return (
    <div className="flex items-center gap-2 text-sm font-semibold text-foreground">
      <Icon className="h-4 w-4 text-primary" />
      {children}
    </div>
  );
}

export default function SettingsPageClient() {
  const { isAdmin, loading } = useAuthUser();
  const sections: SectionLink[] = loading || isAdmin ? [...BASE_SECTIONS, ...ADMIN_SECTIONS] : BASE_SECTIONS;

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="max-w-4xl mx-auto px-6 py-8 space-y-8">
        <div>
          <p className="font-mono text-[10px] uppercase tracking-[0.16em] text-primary">GeoAI / system</p>
          <h1 className="mt-3 border-b border-border pb-5 text-[36px] font-medium tracking-[-0.045em]">Settings</h1>
          <p className="mt-2 text-sm text-muted-foreground">
            Account, usage limits, infrastructure status, and provider configuration
          </p>
        </div>

        <div className="grid items-stretch gap-4 lg:grid-cols-2">
          <AuthStatusCard />
          <UsageCard />
        </div>

        <div className="space-y-2">
          <SectionHeading icon={Server}>Infrastructure status</SectionHeading>
          <SystemStatusPanel />
        </div>

        <div className="space-y-3">
          <SectionHeading icon={Settings}>Configuration</SectionHeading>
          <div className="grid gap-4 sm:grid-cols-2">
            {sections.map(({ href, icon: Icon, title, description, admin }) => (
              <Link key={href} href={href} className="group">
                <Card float className="h-full cursor-pointer hover:border-primary/40">
                  <CardHeader className="flex-row items-start gap-3 space-y-0">
                    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-md bg-primary/15">
                      <Icon className="h-5 w-5 text-primary" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <CardTitle>{title}</CardTitle>
                        {admin && <Badge variant="primary">Admin</Badge>}
                      </div>
                      <CardDescription>{description}</CardDescription>
                    </div>
                    <ArrowUpRight className="h-4 w-4 shrink-0 text-muted-foreground transition-transform group-hover:-translate-y-0.5 group-hover:translate-x-0.5 group-hover:text-primary" />
                  </CardHeader>
                </Card>
              </Link>
            ))}
          </div>
        </div>

        {!loading && !isAdmin && (
          <p className="text-xs text-muted-foreground">
            Rate library and template management are restricted to admin accounts.
          </p>
        )}
      </div>
    </div>
  );
}

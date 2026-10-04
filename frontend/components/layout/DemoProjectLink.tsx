"use client";

import Link from "next/link";
import { ArrowRight, Play } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useDemoProjectId } from "@/lib/useDemoProjectId";

export function DemoProjectLink({ variant = "button" }: { variant?: "button" | "text" }) {
  const demoId = useDemoProjectId();

  if (variant === "text") {
    return (
      <Link href={`/projects/${demoId}/workspace`} className="text-primary hover:underline">
        View Demo
      </Link>
    );
  }

  return (
    <Link href={`/projects/${demoId}/workspace`}>
      <Button size="lg" variant="outline" className="gap-2 h-11 px-8">
        <Play className="h-4 w-4" />
        View Demo Project
        <ArrowRight className="h-4 w-4" />
      </Button>
    </Link>
  );
}

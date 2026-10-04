"use client";

import Link from "next/link";
import { GitCompareArrows } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { DesignScenario } from "@/lib/types";
import { cn } from "@/lib/utils";

interface Props {
  projectId: number;
  scenarios: DesignScenario[];
  selectedId: number | null;
  onSelect: (scenario: DesignScenario) => void;
  compact?: boolean;
}

export default function ScenarioSelector({
  projectId,
  scenarios,
  selectedId,
  onSelect,
  compact,
}: Props) {
  if (!scenarios.length) {
    return (
      <p className="text-xs text-muted-foreground px-1">No design scenarios yet — generate one in AI Studio.</p>
    );
  }

  return (
    <div className={cn("space-y-2", compact && "space-y-1")}>
      <div className="flex items-center justify-between gap-2 px-1">
        <span className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
          Design Scenario
        </span>
        {scenarios.length > 1 && (
          <Link href={`/projects/${projectId}/scenarios`}>
            <Button variant="ghost" size="sm" className="h-6 gap-1 text-[10px] px-2">
              <GitCompareArrows className="h-3 w-3" />
              Compare
            </Button>
          </Link>
        )}
      </div>
      <select
        title="Select a design scenario"
        value={selectedId ?? ""}
        onChange={(e) => {
          const s = scenarios.find((sc) => sc.id === Number(e.target.value));
          if (s) onSelect(s);
        }}
        className="w-full rounded-md border border-border bg-background px-2 py-1.5 text-xs text-foreground focus:border-primary focus:shadow-[var(--shadow-focus)] focus:outline-none"
      >
        {scenarios.map((s) => (
          <option key={s.id} value={s.id}>
            {s.name} — {s.status}
          </option>
        ))}
      </select>
      {selectedId && (
        <div className="flex flex-wrap gap-1 px-1">
          {scenarios
            .filter((s) => s.id === selectedId)
            .map((s) => (
              <Badge
                key={s.id}
                variant={s.status === "completed" ? "success" : "warning"}
                className="text-[10px]"
              >
                {s.status}
              </Badge>
            ))}
        </div>
      )}
    </div>
  );
}

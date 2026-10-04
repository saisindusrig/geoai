"use client";

import { useCallback, useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";
import { toastPromise } from "@/lib/toast";
import { useAuthUser } from "@/lib/useAuthUser";
import type { ProjectTemplate } from "@/lib/types";

export default function TemplatesPage() {
  const { isAdmin, loading: authLoading } = useAuthUser();
  const [templates, setTemplates] = useState<ProjectTemplate[]>([]);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [draftJson, setDraftJson] = useState("");
  const [error, setError] = useState("");

  const load = useCallback(
    () =>
      api
        .get<ProjectTemplate[]>("/api/admin/templates")
        .then(setTemplates)
        .catch((e) => setError(String(e.message ?? e))),
    [],
  );
  useEffect(() => {
    load();
  }, [load]);

  const startEdit = (t: ProjectTemplate) => {
    setEditingId(t.id);
    setDraftJson(JSON.stringify(t.default_parameters_json, null, 2));
    setError("");
  };

  const save = async (t: ProjectTemplate) => {
    try {
      const parsed = JSON.parse(draftJson);
      await toastPromise(
        api.put(`/api/admin/templates/${t.id}`, {
          project_type: t.project_type,
          name: t.name,
          default_parameters_json: parsed,
        }),
        { loading: "Saving template…", success: "Template saved" },
      );
      setEditingId(null);
      load();
    } catch (e) {
      setError(e instanceof SyntaxError ? "Invalid JSON" : String(e));
    }
  };

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="max-w-4xl mx-auto w-full px-6 py-8 space-y-5">
        <div>
          <p className="font-mono text-[10px] uppercase tracking-[0.16em] text-primary">GeoAI / administration</p>
          <h1 className="mt-3 border-b border-border pb-5 text-[36px] font-medium tracking-[-0.045em]">Project Templates</h1>
          <p className="mt-2 text-sm text-muted-foreground">
            Default parameters applied when creating a new design for each project type.
            {!isAdmin && !authLoading ? " Read-only view." : ""}
          </p>
        </div>
        {!authLoading && !isAdmin && (
          <p className="text-xs text-amber-600/90">Admin access is required to edit templates.</p>
        )}
        {error && <p className="text-sm text-destructive">{error}</p>}

        <div className="grid gap-3">
          {templates.map((t) => (
            <Card key={t.id} float>
              <CardHeader className="flex-row items-center gap-2 space-y-0 pb-2">
                <Badge variant="accent">{t.project_type}</Badge>
                <CardTitle className="text-sm flex-1">{t.name}</CardTitle>
                {isAdmin && (
                <Button
                  size="sm"
                  variant="secondary"
                  className="h-7 text-xs"
                  onClick={() => (editingId === t.id ? save(t) : startEdit(t))}
                >
                  {editingId === t.id ? "Save" : "Edit JSON"}
                </Button>
                )}
              </CardHeader>
              <CardContent>
                {editingId === t.id ? (
                  <textarea
                    aria-label="Template JSON"
                    placeholder="Template JSON" 
                    value={draftJson}
                    onChange={(e) => setDraftJson(e.target.value)}
                    rows={10}
                    className="w-full rounded-md border border-border bg-background p-2 font-data text-xs focus:border-primary focus:shadow-[var(--shadow-focus)] focus:outline-none"
                  />
                ) : (
                  <pre className="text-xs bg-muted/30 rounded-md p-3 overflow-x-auto font-data">
                    {JSON.stringify(t.default_parameters_json, null, 2)}
                  </pre>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
}

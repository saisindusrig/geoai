"use client";

import { useRef, useState } from "react";
import { Input } from "@/components/ui/input";
import { api, apiUrl } from "@/lib/api";
import { useProjectStore } from "@/stores/projectStore";

interface ChatEntry {
  role: "user" | "assistant";
  text: string;
}

interface AssistantAction {
  type: "update_parameters" | "regenerate" | "show_layer" | "download";
  parameters?: Record<string, unknown>;
  layer?: string;
  export?: string;
}

interface AssistantPanelProps {
  projectId: number;
  onApplyParameters: (params: Record<string, unknown>) => void;
  onRegenerate: (params: Record<string, unknown>) => void;
}

export default function AssistantPanel({
  projectId,
  onApplyParameters,
  onRegenerate,
}: AssistantPanelProps) {
  const [history, setHistory] = useState<ChatEntry[]>([
    {
      role: "assistant",
      text: "I can adjust the design. Try: 'make this 4 lanes', 'change pier spacing to 35', 'reduce cost', 'show excavation', or 'generate report'.",
    },
  ]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const toggleLayer = useProjectStore((s) => s.toggleLayer);
  const layers = useProjectStore((s) => s.layers);

  const send = async () => {
    const message = input.trim();
    if (!message || busy) return;
    setInput("");
    setHistory((h) => [...h, { role: "user", text: message }]);
    setBusy(true);
    try {
      const res = await api.post<{ reply: string; action: AssistantAction | null }>(
        `/api/projects/${projectId}/ai/chat`,
        { message },
      );
      setHistory((h) => [...h, { role: "assistant", text: res.reply }]);
      const action = res.action;
      if (action?.type === "update_parameters" && action.parameters) {
        onApplyParameters(action.parameters);
      } else if (action?.type === "regenerate") {
        onRegenerate(action.parameters ?? {});
      } else if (action?.type === "show_layer" && action.layer === "excavation" && !layers.excavation) {
        toggleLayer("excavation");
      } else if (action?.type === "download" && action.export) {
        window.open(apiUrl(`/api/projects/${projectId}/exports/${action.export}`), "_blank");
      }
    } catch (e) {
      setHistory((h) => [...h, { role: "assistant", text: `Error: ${e instanceof Error ? e.message : e}` }]);
    } finally {
      setBusy(false);
      setTimeout(() => scrollRef.current?.scrollTo({ top: 99999, behavior: "smooth" }), 50);
    }
  };

  return (
    <div className="flex flex-col h-full">
      <div ref={scrollRef} className="flex-1 overflow-y-auto space-y-2 pr-1">
        {history.map((entry, i) => (
          <div
            key={i}
            className={`text-xs px-3 py-2 max-w-[95%] ${
              entry.role === "user"
                ? "bg-primary text-primary-foreground ml-auto border border-primary/50"
                : "bg-muted border border-border"
            }`}
          >
            {entry.text}
          </div>
        ))}
      </div>
      <div className="flex gap-2 pt-2">
        <Input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && send()}
          placeholder="Ask the assistant…"
          className="flex-1 h-8 text-xs"
        />
        <button
          onClick={send}
          disabled={busy}
          className="px-3 py-1.5 bg-primary text-primary-foreground text-xs disabled:opacity-50"
        >
          Send
        </button>
      </div>
    </div>
  );
}

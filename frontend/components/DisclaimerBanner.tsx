import { AlertTriangle } from "lucide-react";
import { cn } from "@/lib/utils";

const MESSAGE =
  "Preliminary planning only. Final construction drawings and quantities must be verified by licensed engineers and survey data.";

export default function DisclaimerBanner({
  compact = false,
  className,
}: {
  compact?: boolean;
  className?: string;
}) {
  if (compact) {
    return (
      <div
        className={cn(
          "flex gap-2.5 rounded-lg border border-[rgba(245,158,11,0.25)] bg-[rgba(245,158,11,0.06)] px-3 py-2.5",
          className,
        )}
        role="note"
      >
        <AlertTriangle className="h-4 w-4 shrink-0 text-[#F59E0B] mt-0.5" strokeWidth={1.75} />
        <p className="text-[12px] leading-snug text-muted-foreground">{MESSAGE}</p>
      </div>
    );
  }

  return (
    <div
      className={cn(
        "flex gap-3 rounded-xl border border-[rgba(245,158,11,0.2)] bg-[rgba(245,158,11,0.05)] px-5 py-4",
        className,
      )}
      role="note"
    >
      <AlertTriangle className="h-5 w-5 shrink-0 text-[#F59E0B]" strokeWidth={1.75} />
      <p className="text-sm leading-relaxed text-foreground-secondary">{MESSAGE}</p>
    </div>
  );
}

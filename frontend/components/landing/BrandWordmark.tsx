import { cn } from "@/lib/utils";

const sizeClasses = {
  sm: "text-sm",
  md: "text-[17px]",
  nav: "text-[22px]",
  lg: "text-xl sm:text-2xl",
} as const;

export default function BrandWordmark({
  className,
  size = "md",
}: {
  className?: string;
  size?: keyof typeof sizeClasses;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-2 leading-none tracking-[-0.04em] text-foreground",
        sizeClasses[size],
        className,
      )}
      aria-label="GeoAI"
    >
      <svg width="27" height="29" viewBox="0 0 27 29" fill="none" className="h-[1.15em] w-[1.1em] text-foreground-secondary" aria-hidden="true"><path d="M2 23 13.5 3 25 23H2Z M8 23l5.5-10L19 23 M2 23l11.5 4L25 23" stroke="currentColor" strokeWidth="1.3" /></svg>
      <span className="font-medium">GeoAI</span>
      <span className="-ml-1 mt-1 size-1 self-start rounded-full bg-primary" aria-hidden="true" />
    </span>
  );
}

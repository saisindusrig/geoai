import { cn } from "@/lib/utils";

export function Input({
  className,
  ...props
}: React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      className={cn(
        "flex h-9 w-full rounded-none border border-border bg-background px-3 py-2 text-sm text-foreground",
        "placeholder:text-muted-foreground",
        "focus:outline-none focus:border-primary focus:shadow-[var(--shadow-focus)]",
        "transition-all duration-150",
        className,
      )}
      {...props}
    />
  );
}

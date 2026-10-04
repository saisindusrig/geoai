import { cn } from "@/lib/utils";

export const selectClassName =
  "flex h-9 w-full rounded-none border border-border bg-background px-3 py-2 text-sm text-foreground focus:outline-none focus:border-primary focus:shadow-[var(--shadow-focus)] transition-all duration-150";

export function Select({
  className,
  children,
  ...props
}: React.SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <select className={cn(selectClassName, className)} {...props}>
      {children}
    </select>
  );
}

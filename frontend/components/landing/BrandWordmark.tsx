import BrandLogo from "@/components/brand/BrandLogo";
import { cn } from "@/lib/utils";
const sizes = { sm: "h-9 w-auto", md: "h-10 w-auto", nav: "h-10 w-auto sm:h-12", lg: "h-14 w-auto" } as const;
export default function BrandWordmark({ className, size = "md" }: { className?: string; size?: keyof typeof sizes }) {
 return <span className={cn("inline-flex shrink-0 items-center", className)}>
  <BrandLogo variant="simplified" className={cn(sizes[size], "sm:hidden")} />
  <BrandLogo variant="secondary" className={cn(sizes[size], "hidden sm:block")} />
 </span>;
}

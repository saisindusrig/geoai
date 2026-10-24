import BrandLogo from "@/components/brand/BrandLogo";
export default function AppLoading() {
 return <div role="status" className="flex min-h-[40vh] flex-1 flex-col items-center justify-center gap-4 p-8">
  <BrandLogo variant="animated" className="h-16 w-auto" decorative />
  <p className="text-sm text-muted-foreground">Loading StruvoCivil…</p>
 </div>;
}

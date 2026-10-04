export default function AppLoading() {
  return (
    <div className="flex flex-1 flex-col items-center justify-center gap-4 p-8 min-h-[40vh]">
      <div className="h-10 w-10 rounded-full border-2 border-primary border-t-transparent animate-spin" />
      <p className="text-sm text-muted-foreground">Loading…</p>
    </div>
  );
}

import { Suspense } from "react";
import LoginPageInner from "./LoginPageInner";

export default function LoginPage() {
  return (
    <Suspense fallback={<div className="flex flex-1 items-center justify-center p-6 text-sm text-muted-foreground">Loading…</div>}>
      <LoginPageInner />
    </Suspense>
  );
}

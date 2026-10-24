"use client";

import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { authRequired, getAuthToken } from "@/lib/api";
import { loginPath, PUBLIC_APP_PATHS } from "@/lib/auth-routes";
import { firebaseMode, firebaseSignedIn } from "@/lib/firebase-auth";

/** Redirect unauthenticated users to /login in production JWT mode. */
export function useRequireAuth() {
  const pathname = usePathname();
  const router = useRouter();

  useEffect(() => {
    if (!authRequired() || !pathname) return;
    if (PUBLIC_APP_PATHS.has(pathname)) return;
    const isPublicDemoWorkspace =
      /^\/projects\/\d+\/workspace$/.test(pathname) &&
      new URLSearchParams(window.location.search).get("demo") === "1";
    const isLocalSandboxWorkspace =
      /^\/projects\/\d+\/workspace$/.test(pathname) &&
      new URLSearchParams(window.location.search).get("local") === "1";
    if (!firebaseMode() && (isPublicDemoWorkspace || isLocalSandboxWorkspace)) return;
    if (getAuthToken() || firebaseSignedIn()) return;
    router.replace(loginPath(pathname));
  }, [pathname, router]);
}

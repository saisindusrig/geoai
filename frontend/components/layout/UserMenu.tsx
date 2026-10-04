"use client";

import Link from "next/link";
import { LogIn, LogOut, Settings, User } from "lucide-react";
import { Button } from "@/components/ui/button";
import { loginPath } from "@/lib/auth-routes";
import { authRequired, clearAuthToken, getAuthToken } from "@/lib/api";
import { useAuthUser } from "@/lib/useAuthUser";

export default function UserMenu({ pathname }: { pathname: string | null }) {
  const { user, loading } = useAuthUser();

  function logout() {
    clearAuthToken();
    window.location.href = authRequired() ? loginPath(pathname ?? "/dashboard") : "/dashboard";
  }

  if (loading) {
    return <div className="h-8 w-20 rounded-md bg-muted/40 animate-pulse" aria-hidden />;
  }

  if (!user || (authRequired() && !getAuthToken())) {
    return (
      <Link href={loginPath(pathname ?? "/dashboard")}>
        <Button variant="outline" size="sm" className="h-8 gap-1.5 text-xs">
          <LogIn className="h-3.5 w-3.5" />
          <span className="hidden sm:inline">Sign in</span>
        </Button>
      </Link>
    );
  }

  return (
    <div className="flex items-center gap-1.5">
      <Link href="/settings">
        <Button variant="ghost" size="sm" className="h-8 gap-1.5 px-2 text-xs max-w-[140px]">
          <User className="h-3.5 w-3.5 shrink-0" />
          <span className="truncate hidden sm:inline">{user.name}</span>
        </Button>
      </Link>
      <Button variant="ghost" size="icon" className="h-8 w-8" onClick={logout} title="Sign out">
        <LogOut className="h-3.5 w-3.5" />
      </Button>
      <Link href="/settings" className="hidden md:inline-flex">
        <Button variant="ghost" size="icon" className="h-8 w-8" title="Settings">
          <Settings className="h-3.5 w-3.5" />
        </Button>
      </Link>
    </div>
  );
}

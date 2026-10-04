"use client";

import Link from "next/link";
import { LogIn, LogOut, User } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { authRequired, clearAuthToken } from "@/lib/api";
import { useAuthUser } from "@/lib/useAuthUser";

export default function AuthStatusCard() {
  const { user, loading, reload } = useAuthUser();

  function logout() {
    clearAuthToken();
    if (authRequired()) {
      window.location.href = "/login";
    } else {
      reload();
    }
  }

  const initials = user
    ? user.name
        .split(/\s+/)
        .filter(Boolean)
        .map((w) => w[0])
        .join("")
        .slice(0, 2)
        .toUpperCase()
    : "";

  return (
    <Card float className="h-full">
      <CardHeader className="flex-row items-center gap-3 space-y-0">
        <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full border border-primary/25 bg-primary/10 text-sm font-semibold text-primary">
          {initials || <User className="h-5 w-5" />}
        </div>
        <div className="min-w-0 flex-1">
          <CardTitle className="truncate">{user ? user.name : "Account"}</CardTitle>
          <CardDescription className="truncate">
            {loading
              ? "Checking session…"
              : user
                ? user.email
                : authRequired()
                  ? "Not signed in"
                  : "Dev mode — mock user"}
          </CardDescription>
        </div>
        {user?.role === "admin" && <Badge variant="primary">Admin</Badge>}
      </CardHeader>
      <CardContent className="flex items-center justify-between border-t border-border pt-4">
        <span className="text-xs text-muted-foreground">
          {loading
            ? "\u00A0"
            : user
              ? `Signed in as ${user.role}`
              : "Sign in to sync projects and settings"}
        </span>
        {user ? (
          <Button type="button" variant="outline" size="sm" onClick={logout}>
            <LogOut className="h-4 w-4 mr-1" />
            Sign out
          </Button>
        ) : (
          <Link
            href="/login"
            className="inline-flex items-center rounded-md border border-input bg-background px-3 py-1.5 text-sm font-medium hover:bg-accent"
          >
            <LogIn className="h-4 w-4 mr-1" />
            Sign in
          </Link>
        )}
      </CardContent>
    </Card>
  );
}

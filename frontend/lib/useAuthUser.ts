"use client";

import { useCallback, useEffect, useState } from "react";
import { api, authRequired, getAuthToken } from "@/lib/api";

export type AuthUser = {
  id: number;
  name: string;
  email: string;
  role: "user" | "admin";
};

const DEV_MOCK_USER: AuthUser = {
  id: 1,
  name: "Dev user",
  email: "dev@example.com (mock)",
  role: "admin",
};

function fetchAuthUser(): Promise<AuthUser | null> {
  const token = getAuthToken();
  if (!token && authRequired()) {
    return Promise.resolve(null);
  }
  if (!token) {
    return Promise.resolve(DEV_MOCK_USER);
  }
  return api.get<AuthUser>("/api/auth/me").catch(() => null);
}

export function useAuthUser() {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);
  const [reloadNonce, setReloadNonce] = useState(0);

  useEffect(() => {
    let cancelled = false;

    fetchAuthUser()
      .then((nextUser) => {
        if (!cancelled) setUser(nextUser);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [reloadNonce]);

  const reload = useCallback(() => {
    setLoading(true);
    setReloadNonce((n) => n + 1);
  }, []);

  return {
    user,
    loading,
    isAdmin: user?.role === "admin",
    reload,
  };
}

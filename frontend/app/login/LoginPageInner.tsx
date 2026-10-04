"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { FormEvent, useState } from "react";
import { motion } from "framer-motion";
import { ArrowRight, ArrowUpRight, Eye, EyeOff } from "lucide-react";
import { Button } from "@/components/ui/button";
import { FormField } from "@/components/ui/form-field";
import BrandWordmark from "@/components/landing/BrandWordmark";
import { api, authRequired, formatApiErrorMessage, setAuthToken } from "@/lib/api";
import { toast } from "@/lib/toast";

type AuthResponse = {
  access_token: string;
};

export default function LoginPageInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const nextPath = searchParams.get("next") || "/dashboard";
  const [mode, setMode] = useState<"login" | "register">(
    searchParams.get("mode") === "register" ? "register" : "login",
  );
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const formErrorId = "login-form-error";

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const path = mode === "login" ? "/api/auth/login" : "/api/auth/register";
      const body =
        mode === "login"
          ? { email, password }
          : { name: name.trim() || email.split("@")[0], email, password };
      const res = await api.post<AuthResponse>(path, body);
      setAuthToken(res.access_token);
      toast(mode === "login" ? "Signed in successfully" : "Account created successfully", { variant: "success" });
      router.replace(nextPath);
    } catch (err) {
      setError(formatApiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="auth-page">
      <header className="auth-header">
        <Link href="/" aria-label="GeoAI home"><BrandWordmark size="lg" /></Link>
        <Link href="/">Back to platform <ArrowUpRight size={15} /></Link>
      </header>
      <div className="auth-layout">
        <section className="auth-intro">
          <p className="auth-eyebrow"><span>01</span> / YOUR ENGINEERING WORKSPACE</p>
          <h2>Real terrain.<br />Considered<br /><em>infrastructure.</em></h2>
          <p className="auth-description">From the first site decision to your next design iteration. Bring your project into perspective.</p>
          <div className="auth-terrain" aria-hidden="true">
            <svg viewBox="0 0 600 220" fill="none">
              {Array.from({ length: 9 }, (_, i) => <path key={i} d={`M-20 ${80+i*19} C100 ${-80+i*24} 220 ${230+i*5} 350 ${90+i*12} S520 ${-10+i*22} 640 ${55+i*17}`} stroke="currentColor" />)}
              <path d="M0 168C150 60 270 190 380 107S530 90 600 34" stroke="#c8ff32" strokeWidth="2" />
              <circle cx="380" cy="107" r="5" fill="#c8ff32" />
            </svg>
            <span>CONTEXT → CONCEPT → ENGINEERING REVIEW</span>
          </div>
        </section>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.55 }}
          className="auth-form-panel"
        >
          <div className="mb-7">
            <p className="auth-eyebrow"><span>02</span> / {mode === "login" ? "WELCOME BACK" : "GET STARTED"}</p>
            <div className="flex items-start justify-between gap-4">
              <div>
                <h1 className="auth-title">
              {mode === "login" ? "Sign in" : "Create account"}
                </h1>
              </div>
            </div>
            <p className="mt-3 text-sm leading-relaxed text-muted-foreground">
              {mode === "register"
                ? "Create your workspace and start exploring site-aware infrastructure concepts."
                : authRequired()
                  ? "Sign in to access your projects and workspace."
                  : "Sign in to return to your saved workspaces."}
            </p>
          </div>

          <form
            onSubmit={onSubmit}
            className="space-y-5"
            aria-describedby={error ? formErrorId : undefined}
          >
            {mode === "register" && (
              <FormField label="Name" htmlFor="name">
                <input
                  id="name"
                    className="auth-glass-input w-full rounded-lg border px-4 py-3 text-base"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  autoComplete="name"
                />
              </FormField>
            )}
            <FormField label="Email" htmlFor="email">
              <input
                id="email"
                type="email"
                required
                    className="auth-glass-input w-full rounded-lg border px-4 py-3 text-base"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoComplete="email"
              />
            </FormField>
            <FormField label="Password" htmlFor="password" hint="Minimum 8 characters">
              <div className="relative"><input id="password" type={showPassword ? "text" : "password"} required minLength={8} className="auth-glass-input w-full rounded-lg border px-4 py-3 pr-12 text-base" value={password} onChange={(e) => setPassword(e.target.value)} autoComplete={mode === "login" ? "current-password" : "new-password"}/><button type="button" onClick={() => setShowPassword((value) => !value)} className="absolute right-2 top-1/2 -translate-y-1/2 p-2 text-muted-foreground hover:text-foreground" aria-label={showPassword ? "Hide password" : "Show password"} title={showPassword ? "Hide password" : "Show password"}>{showPassword ? <EyeOff className="size-4" /> : <Eye className="size-4" />}</button></div>
            </FormField>
            {error && (
              <div
                id={formErrorId}
                role="alert"
                className="rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-3 text-base text-destructive"
              >
                {error}
              </div>
            )}
            <Button type="submit" size="lg" className="h-12 w-full text-base" disabled={loading}>
              {loading ? "Please wait…" : mode === "login" ? "Sign in" : "Register"}
              {!loading && <ArrowRight className="size-4" aria-hidden="true" />}
            </Button>
          </form>

          <p className="mt-5 text-center text-base text-muted-foreground">
            {mode === "login" ? (
              <>
                No account?{" "}
                <button
                  type="button"
                  className="font-medium text-primary underline-offset-2 hover:underline"
                  onClick={() => { setMode("register"); setError(null); }}
                >
                  Register
                </button>
              </>
            ) : (
              <>
                Already registered?{" "}
                <button
                  type="button"
                  className="font-medium text-primary underline-offset-2 hover:underline"
                  onClick={() => { setMode("login"); setError(null); }}
                >
                  Sign in
                </button>
              </>
            )}
          </p>
          {!authRequired() && (
            <p className="mt-3 text-center text-sm text-muted-foreground">
              <Link href="/dashboard" className="hover:text-foreground">
                Continue to dashboard
              </Link>
            </p>
          )}
        </motion.div>
      </div>
      <footer className="auth-footer"><span>SPATIAL INTELLIGENCE, ENGINEERED.</span><Link href="/privacy">Privacy & data use <ArrowUpRight size={12} /></Link></footer>
    </div>
  );
}

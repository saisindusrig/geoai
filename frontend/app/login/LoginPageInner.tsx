"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";
import { motion } from "framer-motion";
import { ArrowRight, ArrowUpRight, Eye, EyeOff } from "lucide-react";
import { Button } from "@/components/ui/button";
import { FormField } from "@/components/ui/form-field";
import BrandWordmark from "@/components/landing/BrandWordmark";
import { api, authRequired, formatApiErrorMessage, setAuthToken } from "@/lib/api";
import { toast } from "@/lib/toast";
import { safeAuthReturnPath } from "@/lib/auth-routes";
import { assertSession, browserFirebaseConfiguration, firebaseGoogleSignIn, firebaseGoogleSignInAllowed, firebasePasswordSignInAllowed, firebaseRecoverPassword, firebaseSignIn, firebaseSignInAllowed, firebaseSignOut, isAuthConfiguration, passwordSignInAllowed, sessionRevision, signInPreparation, type AuthConfiguration } from "@/lib/firebase-auth";

type AuthResponse = {
  access_token: string;
};

async function fetchConfiguration(): Promise<AuthConfiguration> {
  const value = await api.get<unknown>("/api/auth/config");
  if (!isAuthConfiguration(value)) throw new Error("Invalid authentication configuration");
  return value;
}

export default function LoginPageInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const nextPath = safeAuthReturnPath(searchParams.get("next"));
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
  const [configuration, setConfiguration] = useState<AuthConfiguration | null>(null);
  const [configurationError, setConfigurationError] = useState(false);
  const loadConfiguration = async () => {
    try {
      const value = await fetchConfiguration();
      setConfigurationError(false);
      setConfiguration(value);
    }
    catch { setConfiguration(null); setConfigurationError(true); }
  };
  useEffect(() => {
    let active = true;
    void fetchConfiguration().then(value => {
      if (active) { setConfiguration(value); setConfigurationError(false); }
    }).catch(() => { if (active) setConfigurationError(true); });
    return () => { active = false; };
  }, []);
  const passwordAllowed = passwordSignInAllowed(configuration);
  const firebaseAllowed = firebaseSignInAllowed(configuration);
  const googleAllowed = firebaseGoogleSignInAllowed(configuration);
  const firebasePasswordAllowed = firebasePasswordSignInAllowed(configuration);
  const registrationAllowed = configuration?.registration_allowed !== false;
  const effectiveMode = registrationAllowed && !firebaseAllowed ? mode : "login";

  async function signInFirebase(provider: "google" | "password") {
    setError(null); setLoading(true);
    let backendCheck = false;
    let expected: number | undefined;
    try {
      if (provider === "google") await firebaseGoogleSignIn();
      else await firebaseSignIn(email, password);
      backendCheck = true;
      expected = sessionRevision();
      await api.get("/api/auth/me");
      assertSession(expected);
      router.replace(nextPath);
    } catch (err) {
      if (expected !== undefined && expected === sessionRevision()) {
        try { await firebaseSignOut(); } catch { /* Local authority is already cleared. */ }
      }
      const status = err && typeof err === "object" && "status" in err ? err.status : undefined;
      setError(backendCheck
        ? status === 403 ? "Access denied. This Firebase account is not approved for StruvoCivil. Contact your administrator."
          : "Workspace access could not be verified. Sign in again or contact your administrator."
        : err instanceof Error ? err.message : "Sign-in unavailable. Try again later.");
    } finally { setLoading(false); }
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!passwordAllowed && !firebasePasswordAllowed) return;
    if (firebasePasswordAllowed) { await signInFirebase("password"); return; }
    setError(null);
    setLoading(true);
    try {
      const path = effectiveMode === "login" ? "/api/auth/login" : "/api/auth/register";
      const body =
        effectiveMode === "login"
          ? { email, password }
          : { name: name.trim() || email.split("@")[0], email, password };
      const res = await api.post<AuthResponse>(path, body);
      setAuthToken(res.access_token);
      toast(effectiveMode === "login" ? "Signed in successfully" : "Account created successfully", { variant: "success" });
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
        <Link href="/" aria-label="StruvoCivil home"><BrandWordmark size="lg" /></Link>
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
              <path d="M0 168C150 60 270 190 380 107S530 90 600 34" stroke="#b7c3aa" strokeWidth="2" />
              <circle cx="380" cy="107" r="5" fill="#b7c3aa" />
            </svg>
            <span>CONTEXT â†’ CONCEPT â†’ ENGINEERING REVIEW</span>
          </div>
        </section>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.55 }}
          className="auth-form-panel"
        >
          <div className="mb-7">
            <p className="auth-eyebrow"><span>02</span> / {effectiveMode === "login" ? "WELCOME BACK" : "GET STARTED"}</p>
            <div className="flex items-start justify-between gap-4">
              <div>
                <h1 className="auth-title">
              {effectiveMode === "login" ? "Sign in" : "Create account"}
                </h1>
              </div>
            </div>
            <p className="mt-3 text-sm leading-relaxed text-muted-foreground">
              {effectiveMode === "register"
                ? "Create your workspace and start exploring site-aware infrastructure concepts."
                : authRequired()
                  ? "Sign in to access your projects and workspace."
                  : "Sign in to return to your saved workspaces."}
            </p>
          </div>

          <div className="mb-5 rounded-lg border border-border bg-background/50 p-4 text-sm leading-relaxed" role="status" aria-label="Authentication mode">
            {configurationError ? "Authentication configuration unavailable. No sign-in was attempted." : firebaseAllowed ? "Firebase sign-in · in-memory session. Access requires a verified, linked backend identity." : signInPreparation(configuration)}
            {configurationError && <button type="button" className="ml-2 text-primary underline" onClick={() => void loadConfiguration()}>Retry configuration</button>}
          </div>
          {passwordAllowed && !registrationAllowed && <p className="mb-4 text-sm text-muted-foreground">Account registration is unavailable. Existing account sign-in remains available.</p>}
          {googleAllowed && <div className="mb-5 space-y-4">
            <Button type="button" variant="outline" size="lg" className="h-12 w-full gap-3 text-base" disabled={loading} onClick={() => void signInFirebase("google")}>
              <svg viewBox="0 0 24 24" className="size-5" aria-hidden="true"><path fill="currentColor" d="M21.6 12.23c0-.71-.06-1.39-.18-2.05H12v3.88h5.38a4.61 4.61 0 0 1-2 3.03v2.52h3.24c1.9-1.75 2.98-4.33 2.98-7.38ZM12 22c2.7 0 4.96-.9 6.62-2.39l-3.24-2.52c-.9.6-2.05.97-3.38.97-2.6 0-4.8-1.76-5.6-4.12H3.06v2.59A10 10 0 0 0 12 22ZM6.4 13.94a6 6 0 0 1 0-3.88V7.47H3.06a10 10 0 0 0 0 9.06l3.34-2.59ZM12 5.94c1.47 0 2.78.5 3.82 1.5l2.87-2.87A9.57 9.57 0 0 0 12 2a10 10 0 0 0-8.94 5.47l3.34 2.59C7.2 7.7 9.4 5.94 12 5.94Z"/></svg>
              {loading ? "Please wait…" : "Continue with Google"}
            </Button>
            {firebasePasswordAllowed && <p className="text-center text-xs text-muted-foreground">or sign in with email</p>}
          </div>}
          {error && <div id={formErrorId} role="alert" className="mb-5 rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">{error}</div>}
          {(passwordAllowed || firebasePasswordAllowed) && <form
            onSubmit={onSubmit}
            className="space-y-5"
            aria-describedby={error ? formErrorId : undefined}
          >
            {effectiveMode === "register" && (
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
            <FormField label="Password" htmlFor="password" hint={firebasePasswordAllowed ? "Use your administrator-approved account password" : "Minimum 8 characters"}>
              <div className="relative"><input id="password" type={showPassword ? "text" : "password"} required minLength={8} className="auth-glass-input w-full rounded-lg border px-4 py-3 pr-12 text-base" value={password} onChange={(e) => setPassword(e.target.value)} autoComplete={effectiveMode === "login" ? "current-password" : "new-password"}/><button type="button" onClick={() => setShowPassword((value) => !value)} className="absolute right-2 top-1/2 -translate-y-1/2 p-2 text-muted-foreground hover:text-foreground" aria-label={showPassword ? "Hide password" : "Show password"} title={showPassword ? "Hide password" : "Show password"}>{showPassword ? <EyeOff className="size-4" /> : <Eye className="size-4" />}</button></div>
            </FormField>
            <Button type="submit" size="lg" className="h-12 w-full text-base" disabled={loading}>
              {loading ? "Please waitâ€¦" : effectiveMode === "login" ? "Sign in" : "Register"}
              {!loading && <ArrowRight className="size-4" aria-hidden="true" />}
            </Button>
          </form>}
          {firebaseAllowed && browserFirebaseConfiguration().recovery && <button type="button" className="mt-4 text-sm text-primary underline" onClick={async () => {
            try { await firebaseRecoverPassword(email); toast("If this account supports recovery, check its email for the next step."); }
            catch { setError("Account recovery is unavailable."); }
          }}>Request password recovery</button>}

          {passwordAllowed && registrationAllowed && <p className="mt-5 text-center text-base text-muted-foreground">
            {effectiveMode === "login" ? (
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
          </p>}
          {!authRequired() && configuration?.mode === 'local_development' && (
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

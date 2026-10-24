/** Backend-authorized, lazy official SDK boundary. Browser claims never authorize API access. */
import type { Auth, User } from "firebase/auth";
export type AuthConfiguration = {
  mode: "local_development" | "legacy_jwt" | "firebase";
  password_login_allowed: boolean;
  registration_allowed?: boolean;
  firebase_project_id: string | null;
  firebase: { enabled: boolean; ready: boolean; code: string; message: string };
};

export function isAuthConfiguration(value: unknown): value is AuthConfiguration {
  if (!value || typeof value !== "object") return false;
  const config = value as Partial<AuthConfiguration>;
  return ["local_development", "legacy_jwt", "firebase"].includes(config.mode || "")
    && typeof config.password_login_allowed === "boolean"
    && (config.registration_allowed === undefined || typeof config.registration_allowed === "boolean")
    && (config.firebase_project_id === null || typeof config.firebase_project_id === "string")
    && !!config.firebase && typeof config.firebase.enabled === "boolean"
    && typeof config.firebase.ready === "boolean" && typeof config.firebase.code === "string"
    && typeof config.firebase.message === "string"
    && (config.mode === "firebase" ? config.firebase.enabled && config.password_login_allowed === false : !config.firebase.enabled);
}

export function signInPreparation(config: AuthConfiguration | null): string {
  if (!config) return "Checking authentication configuration…";
  if (browserFirebaseConfiguration().enabled && config.mode !== "firebase") return "Firebase sign-in unavailable · backend and browser authentication modes do not match.";
  if (config.mode === "local_development") return "Local development identity · not Firebase authentication. Local access may use a shared development user.";
  if (config.mode === "legacy_jwt") return "Existing account sign-in · FastAPI JWT authentication. Firebase sign-in is not enabled.";
  return config.firebase.ready
    ? "Firebase sign-in unavailable · approved browser configuration and genuine staging qualification are required."
    : `Firebase sign-in unavailable · ${config.firebase.message}`;
}

export type BrowserFirebaseConfiguration = {
  enabled: boolean; passwordProvider: boolean; googleProvider?: boolean; recovery: boolean;
  apiKey: string; projectId: string; authDomain: string; appId: string;
};
export function browserFirebaseConfiguration(): BrowserFirebaseConfiguration {
  return {
    enabled: process.env.NEXT_PUBLIC_FIREBASE_AUTH_ENABLED === "true",
    passwordProvider: process.env.NEXT_PUBLIC_FIREBASE_PASSWORD_PROVIDER_ENABLED === "true",
    googleProvider: process.env.NEXT_PUBLIC_FIREBASE_GOOGLE_PROVIDER_ENABLED === "true",
    recovery: process.env.NEXT_PUBLIC_FIREBASE_RECOVERY_ENABLED === "true",
    apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY || "",
    projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID || "",
    authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN || "",
    appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID || "",
  };
}
/** Local shape/identity checks only; cannot prove registered app or API-key ownership. */
export function firebaseConfigurationIssues(client: BrowserFirebaseConfiguration, expectedProjectId: string): string[] {
  const issues: string[] = [];
  if (client.projectId !== expectedProjectId) issues.push("PROJECT_MISMATCH");
  if (!/^[a-z][a-z0-9-]{4,28}[a-z0-9]$/.test(client.projectId)) issues.push("PROJECT_INVALID");
  if (client.authDomain !== `${expectedProjectId}.firebaseapp.com`) issues.push("AUTH_DOMAIN_MISMATCH");
  if (!/^[A-Za-z0-9_-]{20,200}$/.test(client.apiKey)
    || /placeholder|replace[_-]?(?:with|me)|your[_-]?api[_-]?key|change[_-]?me/i.test(client.apiKey)) issues.push("API_KEY_INVALID");
  if (!/^1:[1-9]\d*:web:[a-f0-9]+$/.test(client.appId) || client.appId.length > 256) issues.push("APP_ID_INVALID");
  return issues;
}
export function firebaseSignInAllowed(config: AuthConfiguration | null, client = browserFirebaseConfiguration()): boolean {
  return !!config && config.mode === "firebase" && config.firebase.enabled && config.firebase.ready
    && client.enabled && (client.passwordProvider || client.googleProvider === true)
    && typeof config.firebase_project_id === "string"
    && firebaseConfigurationIssues(client, config.firebase_project_id).length === 0;
}
export const firebasePasswordSignInAllowed = (config: AuthConfiguration | null) => firebaseSignInAllowed(config) && browserFirebaseConfiguration().passwordProvider;
export const firebaseGoogleSignInAllowed = (config: AuthConfiguration | null) => firebaseSignInAllowed(config) && browserFirebaseConfiguration().googleProvider === true;

let configuration: AuthConfiguration | null = null;
let auth: Auth | null = null;
let sdk: typeof import("firebase/auth") | null = null;
let currentUser: User | null = null;
let revision = 0;
let sessionController = new AbortController();
export const sessionSignal = () => sessionController.signal;
let preparation = 0;
let acceptSessionEvents = false;
let signingIn = false;
let signInGeneration = 0;
let unsubscribe: (() => void) | undefined;
const listeners = new Set<() => void>();
export const sessionRevision = () => revision;
export const subscribeSession = (listener: () => void) => { listeners.add(listener); return () => { listeners.delete(listener); }; };
export const firebaseMode = () => configuration?.mode === "firebase" || browserFirebaseConfiguration().enabled;
export const firebaseSignedIn = () => !!currentUser;
export function assertSession(expected: number) {
  if (expected !== revision) throw new Error("Session changed. Discarded the previous account's response.");
}
export function invalidateSession(nextUser: User | null = null) {
  currentUser = nextUser;
  sessionController.abort(); sessionController = new AbortController();
  revision++;
  listeners.forEach(listener => listener());
}
export function firebaseAuthError(): string {
  // Never expose SDK messages, addresses, tokens, provider details or account existence.
  return "Sign-in unavailable or session rejected. Check your details or try again later.";
}
function providerError(error: unknown): Error {
  const code = error && typeof error === "object" && "code" in error ? error.code : "";
  if (code === "auth/popup-closed-by-user" || code === "auth/cancelled-popup-request") return new Error("Google sign-in canceled. No workspace access was granted.");
  if (code === "auth/popup-blocked") return new Error("The Google popup was blocked. Allow popups for this site, then choose Continue with Google again.");
  if (code === "auth/account-exists-with-different-credential" || code === "auth/credential-already-in-use") return new Error("Sign-in could not complete. Use your approved sign-in method or contact an administrator about account linking.");
  if (code === "auth/admin-restricted-operation" || code === "auth/operation-not-allowed") return new Error("This sign-in method is unavailable for this account. Contact your StruvoCivil administrator; public registration is unavailable.");
  return new Error(firebaseAuthError());
}
export async function prepareFirebase(config: AuthConfiguration, client = browserFirebaseConfiguration()): Promise<void> {
  const attempt = ++preparation;
  unsubscribe?.(); unsubscribe = undefined;
  const wasFirebase = firebaseMode();
  configuration = config;
  acceptSessionEvents = false;
  if (wasFirebase || config.mode === "firebase") invalidateSession();
  if (!firebaseSignInAllowed(config, client)) { auth = null; sdk = null; return; }
  // No SDK import or initialization occurs before every gate passes.
  const [apps, authSdk] = await Promise.all([import("firebase/app"), import("firebase/auth")]);
  if (attempt !== preparation) return;
  const name = `struvocivil-browser-${client.projectId}`;
  const existing = apps.getApps().find(app => app.name === name);
  if (existing && (existing.options.projectId !== client.projectId || existing.options.apiKey !== client.apiKey
    || existing.options.authDomain !== client.authDomain || existing.options.appId !== client.appId)) {
    throw new Error("Firebase browser configuration conflict. Reload after approved configuration changes.");
  }
  const app = existing || apps.initializeApp({ apiKey: client.apiKey, projectId: client.projectId, authDomain: client.authDomain, appId: client.appId }, name);
  // initializeAuth deliberately avoids getAuth's default durable browser persistence.
  auth = authSdk.initializeAuth(app, { persistence: authSdk.inMemoryPersistence });
  sdk = authSdk;
  acceptSessionEvents = true;
  unsubscribe = authSdk.onIdTokenChanged(auth, user => {
    if (attempt !== preparation || !acceptSessionEvents) return;
    if (currentUser?.uid !== user?.uid) invalidateSession(user);
    else currentUser = user;
  }, () => { if (attempt === preparation) { acceptSessionEvents = false; invalidateSession(); } });
}
async function providerSignIn(provider: "password" | "google", email = "", password = ""): Promise<void> {
  if (!auth || !sdk || !firebaseSignInAllowed(configuration)) throw new Error("Firebase sign-in unavailable.");
  if (provider === "google" ? !firebaseGoogleSignInAllowed(configuration) : !firebasePasswordSignInAllowed(configuration)) throw new Error("Firebase sign-in unavailable.");
  if (signingIn) throw new Error("A sign-in attempt is already pending.");
  signingIn = true;
  const expected = preparation;
  const generation = signInGeneration;
  const instance = auth; const authSdk = sdk;
  // Clear previous-account UI/cache authority before either provider starts.
  acceptSessionEvents = false;
  invalidateSession();
  try {
    let operation;
    if (provider === "google") {
      const google = new authSdk.GoogleAuthProvider();
      google.setCustomParameters({ prompt: "select_account" });
      // Called synchronously from the click: no redirect or persistence fallback.
      operation = authSdk.signInWithPopup(instance, google, authSdk.browserPopupRedirectResolver);
    } else operation = authSdk.signInWithEmailAndPassword(instance, email, password);
    const result = await operation;
    if (expected !== preparation || generation !== signInGeneration) throw new Error("Session configuration changed.");
    acceptSessionEvents = true;
    if (currentUser?.uid !== result.user.uid) invalidateSession(result.user);
  } catch (error) {
    if (expected === preparation && generation === signInGeneration) {
      acceptSessionEvents = false;
      invalidateSession();
      try { await authSdk.signOut(instance); } catch { /* Local authority remains cleared. */ }
    }
    throw providerError(error);
  }
  finally { signingIn = false; }
}
export const firebaseSignIn = (email: string, password: string) => providerSignIn("password", email, password);
export const firebaseGoogleSignIn = () => providerSignIn("google");
export async function firebaseIdToken(forceRefresh = false): Promise<string | null> {
  if (!firebaseMode()) return null;
  const expected = revision;
  const user = currentUser;
  if (!auth || !sdk || !user) throw new Error("Firebase session unavailable. Sign in again.");
  try {
    const token = await user.getIdToken(forceRefresh);
    assertSession(expected);
    if (!token) throw new Error("Missing ID token");
    return token;
  } catch {
    // A late rejection from account A must not log out account B.
    if (revision === expected) { acceptSessionEvents = false; invalidateSession(); }
    throw new Error("Firebase session unavailable. Sign in again.");
  }
}
export async function firebaseSignOut(): Promise<void> {
  const instance = auth; const authSdk = sdk;
  signInGeneration++;
  acceptSessionEvents = false;
  invalidateSession();
  if (instance && authSdk) {
    try { await authSdk.signOut(instance); }
    catch { throw new Error("Local session cleared. Remote sign-out could not be confirmed."); }
  }
}
export async function firebaseRecoverPassword(email: string): Promise<void> {
  if (!auth || !sdk || !firebasePasswordSignInAllowed(configuration) || !browserFirebaseConfiguration().recovery) {
    throw new Error("Firebase account recovery is unavailable pending approved configuration and recovery policy.");
  }
  // The UI always uses the same non-enumerating outcome, including SDK errors.
  try { await sdk.sendPasswordResetEmail(auth, email); } catch { /* Do not reveal account existence. */ }
}

export function passwordSignInAllowed(config: AuthConfiguration | null): boolean {
  return !browserFirebaseConfiguration().enabled && !!config && ["local_development", "legacy_jwt"].includes(config.mode) && config.password_login_allowed === true;
}

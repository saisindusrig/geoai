// @vitest-environment jsdom
import { afterEach, beforeEach, expect, it, vi } from "vitest";

const mock = vi.hoisted(() => ({ initializeApp: vi.fn(), initializeAuth: vi.fn(), signIn: vi.fn(), popup: vi.fn(), parameters: vi.fn(), signOut: vi.fn(), recovery: vi.fn(), changed: undefined as undefined | ((user: unknown) => void) }));
vi.mock("firebase/app", () => ({ getApps: () => [], initializeApp: mock.initializeApp }));
vi.mock("firebase/auth", () => ({ initializeAuth: mock.initializeAuth, inMemoryPersistence: "MEMORY_ONLY",
  signInWithEmailAndPassword: mock.signIn, signOut: mock.signOut, sendPasswordResetEmail: mock.recovery,
  GoogleAuthProvider: class { setCustomParameters = mock.parameters; }, signInWithPopup: mock.popup, browserPopupRedirectResolver: "POPUP_ONLY",
  onIdTokenChanged: (_: unknown, next: (user: unknown) => void) => { mock.changed = next; return vi.fn(); } }));
const configuration = { mode: "firebase" as const, password_login_allowed: false, registration_allowed: false,
  firebase_project_id: "synthetic-auth-project", firebase: { enabled: true, ready: true, code: "PREREQUISITES_PRESENT", message: "Synthetic only" } };
const user = (uid: string, token = `synthetic-${uid}`) => ({ uid, getIdToken: vi.fn().mockResolvedValue(token) });
beforeEach(() => {
  vi.resetModules(); vi.clearAllMocks(); localStorage.clear(); mock.changed = undefined;
  mock.initializeAuth.mockReturnValue({});
  vi.stubEnv("NEXT_PUBLIC_FIREBASE_AUTH_ENABLED", "true");
  vi.stubEnv("NEXT_PUBLIC_FIREBASE_PASSWORD_PROVIDER_ENABLED", "true");
  vi.stubEnv("NEXT_PUBLIC_FIREBASE_PROJECT_ID", "synthetic-auth-project");
  vi.stubEnv("NEXT_PUBLIC_FIREBASE_API_KEY", "synthetic-public-browser-key-not-real");
  vi.stubEnv("NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN", "synthetic-auth-project.firebaseapp.com");
  vi.stubEnv("NEXT_PUBLIC_FIREBASE_APP_ID", "1:123:web:abc123");
  vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("Unexpected network")));
});
afterEach(() => { vi.unstubAllEnvs(); vi.unstubAllGlobals(); });

it("never initializes an SDK or requests a network connection when disabled or unavailable", async () => {
  const boundary = await import("./firebase-auth");
  for (const config of [configuration, { ...configuration, firebase: { ...configuration.firebase, ready: false } }]) {
    await boundary.prepareFirebase(config, { ...boundary.browserFirebaseConfiguration(), enabled: false });
    await expect(boundary.firebaseIdToken()).rejects.toThrow("unavailable");
  }
  expect(mock.initializeApp).not.toHaveBeenCalled(); expect(fetch).not.toHaveBeenCalled();
});
it.each(["projectId", "authDomain", "appId", "apiKey"])("rejects malformed or mismatched %s before SDK initialization", async key => {
  const b = await import("./firebase-auth");
  await b.prepareFirebase(configuration, { ...b.browserFirebaseConfiguration(), [key]: "invalid" });
  expect(mock.initializeApp).not.toHaveBeenCalled(); expect(fetch).not.toHaveBeenCalled();
});
it("never initializes an obsolete configuration after an asynchronous import", async () => {
  const b = await import("./firebase-auth");
  const pending = b.prepareFirebase(configuration);
  await b.prepareFirebase({ ...configuration, firebase: { ...configuration.firebase, ready: false } });
  await pending;
  expect(mock.initializeApp).not.toHaveBeenCalled(); expect(fetch).not.toHaveBeenCalled();
});
it("uses official modular APIs with memory-only persistence, sanitized errors and no legacy token writes", async () => {
  const b = await import("./firebase-auth"); await b.prepareFirebase(configuration);
  expect(mock.initializeAuth).toHaveBeenCalledWith(undefined, { persistence: "MEMORY_ONLY" });
  mock.changed?.(user("one"));
  expect(localStorage.getItem("geoai_access_token")).toBeNull();
  expect(fetch).not.toHaveBeenCalled();
});
it("refreshes SDK ID tokens, invalidates account caches, and rejects stale token resolutions", async () => {
  mock.initializeAuth.mockReturnValue({});
  const b = await import("./firebase-auth"); await b.prepareFirebase(configuration);
  const changes = vi.fn(); b.subscribeSession(changes);
  const one = user("one"); mock.changed?.(one);
  expect(await b.firebaseIdToken(true)).toBe("synthetic-one"); expect(one.getIdToken).toHaveBeenCalledWith(true);
  let resolve!: (token: string) => void;
  one.getIdToken.mockImplementation(() => new Promise<string>(r => { resolve = r; }));
  const late = b.firebaseIdToken(); mock.changed?.(user("two")); resolve("old-token");
  await expect(late).rejects.toThrow("unavailable"); expect(b.firebaseSignedIn()).toBe(true);
  await b.firebaseSignOut(); expect(b.firebaseSignedIn()).toBe(false); expect(mock.signOut).toHaveBeenCalledOnce();
  expect(changes).toHaveBeenCalledTimes(3);
});
it("fails closed on token expiry or missing user and never uses the legacy bearer in Firebase mode", async () => {
  mock.initializeAuth.mockReturnValue({});
  const b = await import("./firebase-auth"); await b.prepareFirebase(configuration);
  localStorage.setItem("geoai_access_token", "previous-local-token");
  const { api, setAuthToken } = await import("./api");
  await expect(api.get("/api/projects")).rejects.toThrow("unavailable");
  expect(() => setAuthToken("fake")).toThrow("not accepted"); expect(fetch).not.toHaveBeenCalled();
  const expired = user("expired"); expired.getIdToken.mockRejectedValue(new Error("sensitive-provider-error")); mock.changed?.(expired);
  await expect(b.firebaseIdToken()).rejects.toThrow("Sign in again"); expect(b.firebaseSignedIn()).toBe(false);
});
it("never sends an SDK bearer to an external destination", async () => {
  const b = await import("./firebase-auth"); await b.prepareFirebase(configuration); mock.changed?.(user("one"));
  const { authenticatedFetch } = await import("./api");
  await expect(authenticatedFetch("https://outside.invalid/api/projects")).rejects.toThrow("outside");
  expect(fetch).not.toHaveBeenCalled();
});
it("uses the SDK bearer and rejects stale body completion after an account switch", async () => {
  mock.initializeAuth.mockReturnValue({});
  const b = await import("./firebase-auth"); await b.prepareFirebase(configuration); mock.changed?.(user("one"));
  let finish!: (text: string) => void;
  vi.mocked(fetch).mockResolvedValue({ status: 200, ok: true, text: () => new Promise<string>(resolve => { finish = resolve; }) } as Response);
  const { api } = await import("./api"); const pending = api.get("/api/projects/1");
  await vi.waitFor(() => expect(finish).toBeTypeOf("function"));
  expect(new Headers(vi.mocked(fetch).mock.calls[0][1]?.headers).get("Authorization")).toBe("Bearer synthetic-one");
  mock.changed?.(user("two")); finish('{"name":"private account one project"}');
  await expect(pending).rejects.toThrow("Session changed");
});
it("clears rejected sessions without retry, refresh or development fallback", async () => {
  mock.initializeAuth.mockReturnValue({});
  const b = await import("./firebase-auth"); await b.prepareFirebase(configuration); mock.changed?.(user("one"));
  vi.mocked(fetch).mockResolvedValue(new Response('{"detail":"Session rejected"}', { status: 401 }));
  const { api } = await import("./api");
  await expect(api.get("/api/projects")).rejects.toThrow();
  expect(fetch).toHaveBeenCalledOnce(); expect(mock.signOut).toHaveBeenCalledOnce(); expect(b.firebaseSignedIn()).toBe(false);
});
it("does not log out account B when account A's delayed request returns 401", async () => {
  const b = await import("./firebase-auth"); await b.prepareFirebase(configuration); mock.changed?.(user("one"));
  let finish!: (response: Response) => void;
  vi.mocked(fetch).mockImplementationOnce(() => new Promise(resolve => { finish = resolve; }));
  const { api } = await import("./api"); const pending = api.get("/api/projects");
  await vi.waitFor(() => expect(finish).toBeTypeOf("function")); mock.changed?.(user("two"));
  finish(new Response("Rejected old session", { status: 401 }));
  await expect(pending).rejects.toThrow("Session changed"); expect(mock.signOut).not.toHaveBeenCalled();
  expect(b.firebaseSignedIn()).toBe(true);
});
it("sanitizes sign-in errors and keeps recovery disabled without an approved policy", async () => {
  mock.initializeAuth.mockReturnValue({}); mock.signIn.mockRejectedValue(new Error("user-not-found private@example.test"));
  const b = await import("./firebase-auth"); await b.prepareFirebase(configuration);
  await expect(b.firebaseSignIn("synthetic@example.test", "not-a-real-password")).rejects.toThrow(b.firebaseAuthError());
  await expect(b.firebaseRecoverPassword("synthetic@example.test")).rejects.toThrow("unavailable"); expect(mock.recovery).not.toHaveBeenCalled();
});
it("does not resurrect a logged-out account after a failed SDK logout or late token event", async () => {
  mock.signOut.mockRejectedValueOnce(new Error("synthetic outage"));
  const b = await import("./firebase-auth"); await b.prepareFirebase(configuration); mock.changed?.(user("one"));
  await expect(b.firebaseSignOut()).rejects.toThrow("Local session cleared");
  mock.changed?.(user("one")); expect(b.firebaseSignedIn()).toBe(false);
});
it("rejects a pending sign-in that completes after explicit logout", async () => {
  let finish!: (result: { user: ReturnType<typeof user> }) => void;
  mock.signIn.mockImplementationOnce(() => new Promise(resolve => { finish = resolve; }));
  const b = await import("./firebase-auth"); await b.prepareFirebase(configuration);
  const pending = b.firebaseSignIn("synthetic@example.test", "synthetic");
  await b.firebaseSignOut(); finish({ user: user("one") });
  await expect(pending).rejects.toThrow(b.firebaseAuthError()); expect(b.firebaseSignedIn()).toBe(false);
});
it("prepares recovery through the official API only behind the explicit recovery policy gate", async () => {
  vi.stubEnv("NEXT_PUBLIC_FIREBASE_RECOVERY_ENABLED", "true");
  const b = await import("./firebase-auth"); await b.prepareFirebase(configuration);
  await b.firebaseRecoverPassword("synthetic@example.test"); expect(mock.recovery).toHaveBeenCalledWith({}, "synthetic@example.test");
  mock.recovery.mockRejectedValueOnce(new Error("unknown account"));
  await expect(b.firebaseRecoverPassword("unknown@example.test")).resolves.toBeUndefined();
});

it("gates Google independently and uses popup with memory-only Firebase ID-token transport", async () => {
  const b = await import("./firebase-auth"); await b.prepareFirebase(configuration);
  await expect(b.firebaseGoogleSignIn()).rejects.toThrow("unavailable");
  expect(mock.popup).not.toHaveBeenCalled();
  vi.stubEnv("NEXT_PUBLIC_FIREBASE_GOOGLE_PROVIDER_ENABLED", "true");
  mock.popup.mockResolvedValueOnce({ user: user("google-uid", "firebase-id-token") });
  await b.firebaseGoogleSignIn();
  expect(mock.parameters).toHaveBeenCalledWith({ prompt: "select_account" });
  expect(mock.popup).toHaveBeenCalledWith({}, expect.anything(), "POPUP_ONLY");
  expect(await b.firebaseIdToken()).toBe("firebase-id-token");
  expect(mock.initializeAuth).toHaveBeenCalledWith(undefined, { persistence: "MEMORY_ONLY" });
  expect(localStorage.length).toBe(0); expect(fetch).not.toHaveBeenCalled();
});
it.each([
  ["auth/popup-closed-by-user", "canceled"], ["auth/popup-blocked", "blocked"],
  ["auth/account-exists-with-different-credential", "account linking"],
  ["auth/credential-already-in-use", "account linking"],
  ["auth/admin-restricted-operation", "public registration"],
  ["auth/operation-not-allowed", "unavailable"], ["auth/internal-error", "session rejected"],
])("clears previous identity and sanitizes popup failure %s", async (code, message) => {
  vi.stubEnv("NEXT_PUBLIC_FIREBASE_GOOGLE_PROVIDER_ENABLED", "true");
  const b = await import("./firebase-auth"); await b.prepareFirebase(configuration); mock.changed?.(user("old"));
  mock.popup.mockRejectedValueOnce({ code, message: "private@example.test oauth-secret" });
  await expect(b.firebaseGoogleSignIn()).rejects.toThrow(message);
  mock.changed?.(user("late"));
  expect(b.firebaseSignedIn()).toBe(false); expect(mock.signOut).toHaveBeenCalledOnce();
  expect(localStorage.length).toBe(0); expect(fetch).not.toHaveBeenCalled();
});
it("rejects late popup completion after logout and concurrent provider attempts", async () => {
  vi.stubEnv("NEXT_PUBLIC_FIREBASE_GOOGLE_PROVIDER_ENABLED", "true");
  const b = await import("./firebase-auth"); await b.prepareFirebase(configuration);
  let finish!: (result: { user: ReturnType<typeof user> }) => void;
  mock.popup.mockImplementationOnce(() => new Promise(resolve => { finish = resolve; }));
  const pending = b.firebaseGoogleSignIn();
  await expect(b.firebaseSignIn("synthetic@example.test", "synthetic")).rejects.toThrow("already pending");
  await b.firebaseSignOut(); finish({ user: user("late") });
  await expect(pending).rejects.toThrow(); expect(b.firebaseSignedIn()).toBe(false);
});
it("permits a Google-only configuration without enabling password or legacy login", async () => {
  vi.stubEnv("NEXT_PUBLIC_FIREBASE_GOOGLE_PROVIDER_ENABLED", "true");
  vi.stubEnv("NEXT_PUBLIC_FIREBASE_PASSWORD_PROVIDER_ENABLED", "false");
  const b = await import("./firebase-auth"); await b.prepareFirebase(configuration);
  expect(b.firebaseGoogleSignInAllowed(configuration)).toBe(true);
  expect(b.passwordSignInAllowed(configuration)).toBe(false);
  await expect(b.firebaseSignIn("synthetic", "synthetic")).rejects.toThrow("unavailable");
});

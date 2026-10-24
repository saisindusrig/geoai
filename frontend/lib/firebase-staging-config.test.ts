import { readFileSync } from "node:fs";
import path from "node:path";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { firebaseConfigurationIssues, firebaseSignInAllowed, prepareFirebase, type AuthConfiguration, type BrowserFirebaseConfiguration } from "./firebase-auth";

const sdk = vi.hoisted(() => ({ app: vi.fn(), auth: vi.fn() }));
vi.mock("firebase/app", () => ({ initializeApp: sdk.app, getApps: () => [] }));
vi.mock("firebase/auth", () => ({ initializeAuth: sdk.auth }));
const project = "struvocivil-918c9";
const template = readFileSync(process.env.STRUVO_FIREBASE_TEMPLATE_FIXTURE || path.resolve("../docs/release-phase-c/gate-2h/frontend.staging.env.template"), "utf8");
const values = Object.fromEntries(template.split(/\r?\n/).filter(line => line && !line.startsWith("#")).map(line => {
  const split = line.indexOf("="); return [line.slice(0, split), line.slice(split + 1)];
}));
const client: BrowserFirebaseConfiguration = {
  enabled: values.NEXT_PUBLIC_FIREBASE_AUTH_ENABLED === "true", passwordProvider: values.NEXT_PUBLIC_FIREBASE_PASSWORD_PROVIDER_ENABLED === "true",
  googleProvider: values.NEXT_PUBLIC_FIREBASE_GOOGLE_PROVIDER_ENABLED === "true", recovery: values.NEXT_PUBLIC_FIREBASE_RECOVERY_ENABLED === "true",
  projectId: values.NEXT_PUBLIC_FIREBASE_PROJECT_ID, authDomain: values.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
  apiKey: values.NEXT_PUBLIC_FIREBASE_API_KEY, appId: values.NEXT_PUBLIC_FIREBASE_APP_ID,
};
const backend: AuthConfiguration = { mode: "firebase", password_login_allowed: false, registration_allowed: false,
  firebase_project_id: project, firebase: { enabled: true, ready: true, code: "SYNTHETIC", message: "Offline mock only" } };
const synthetic = { ...client, enabled: true, apiKey: "synthetic-browser-key-not-a-real-key", appId: "1:123:web:abc123" };
beforeEach(() => { vi.clearAllMocks(); vi.stubGlobal("fetch", vi.fn(() => { throw Error("Unexpected network"); })); });
afterEach(() => { vi.unstubAllGlobals(); });

it("pins the staging project/domain with only two unknown official app values and both providers prepared", () => {
  expect(client.projectId).toBe(project); expect(client.authDomain).toBe(`${project}.firebaseapp.com`);
  expect(client.enabled).toBe(false); expect(client.recovery).toBe(false);
  expect(client.googleProvider).toBe(true); expect(client.passwordProvider).toBe(true);
  expect(firebaseConfigurationIssues(client, project)).toEqual(["API_KEY_INVALID", "APP_ID_INVALID"]);
  expect(Object.keys(values)).toHaveLength(8);
});
it("never initializes the SDK for the template, placeholders, or backend-unavailable configuration", async () => {
  for (const candidate of [client, { ...client, enabled: true }, { ...synthetic, enabled: false }]) {
    expect(firebaseSignInAllowed(backend, candidate)).toBe(false); await prepareFirebase(backend, candidate);
  }
  await prepareFirebase({ ...backend, firebase: { ...backend.firebase, ready: false } }, synthetic);
  expect(sdk.app).not.toHaveBeenCalled(); expect(sdk.auth).not.toHaveBeenCalled(); expect(fetch).not.toHaveBeenCalled();
});
it.each([
  ["projectId", "other-project", "PROJECT_MISMATCH"], ["projectId", "StruvoCivil", "PROJECT_INVALID"],
  ["authDomain", "https://struvocivil-918c9.firebaseapp.com", "AUTH_DOMAIN_MISMATCH"],
  ["authDomain", "struvocivil-918c9.firebaseapp.com.attacker.invalid", "AUTH_DOMAIN_MISMATCH"],
  ["authDomain", "struvocivil-918c9.web.app", "AUTH_DOMAIN_MISMATCH"],
  ["apiKey", "REPLACE_WITH_OFFICIAL_API_KEY", "API_KEY_INVALID"], ["apiKey", "", "API_KEY_INVALID"],
  ["appId", "1:123:android:abc123", "APP_ID_INVALID"], ["appId", "1:0:web:abc123", "APP_ID_INVALID"],
  ["appId", "<OFFICIAL_WEB_APP_ID>", "APP_ID_INVALID"],
])("rejects invalid %s before initialization", async (key, value, code) => {
  const invalid = { ...synthetic, [key]: value };
  expect(firebaseConfigurationIssues(invalid, project)).toContain(code);
  await prepareFirebase(backend, invalid); expect(sdk.app).not.toHaveBeenCalled(); expect(fetch).not.toHaveBeenCalled();
});
it("accepts only the synthetic shape locally, without claiming an actual registered app binding", () => {
  expect(firebaseConfigurationIssues(synthetic, project)).toEqual([]); expect(firebaseSignInAllowed(backend, synthetic)).toBe(true);
  expect(firebaseSignInAllowed({ ...backend, firebase_project_id: "other-project" }, synthetic)).toBe(false);
  expect(firebaseSignInAllowed({ ...backend, mode: "local_development" }, synthetic)).toBe(false);
  expect(firebaseSignInAllowed(backend, { ...synthetic, googleProvider: false, passwordProvider: false })).toBe(false);
  expect(sdk.app).not.toHaveBeenCalled(); expect(fetch).not.toHaveBeenCalled();
});

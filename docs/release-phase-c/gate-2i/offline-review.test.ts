/** Review supplied public identifiers only; never initialize a real SDK or log values. */
import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import path from "node:path";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { firebaseConfigurationIssues, firebaseSignInAllowed, prepareFirebase, type AuthConfiguration, type BrowserFirebaseConfiguration } from "@/lib/firebase-auth";

const calls = vi.hoisted(() => ({ app: vi.fn(), auth: vi.fn() }));
vi.mock("firebase/app", () => ({ getApps: () => [], initializeApp: calls.app }));
vi.mock("firebase/auth", () => ({ initializeAuth: calls.auth }));
const folder = process.env.STRUVO_GATE2I_REVIEW_DIR!;
const raw = readFileSync(path.join(folder, "frontend.staging.env.review"));
const lines = raw.toString("utf8").split(/\r?\n/).filter(line => line.trim() && !line.trimStart().startsWith("#"));
const entries = lines.map(line => { const n = line.indexOf("="); if (n <= 0) throw Error("Invalid review assignment"); return [line.slice(0, n), line.slice(n + 1)]; });
const values = Object.fromEntries(entries);
const client: BrowserFirebaseConfiguration = {
  projectId: values.NEXT_PUBLIC_FIREBASE_PROJECT_ID, authDomain: values.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
  apiKey: values.NEXT_PUBLIC_FIREBASE_API_KEY, appId: values.NEXT_PUBLIC_FIREBASE_APP_ID,
  enabled: values.NEXT_PUBLIC_FIREBASE_AUTH_ENABLED === "true",
  passwordProvider: values.NEXT_PUBLIC_FIREBASE_PASSWORD_PROVIDER_ENABLED === "true",
  googleProvider: values.NEXT_PUBLIC_FIREBASE_GOOGLE_PROVIDER_ENABLED === "true",
  recovery: values.NEXT_PUBLIC_FIREBASE_RECOVERY_ENABLED === "true",
};
const backend: AuthConfiguration = { mode: "firebase", password_login_allowed: false, registration_allowed: false,
  firebase_project_id: "struvocivil-918c9", firebase: { enabled: true, ready: true, code: "MOCK_ONLY", message: "Offline test; no real backend" } };
beforeEach(() => { vi.clearAllMocks(); vi.stubGlobal("fetch", vi.fn(() => { throw Error("Network forbidden"); })); });
afterEach(() => vi.unstubAllGlobals());

it("contains exactly the eight approved assignment keys without duplicate keys or script content", () => {
  expect(entries.length).toBe(8); expect(Object.keys(values).length).toBe(8);
  expect(Object.keys(values).sort()).toEqual([
    "NEXT_PUBLIC_FIREBASE_API_KEY", "NEXT_PUBLIC_FIREBASE_APP_ID", "NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN", "NEXT_PUBLIC_FIREBASE_AUTH_ENABLED",
    "NEXT_PUBLIC_FIREBASE_GOOGLE_PROVIDER_ENABLED", "NEXT_PUBLIC_FIREBASE_PASSWORD_PROVIDER_ENABLED", "NEXT_PUBLIC_FIREBASE_PROJECT_ID", "NEXT_PUBLIC_FIREBASE_RECOVERY_ENABLED",
  ]);
  expect(lines.some(line => /[`;$]|\$\(|-----BEGIN|private_key|refresh_token|client_secret/i.test(line))).toBe(false);
});
it("matches the owner-approved exact staging project", () => expect(client.projectId === "struvocivil-918c9").toBe(true));
it("matches the exact expected standard auth domain", () => expect(client.authDomain === "struvocivil-918c9.firebaseapp.com").toBe(true));
it("passes the existing local Web app/API-key format checks without claiming ownership", () => {
  expect(firebaseConfigurationIssues(client, "struvocivil-918c9")).toEqual([]);
  expect(firebaseConfigurationIssues(client, "other-project")).toContain("PROJECT_MISMATCH");
});
it("keeps Firebase and recovery explicitly false", () => {
  expect(values.NEXT_PUBLIC_FIREBASE_AUTH_ENABLED === "false").toBe(true);
  expect(values.NEXT_PUBLIC_FIREBASE_RECOVERY_ENABLED === "false").toBe(true);
});
it("preserves both prepared providers without enabling the connection", () => {
  expect(client.passwordProvider && client.googleProvider && !client.enabled).toBe(true);
  expect(firebaseSignInAllowed(backend, client)).toBe(false);
});
it("matches the supplied review digest, which proves packet integrity only", () => {
  const declared = JSON.parse(readFileSync(path.join(folder, "VALIDATION.json"), "utf8"));
  expect(createHash("sha256").update(raw).digest("hex") === declared.sha256).toBe(true);
});
it.each([
  ["apiKey", "NEXT_PUBLIC_FIREBASE_API_KEY"], ["authDomain", "NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN"],
  ["projectId", "NEXT_PUBLIC_FIREBASE_PROJECT_ID"], ["appId", "NEXT_PUBLIC_FIREBASE_APP_ID"],
])("exactly matches %s to the owner-supplied Console reference", (field, variable) => {
  const reference = JSON.parse(readFileSync(path.join(folder, "owner-console-reference.json"), "utf8"));
  const actual = createHash("sha256").update(values[variable], "utf8").digest("hex");
  expect(actual === reference.identifier_sha256[field]).toBe(true);
});
it("does not initialize Firebase or call the network even with a mocked ready backend", async () => {
  await prepareFirebase(backend, client);
  expect(calls.app).not.toHaveBeenCalled(); expect(calls.auth).not.toHaveBeenCalled(); expect(fetch).not.toHaveBeenCalled();
});

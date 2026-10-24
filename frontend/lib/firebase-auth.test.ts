import { expect, it } from "vitest";
import { isAuthConfiguration, passwordSignInAllowed, signInPreparation, type AuthConfiguration } from "./firebase-auth";

const local: AuthConfiguration = { mode: "local_development", password_login_allowed: true,
  firebase_project_id: null, firebase: { enabled: false, ready: false, code: "DISABLED", message: "Disabled" } };
it("clearly distinguishes local development from genuine Firebase authentication", () => {
  expect(signInPreparation(local)).toContain("not Firebase authentication");
  expect(passwordSignInAllowed(local)).toBe(true);
  expect(passwordSignInAllowed(null)).toBe(false);
  expect(signInPreparation({ ...local, mode: "legacy_jwt" })).toContain("FastAPI JWT");
});
it("never presents a working Firebase login merely because backend prerequisites exist", () => {
  for (const ready of [true, false]) {
    const config: AuthConfiguration = { ...local, mode: "firebase", firebase: { ...local.firebase, enabled: true, ready } };
    expect(passwordSignInAllowed(config)).toBe(false);
    expect(signInPreparation(config)).toContain("Firebase sign-in unavailable");
  }
});

it("validates the backend configuration boundary at runtime", () => {
  expect(isAuthConfiguration(local)).toBe(true);
  expect(isAuthConfiguration({ password_login_allowed: true })).toBe(false);
  expect(isAuthConfiguration({ ...local, mode: "unknown" })).toBe(false);
});
it("rejects malformed registration capability while retaining older local config compatibility", () => {
  expect(isAuthConfiguration({ ...local, registration_allowed: false })).toBe(true);
  expect(isAuthConfiguration({ ...local, registration_allowed: "true" })).toBe(false);
});

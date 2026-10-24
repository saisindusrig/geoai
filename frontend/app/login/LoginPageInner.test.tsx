import React from "react";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import LoginPageInner from "./LoginPageInner";
import { api, authRequired, setAuthToken } from "@/lib/api";
const replace = vi.fn();
const provider = vi.hoisted(() => ({ google: vi.fn(), password: vi.fn(), signOut: vi.fn() }));
vi.mock("@/lib/firebase-auth", async original => ({
  ...await original<typeof import("@/lib/firebase-auth")>(),
  firebaseGoogleSignIn: provider.google, firebaseSignIn: provider.password, firebaseSignOut: provider.signOut,
}));
vi.mock("next/navigation", () => ({ useRouter: () => ({ replace }), useSearchParams: () => new URLSearchParams("next=/projects/1/workspace") }));
vi.mock("@/lib/api", () => ({ api: { get: vi.fn(), post: vi.fn() }, authRequired: vi.fn(() => false), setAuthToken: vi.fn(), formatApiErrorMessage: () => "Sign-in failed" }));
vi.mock("@/lib/toast", () => ({ toast: vi.fn() }));
const local = { firebase_project_id: null, mode: "local_development", password_login_allowed: true, firebase: { enabled: false, ready: false, code: "DISABLED", message: "Disabled" } };
beforeEach(() => { vi.mocked(api.get).mockResolvedValue(local); vi.mocked(authRequired).mockReturnValue(false); });
afterEach(() => { cleanup(); vi.resetAllMocks(); vi.unstubAllEnvs(); });
it("keeps existing local login and explicitly labels the development identity", async () => {
  render(<LoginPageInner />);
  await screen.findByText(/Local development identity/);
  expect(screen.getByRole("link", { name: "Continue to dashboard" })).toHaveAttribute("href", "/dashboard");
  vi.mocked(api.post).mockResolvedValue({ access_token: "synthetic-local-token" });
  fireEvent.change(screen.getByLabelText("Email"), { target: { value: "synthetic@example.test" } });
  fireEvent.change(screen.getByLabelText("Password"), { target: { value: "synthetic-password" } });
  fireEvent.click(screen.getByRole("button", { name: "Sign in" }));
  await vi.waitFor(() => expect(replace).toHaveBeenCalledWith("/projects/1/workspace"));
  expect(setAuthToken).toHaveBeenCalledWith("synthetic-local-token");
});
it("hides legacy login and signup in Firebase mode without offering a fake Google button", async () => {
  vi.mocked(api.get).mockResolvedValue({ ...local, mode: "firebase", password_login_allowed: false, firebase: { ...local.firebase, enabled: true } });
  render(<LoginPageInner />);
  await screen.findByText(/Firebase sign-in unavailable/);
  expect(screen.queryByLabelText("Password")).toBeNull();
  expect(screen.queryByRole("button", { name: /Google|Sign in|Register/ })).toBeNull();
  expect(screen.queryByRole("link", { name: "Continue to dashboard" })).toBeNull();
  expect(api.post).not.toHaveBeenCalled();
});
it("fails closed on configuration errors and recovers only after manual retry", async () => {
  vi.mocked(api.get).mockRejectedValueOnce(new Error("Synthetic outage"));
  render(<LoginPageInner />);
  await screen.findByText(/Authentication configuration unavailable/);
  expect(screen.queryByLabelText("Password")).toBeNull();
  fireEvent.click(screen.getByRole("button", { name: "Retry configuration" }));
  await screen.findByLabelText("Password");
  expect(api.get).toHaveBeenCalledTimes(2); expect(api.post).not.toHaveBeenCalled();
});

it("rejects a malformed configuration instead of enabling a login form", async () => {
  vi.mocked(api.get).mockResolvedValue({ password_login_allowed: true });
  render(<LoginPageInner />);
  await screen.findByText(/Authentication configuration unavailable/);
  expect(screen.queryByLabelText("Password")).toBeNull();
});
it("hides unavailable production registration while preserving existing account sign-in", async () => {
  vi.mocked(api.get).mockResolvedValue({ ...local, mode: "legacy_jwt", registration_allowed: false });
  render(<LoginPageInner />);
  await screen.findByText(/Account registration is unavailable/);
  expect(screen.queryByRole("button", { name: "Register" })).toBeNull();
  expect(screen.getByRole("button", { name: "Sign in" })).toBeEnabled();
  await vi.waitFor(() => expect(screen.getByLabelText("Password")).toBeVisible());
  expect(api.post).not.toHaveBeenCalled();
});

function dualProvider() {
  for (const [key, value] of Object.entries({ NEXT_PUBLIC_FIREBASE_AUTH_ENABLED: "true", NEXT_PUBLIC_FIREBASE_PASSWORD_PROVIDER_ENABLED: "true",
    NEXT_PUBLIC_FIREBASE_GOOGLE_PROVIDER_ENABLED: "true", NEXT_PUBLIC_FIREBASE_PROJECT_ID: "synthetic-auth-project",
    NEXT_PUBLIC_FIREBASE_API_KEY: "synthetic-public-browser-key-not-real", NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN: "synthetic-auth-project.firebaseapp.com",
    NEXT_PUBLIC_FIREBASE_APP_ID: "1:123:web:abc123" })) vi.stubEnv(key, value);
  const config = { ...local, mode: "firebase", password_login_allowed: false, registration_allowed: false,
    firebase_project_id: "synthetic-auth-project", firebase: { ...local.firebase, enabled: true, ready: true } };
  vi.mocked(api.get).mockImplementation(async path => path === "/api/auth/config" ? config : { id: 42 });
}
it.each(["Google", "password"])("requires backend identity authorization after %s sign-in", async method => {
  dualProvider(); render(<LoginPageInner />);
  await screen.findByRole("button", { name: "Continue with Google" });
  if (method === "Google") fireEvent.click(screen.getByRole("button", { name: "Continue with Google" }));
  else {
    fireEvent.change(screen.getByLabelText("Email"), { target: { value: "synthetic@example.test" } });
    fireEvent.change(screen.getByLabelText("Password"), { target: { value: "synthetic-password" } });
    fireEvent.click(screen.getByRole("button", { name: "Sign in" }));
  }
  await vi.waitFor(() => expect(api.get).toHaveBeenCalledWith("/api/auth/me"));
  expect(method === "Google" ? provider.google : provider.password).toHaveBeenCalledOnce();
  await vi.waitFor(() => expect(replace).toHaveBeenCalledWith("/projects/1/workspace"));
  expect(setAuthToken).not.toHaveBeenCalled(); expect(api.post).not.toHaveBeenCalled();
  expect(screen.queryByRole("button", { name: "Register" })).toBeNull();
});
it("denies an unlinked Google account, signs out, and never routes to the workspace", async () => {
  dualProvider(); const check = vi.mocked(api.get).getMockImplementation()!;
  vi.mocked(api.get).mockImplementation(path => path === "/api/auth/me" ? Promise.reject({ status: 403, message: "private identity details" }) : check(path));
  render(<LoginPageInner />); fireEvent.click(await screen.findByRole("button", { name: "Continue with Google" }));
  expect(await screen.findByRole("alert")).toHaveTextContent("Access denied");
  expect(provider.signOut).toHaveBeenCalledOnce(); expect(replace).not.toHaveBeenCalled();
  expect(screen.getByRole("alert")).not.toHaveTextContent("private identity");
});
it("shows safe popup cancellation without a backend check or legacy fallback", async () => {
  dualProvider(); provider.google.mockRejectedValueOnce(new Error("Google sign-in canceled. No workspace access was granted."));
  render(<LoginPageInner />); fireEvent.click(await screen.findByRole("button", { name: "Continue with Google" }));
  expect(await screen.findByRole("alert")).toHaveTextContent("canceled");
  expect(api.get).not.toHaveBeenCalledWith("/api/auth/me"); expect(replace).not.toHaveBeenCalled(); expect(api.post).not.toHaveBeenCalled();
});
it("disables both provider controls while a popup is pending", async () => {
  dualProvider(); provider.google.mockImplementationOnce(() => new Promise(() => {}));
  render(<LoginPageInner />); fireEvent.click(await screen.findByRole("button", { name: "Continue with Google" }));
  await vi.waitFor(() => expect(screen.getAllByRole("button", { name: /Please wait/ })).toHaveLength(2));
  for (const button of screen.getAllByRole("button", { name: /Please wait/ })) expect(button).toBeDisabled();
});

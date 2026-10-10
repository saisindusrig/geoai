# Nebius authentication restoration

## 1. Root cause

The live acceptance process inherited a rejected process-environment credential. Standard Pydantic settings precedence allowed it to override the different, valid repository `.env` credential. The process credential had 236 characters; the repository credential had 234. Both normalized without whitespace errors and were different even after normalization. No key material or fragments were printed.

The previous three requests returned HTTP 401 using the inherited credential. After selecting the repository credential through shared configuration, the single authorized model-list request and single minimal completion both succeeded. This establishes the override as the cause; it does not establish whether the rejected credential was expired, revoked or otherwise invalid.

## 2. Credential source actually used

Before: process environment → shared `Settings` singleton → shared Nebius resolver/provider. The acceptance script did not request an explicit env-file override. The normal app imports the same singleton before provider construction. The configured file list is repository `.env`, then backend `.env`; backend `.env` is absent locally.

After: repository `.env` is authoritative for the Nebius credential in local development. Other settings retain their existing precedence. Explicit constructor credentials still win. Production/staging retain process-environment credential precedence. A missing or blank local file credential falls back to the normal process source.

## 3. Stale process environment

Yes: a different, rejected inherited credential was involved. It remains present in the parent environment, but the shared development loader now prevents it overriding the repository credential. No global Windows user/system environment variable was edited.

The verified local workspace Uvicorn backend was restarted so its already-imported settings singleton would reload the corrected source. Startup completed. No generation message was submitted during restart.

## 4. Authoritative base URL

`https://api.tokenfactory.nebius.com/v1`, from the existing settings default (`NEBIUS_TOKEN_FACTORY_BASE_URL`). `NEBIUS_BASE_URL` is empty; neither the process nor the repository supplies an overriding base URL. No stale host, duplicate `/v1`, missing `/v1`, query or embedded URL credential was involved. The resolver strips a trailing slash and joins allowed endpoints exactly once.

PRIMARY remains `Qwen/Qwen3.5-397B-A17B`, sourced from repository `.env`. FAST remains unset. No model/configuration values were rewritten in `.env`.

## 5. Key detected

**true**. Diagnostics expose configuration presence, source and length only. Credential normalization trims surrounding whitespace/quotes and an optional Bearer prefix, and rejects internal whitespace/newlines. Secrets remain excluded from repr and error diagnostics.

## 6. GET /models

Exactly **one request** through the existing `available_assistant_models` / shared `_request` transport. Result: **HTTP 200**. The configured PRIMARY model was listed. No extra connectivity request or retry occurred.

## 7. Minimal Qwen completion

Exactly **one request** through existing `NebiusProvider` and `ModelRouter`, after model-list success. No site or project data was included. Result: **HTTP 200**, parsed `{"status":"ok"}`, finish_reason `stop`; no repair. The existing PRIMARY token limit, temperature and timeout were retained. Metadata reported 950 output tokens and no output-limit hit; hidden reasoning text was not retained.

Saved sanitized result: `backend/live-results/auth-restoration-v1.json`. The utility refuses to reuse that batch file, preventing accidental extra requests.

## 8. Files changed

- `backend/app/core/config.py`: shared local-development credential precedence, preserving deployment and other setting precedence.
- `backend/app/services/ai/nebius_config.py`: precise sanitized source diagnostics, including explicit diagnostic env-file attribution.
- `backend/scripts/check_assistant_provider.py`: use the existing PRIMARY router and report the actual routed model rather than the legacy CHAT default; no additional client.
- `backend/scripts/check_nebius_auth.py`: bounded one-GET/one-completion utility with stop-on-failure and persisted batch guard.
- `backend/tests/test_nebius_env_precedence.py`: five offline precedence/source/redaction tests.
- `docs/NEBIUS_AUTH_RESTORATION.md`: this report.

The normal Assistant runtime, NebiusProvider, ModelRouter, live acceptance script and verification utilities all import the same shared settings/resolver path. Existing `use_env_file` remains an explicit diagnostic override through that same resolver; it is not implicitly used by normal application or acceptance flows. Diagnostic `dotenv_values` reads inspect sources; they do not load another client or silently replace model settings.

## 9. Focused tests

**54 passed**, one existing test-client deprecation warning. Suites: environment precedence, explicit env-file loading, sanitized diagnostics, HTTP auth failures/no retry, base normalization, shared provider transport and model routing. All test transports were mocked; tests made no live requests.

## 10. Stop / unchanged architecture

**No AREA, bridge or walkway generation case was rerun.** Total authorized live requests: one GET and one minimal chat completion. No Qwen model change, AI3DDesign change, executor change, prompt/tool change, token/temperature change, workspace change or primitive addition occurred. No further request is scheduled or initiated.

# Milestone 4 — Security and private-beta readiness

**Decision: BLOCKED for a shared private beta. Local preview remains available at http://localhost:3001. No deployment or production approval.**

Reviewed existing production/security findings, Milestone 2 capability protections and Milestone 3 diagnostics/preservation evidence. This was a local source-backed review with isolated fixtures, not an exhaustive penetration test. No external AI scanner/agent was invoked.

## Confirmed findings and focused fixes
1. **High — development-token authentication bypass (fixed).** With JWT enforcement enabled in a non-production environment, unauthenticated `/api/auth/token` could mint a token for a chosen existing user. An isolated reproduction returned 200 before the change; the endpoint now returns 403 whenever JWT is required. Deliberate non-JWT development remains available and production remains denied. No original user/token records were changed.
2. **Medium — spoofed rate-limit/audit IP (fixed).** Rotating raw `X-Forwarded-For` bypassed the 20/minute login limit and forged audit IP attribution. Both consumers now use the ASGI peer identity. The normal offline API disables proxy-header trust, so a direct local client cannot supply the normalized identity. A shared deployment must still qualify its proxy chain and strip untrusted forwarding headers. Historical audit records are preserved.
3. **Critical — affected Windows Next.js dependency (blocked).** Installed Next 16.2.9 and this Windows App Router configuration match the [publisher advisory](https://github.com/vercel/next.js/security/advisories/GHSA-p293-qw3h-jr36). No RCE exploit was executed. Existing local launch commands now bind the frontend to 127.0.0.1 instead of the framework's all-interface default; this is exposure reduction, not a vendor patch. No dependency was upgraded.

Source evidence and exact reproduction details: findings.json, reproduction-before.log. Source edits: backend/app/api/routes/auth.py; backend/app/services/rate_limit.py; backend/app/services/audit.py; backend/scripts/serve_copilot_review_local.py; run-website.bat; start-copilot-review.ps1; frontend/package.json (scripts only, no dependency changes).

## Existing control audit
- Project/revision/evidence routes retain ownership checks and non-disclosing 404 rejection. JWT expiration/signature checks, production startup guards and exact engineering proposal/input/document hash gates remain in place.
- Local file containment, project prefix ownership, allowlisted artifact names, DXF content/size bounds and immutable source hash checks were reused. A temporary corrupted source copy is rejected with 409; original drawings were never modified.
- Bearer authorization is sent explicitly by the API client; it is not a cookie session. Cross-site requests do not automatically acquire that bearer token. Local-storage token exposure under XSS, revocation, account recovery and the complete production session lifecycle remain unqualified. Non-JWT local mode is not a shared-user security boundary.
- CORS tests reject an untrusted origin; Netlify wildcard support remains opt-in. CORS is not authorization. Shared origin/proxy/CSRF policy requires deployment-specific qualification.
- Request IDs and structured logging remain; audit metadata removes sensitive named fields. Diagnostics returns flags/codes rather than credential values and makes no inference calls. No Git/history secret scan, secret rotation or external monitoring qualification was performed.
- Browser evidence confirms missing CSP, framing and MIME-sniffing headers on current frontend responses. This is an unresolved deployment policy risk, not a proven engineering-authorization bypass. No broad CSP/header redesign was introduced without compatibility evidence.

## Four current diagnostics warnings
| Warning | Private-beta status | Evidence / required action |
|---|---|---|
| insecure_app_secret | Blocked | Development default detected; production startup fails closed on default/short secrets or disabled JWT. Provision reviewed identity configuration separately; no credentials changed here. |
| redis_unavailable | Blocked | Local in-memory jobs are not durable. Qualify Redis/worker availability, limits and restart recovery before shared use. |
| local_storage | Blocked | Local files work with existing ownership/path gates in JWT mode; production persistence, private storage and consistent recovery are not qualified. |
| map_tokens_missing | Unverified | Existing OSM fallback remains available; optional imagery/provider access and operational terms were not tested. This is not a numerical-method failure. |

Current sanitized snapshot: runtime-final.json. None of these warnings was suppressed or reclassified as production-ready.

## Dependency assessment
The retained audit contains **37 affected package entries: 5 critical, 22 high, 9 moderate, 1 low**. These are not 37 demonstrated application exploits. Every entry has installed versions, severity, exposure classification, inherited/direct advisory links and exploitability limitations in dependency-review.json; the compact table is DEPENDENCIES.md. No fresh registry audit or Python vulnerability scanner was run/installed.

Next's Windows advisory is applicable to the installed component. MapLibre 5.24.0 and the TerraDraw wrapper inherit an affected sanitizer, but the reviewed attribution strings are constants; an attacker-controlled attribution path was not demonstrated ([publisher source](https://github.com/maplibre/maplibre-gl-js/security/advisories/GHSA-jrc7-96c5-q579)). Vitest/Tinypool/Vite tooling reports require separate exposed-server/plugin or worker-option conditions; the application does not expose those test endpoints in reviewed source. Other asset/parser, build-tool and HTTP-client reports remain conditional/unverified, not dismissed. Package remediation and subsequent qualification require a separately authorized change.

## Private-beta readiness matrix
Ready means only the explicitly tested scope below, not overall release approval.

| Area | Status | Evidence / limit |
|---|---|---|
| Ownership and JWT control implementation | Ready | Isolated cross-user/project/revision, invalid/expired token and mock-header rejection; new shortcut regression. |
| Current shared-user authentication configuration | Blocked | Normal preview intentionally uses mock/non-JWT identity and a development secret. |
| Secure file/import control implementation | Ready | Owned/foreign files, real drawing source route, invalid/oversized imports, traversal, artifact allowlist and source hash tests. |
| Engineering execution and stale-result controls | Ready | Existing exact-authorization/hash/idempotency regressions; stale report 417 rejected, current report 421 accessible. No safety approval. |
| Original data/evidence preservation | Ready | Exact row/schema and immutable artifact comparisons below. |
| Database persistence / durable jobs | Blocked | Local SQLite/inline operation is not a qualified shared production data tier. |
| Backup and restore | Unverified | Existing preservation backups/manifests verified; no production restore drill, encryption/RPO/RTO or cross-store consistency qualification. |
| Local errors and manual recovery | Ready | Fresh browser simulated outage clears old health; explicit Retry recovers without mutation replay. Physical crash recovery was not newly tested. |
| Credential-safe logging / monitoring | Unverified | Metadata redaction and request identity covered; no alert delivery, retention or on-call drill. |
| Dependency exposure | Blocked | Applicable critical Next advisory remains unpatched; remaining reports need scoped remediation/validation. |
| Browser headers / HTTPS / proxy / session policy | Blocked | Missing response headers observed; deployment and reverse-proxy trust remain unqualified. |
| Frontend/backend/browser checks | Ready | Focused results below; no claim that all legacy suites or every route passed. |
| Capacity / parser abuse / distributed limits | Unverified | Login abuse boundary covered; no exhaustive malformed-parser fuzzing, concurrency or multi-worker resource qualification. |
| Unsupported engineering / complete safety workflow | Blocked | Existing unsupported capabilities remain disabled; numerical verification is not structural approval. |

## Verification and failures retained
- 100 targeted backend regressions passed across existing authorization, stale-result, upload, configuration, CORS and diagnostics suites (backend-targeted.log). Expanded security tests: 25 passed (security-final.log); six drawing-route checks passed after adding the valid temporary source/hash case (drawing-access-final.log). Across these runs, 110 distinct backend tests passed; overlapping reruns are not counted twice.
- 32 focused frontend tests passed across eight files (frontend-targeted.log). New tests verify download destination restrictions, bearer non-disclosure to outside origins, redirect refusal and denied-download no-retry behavior. TypeScript and scoped ESLint passed.
- Fresh real Chromium: **2 passed**, 1280×900 and 1600×900. Invalid token 401; cross-user read/download 404; non-allowlisted artifact 404; stale result 417 report 409; current result 421 report 200 attachment with saved SHA-256. All browser mutations/external requests are blocked. These normal-preview ownership probes use its development identity header; JWT enforcement is tested separately in isolated applications.
- Manual recovery, keyboard refresh, scrolling and no horizontal overflow passed. Screenshots: diagnostics-1280.png, diagnostics-1600.png, unavailable-1280.png, unavailable-1600.png, capabilities-1280.png, capabilities-1600.png. Exact HTTP/header results: security-1280.json and security-1600.json.
- Initial three defect reproductions failed as expected before fixes. An initial expanded upload test had two Windows fixture setup/teardown errors because generated parameter IDs included large byte strings; explicit short IDs fixed the harness. Failure logs remain; no original data was repaired to satisfy tests. Existing Starlette/httpx, Vitest configuration and Playwright color warnings remain.
- Normal services were restarted only to load the patches; current frontend logs show loopback binding. The existing launcher then reused healthy services (launcher-reuse.log). Production infrastructure and a full browser/security penetration matrix remain untested.

## Preservation
All **10,266 original rows and schemas** match the existing strict baseline; **10,500 isolated rows** are unchanged, with zero appended rows. All **635 spatial artifacts**, **21 coupled native artifacts**, **55,296 original storage files** and **2,090 CAD/proof files** verify unchanged. All 264 baseline database schemas match; 263 older full database fingerprints are identical. The development DB's 27 historical additions predate this milestone and are all included in the strict current-row comparison. Conversations, usage, authorizations, audit events and saved revisions are preserved. See milestone-preservation.json, review-preservation.json, coupled-evidence-preservation.json and preservation-audit.json. No database copy or full-project backup was created.

## Remaining blockers, in priority order
1. Critical: remediate and qualify the applicable Windows Next dependency advisory before shared exposure. Loopback does not remove the vulnerable code.
2. High: provision/qualify real identity and strong server-side signing configuration; complete browser headers, HTTPS and trusted proxy/session policies.
3. High: qualify durable database/jobs/private storage and backup/restore, then review remaining runtime dependency/parser risks and Python advisories.
4. Medium: monitoring/alerting, resource-abuse/concurrency, revocation/recovery and broader browser/security coverage remain unverified.
5. Engineering: unsupported methods and unverified real-site/safety workflows remain blocked regardless of software health.

No Git operation, installation, deployment, paid inference, external AI agent, destructive cleanup or full-project backup. Numerical calculations were unchanged. Stop after Milestone 4.

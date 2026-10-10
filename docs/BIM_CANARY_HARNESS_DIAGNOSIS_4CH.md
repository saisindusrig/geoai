# GeoAI — Phase 4C-H: Offline Canary Execution Harness Diagnosis

The authorized Phase 4C UNDERSTAND canary stopped before the Nebius transport was invoked.

Observed:
- Actor/project: 490001
- Prepared run ID: 1
- Packet hash verification passed
- AssertionError occurred inside the one-request execution guard
- Paid requests: 0
- No provider response
- No valid checkpoint
- ModelRevision unchanged
- Durable ledger terminal
- Existing authorization/run must not be reused

## Objective

Identify and fix the pre-transport assertion without weakening the at-most-once execution guard.

NO PAID REQUESTS ARE AUTHORIZED.

### 1. Investigate the exact assertion

Inspect:
- Canary preparation script
- Canary execution script
- Durable request ledger
- One-request transport guard
- Run/checkpoint state transitions
- Phase 4B orchestration advance endpoint
- Existing recorded execution evidence

Reproduce the failure offline.

Capture the exact assertion, stack location, expected condition and actual state.

Do not guess the cause or replace assertions blindly.

### 2. Preserve the failed run

The existing terminal ledger and claimed authoring attempt must remain untouched.

Do not:
- Resume run 1
- Reset the request counter
- Reuse its authorization
- Delete the terminal ledger
- Replay an uncertain request
- Invoke Nebius

### 3. Correct request-state handling

Ensure the guard:

1. Validates the frozen source and packet.
2. Verifies the exact request and token limits.
3. Creates an exclusive durable request reservation.
4. Records sufficient state before external transport.
5. Dispatches at most one request.
6. Records safe response metadata.
7. Terminates without retries.

Distinguish demonstrable pre-transport failure from an outcome that becomes uncertain after dispatch.

A crash or timeout with uncertain transport outcome must never cause automatic replay.

### 4. Improve diagnostics

Replace opaque assertion failures at operational boundaries with explicit, safe error codes and diagnostic metadata.

Retain useful stack evidence locally without logging:
- API credentials
- Authorization headers
- Raw model responses
- Private reasoning
- Sensitive project data

Do not weaken security checks.

### 5. Mocked end-to-end tests

Using a fresh isolated test fixture and a fake provider transport, verify:

- Successful one-call execution
- Valid UNDERSTAND JSON/schema acceptance
- Truncated response handling
- Pre-transport guard failure
- Concurrent duplicate-action rejection
- Failure after durable reservation
- Uncertain transport outcome
- No replay after interruption
- Correct request accounting
- No unauthorized CAD Build or ModelRevision mutation

The mock must prove that exactly one outbound invocation occurs on the success path.

### 6. Regression verification

Run the relevant orchestration, authoring, approval, ownership, CAD and ModelRevision tests.

Report exact passed, failed and skipped counts.

### 7. Final report

Provide:

1. Exact assertion and root cause
2. Files changed
3. Before/after request-state transitions
4. Mocked success/failure results
5. At-most-once safety evidence
6. Regression results
7. Whether a completely fresh live canary can safely be prepared
8. Remaining uncertainties

STOP after offline verification.

Do not send any Nebius request.

Do not reuse the previous run or its authorization.

Do not change Qwen PRIMARY, output limits, timeout, BIM schemas or production CAD settings.

A new paid test requires separate explicit authorization.
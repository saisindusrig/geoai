# Manually activated Nebius acceptance — not executed

**No paid inference is authorized by this document.** Obtain the human's explicit approval of the model, maximum cumulative application-budget ceiling, number of turns and any retries before activating anything. Milestone 6.1 leaves inference disabled. Startup, Refresh availability, Read saved context and the model-catalogue GET do not request inference.

## Current readiness

`provider-readiness.json` confirms, without inference, that the backend resolver finds a credential, the official endpoint is configured, and the account catalogue contains `zai-org/GLM-5.3-Flash` and `zai-org/GLM-5.3`. The retained official API schema supports native tools, streamed usage, SSE, `max_tokens` and `reasoning_effort`. Actual completion behavior remains untested.

The **normal review process intentionally clears its key and keeps approval false**. Its truthful state is **Awaiting spending approval**, not a claim that the stored backend credential is missing. Do not place a key in the browser or edit credential files for this test.

## Approval and activation

1. Obtain explicit human permission. A possible approval scope is: **Flash only, up to three manually submitted turns, no automatic or unapproved retries, and a USD 0.05 cumulative application-budget ceiling**. This is an example, not permission. Check existing `/api/assistant/status` accounting first: the ceiling includes old estimates and retained reservations across users; it is not an increment or a provider invoice limit. If previous accounting consumes the ceiling, stop and request a new explicitly approved ceiling. Do not reset, delete, move, replace or lower old ledger entries to create headroom.
2. Preserve the existing local identity, original project revision and ledger. Use only this loopback environment; shared-user/Firebase/production qualification is outside this acceptance.
3. Stop **only the verified normal review backend process** on port 8001. Leave the tested local frontend and its existing same-origin proxy on port 3001. Do not start a second backend against an occupied port or use the historical $10 engineering-test launcher.
4. **Only after approval**, from `D:\layout project\backend`, manually run:

   ```powershell
   .\.venv\Scripts\python.exe scripts\serve_assistant_acceptance.py --human-approved-spending --budget-usd 0.05 --daily-tokens 200000
   ```

   Use the human-approved ceiling rather than blindly copying the example. The launcher refuses missing approval, non-finite/zero budgets, ceilings above USD 0.10, and token allowances outside 10,000–200,000. It starts no inference, binds only to 127.0.0.1, disables legacy guarded inference/provider chains and engineering-agent inference, and caps accepted turns at **three per user per rolling 24 hours**. The global spending ceiling still covers all users. The approval flag is an operator assertion, not a substitute for human permission. Existing environment/credential files and ledger entries are retained.
5. Refresh availability. Expect `AVAILABLE`, `configuration.credentialsConfigured=true`, `officialEndpoint=true`, no accounting-review flag and sufficient remaining allowance. This means a request may be attempted; it does not prove provider health. Keep the UI on **GLM-5.3-Flash**. Advanced selection requires separate approval and is not part of this example.

## Three manual acceptance turns

Stop after any failure, model mismatch, unexpected operation, questionable factual answer or accounting anomaly. Do not automatically retry, increase output limits, change models or raise the allowance.

| Turn | Manual request | Acceptance evidence |
|---|---|---|
| 1 — website help | “Where can I inspect saved analysis results without starting a new calculation?” | Genuine visible deltas arrive; response names an existing tool; no solver/file/model mutation or invented completed operation. No offline/template response. |
| 2 — authorized saved context | Open project 793 at saved revision 103, select CAD column SW through the existing inspector, and use Read saved context. Ask: “Describe this selected object's saved geometry and explain which saved evidence is current. Cite saved record IDs. Do not calculate, edit or approve anything.” | Captured project/revision/selection/document hash match the authorized read. Cross-check factual claims and IDs against the existing inspector/results. A source-linked answer is still engineering-unverified. Do not press Apply, Save, authorize a solver, import or export. |
| 3 — native read-only tool | “Use list_projects to list up to five projects I own. Do not make changes.” | A real allowlisted native call appears, its server result contains only owned project IDs, and the bounded verification response uses that result. The task records at most two completion attempts and no consequential operations. |

If the original project/revision is no longer accessible, stop rather than substituting another user's project or inventing evidence. The application may reject a continuation if its exact tool-result payload does not fit the remaining allowance; do not override that rejection.

## Errors, quota and cancellation

- After three accepted turns in the controlled process, one more **manual** submission should return local 429 before another catalogue/completion request. Verify no fourth task/completion was accepted. This local rejected attempt does not authorize a fourth paid turn. If fewer than three succeeded, do not manufacture paid failures to finish the checklist; use the mocked error evidence and report the live limitation.
- Quota, 429/503, incomplete SSE, missing/wrong model identity, invalid native arguments, timeouts, malformed/absent/contradictory usage, cancellation and retries are covered by automated mocks. Do not spend money deliberately provoking provider errors.
- Optional Stop response during an already-approved turn consumes that turn's attempt. It is best-effort cancellation, not a promise to stop provider billing. Unknown usage remains reserved; Refresh history manually to inspect INTERRUPTED/FAILED state. No extra attempt is implied or authorized.
- Missing/invalid usage retains the full per-completion reservation. Valid reported counts reconcile to an **estimate**, including reasoning in `completion_tokens` once. Conflicting usage is unknown. Out-of-bound usage or unconfirmed/wrong model identity blocks further inference for accounting review. Do not clear that flag or modify the ledger merely to continue testing.
- A manually clicked transport Retry reuses the request ID and reads an already-recorded task instead of replaying it. Retrying a terminal failure requires a new explicit request and consumes allowance; it needs permission within the agreed test scope.

## Evidence and shutdown

Record only sanitized task IDs, request hashes, requested and confirmed returned model IDs, timestamps/latency, number of completion requests, reported prompt/completion/reasoning usage, accounting state, reserved/estimated amounts and success/failure. **Actual charges remain unknown without provider billing evidence.** Do not export a raw HAR, bearer headers, keys or unrelated engineering data.

Compare original project/revision/input/authorization/evidence fingerprints with the existing preservation manifests. New assistant task/accounting records are expected only during a future approved test; do not rewrite earlier conversations or engineering rows.

Stop the controlled backend after the approved attempts, then restart the ordinary review backend:

```powershell
.\.venv\Scripts\python.exe scripts\serve_copilot_review_local.py
```

Refresh availability and confirm `AWAITING_SPENDING_APPROVAL` and `enabled=false`. Keep the ledger, including unknown reservations. Report the acceptance results and stop; this procedure does not authorize another milestone, Firebase operations, deployment or additional spending.

# Phase 4C UNDERSTAND canary execution

The explicitly authorized action was attempted against the prepared isolated actor/project 490001, run 1. It stopped on a harness assertion before the provider transport was invoked. No second action or replay was attempted.

Frozen source and regenerated packet verification passed before exclusive durable ledger creation. The packet hash is `b97ae64952b5699ffdf8e626459736845586b2e00f6c5734e12bbc6ab844f967`. The one-request guard then raised `AssertionError` before recording IN_FLIGHT or invoking the original transport. The ledger is terminal and prevents reuse. The specific assertion was not captured; no claim is made that Nebius failed, truncated or returned invalid output.

- Paid request count: **0**; retries: **0**.
- Actual provider token usage, reasoning-token count, finish reason and cost: unavailable; no response received.
- JSON and strict schema validation: not reached; no accepted UNDERSTAND checkpoint.
- Action latency: **0.025 seconds**; provider latency: unavailable.
- ModelRevision documents: unchanged; revision 1 hash remains `e3abf70ebf1d0ddd842c00df3106d4b0c2e464ef59713e82f145e5d788fdd8a8`.
- Proposals: **0**; approvals: **0**; CAD artifacts: **0**.
- PLAN continuation: none. Production/model configuration: unchanged.

Evidence: `backend/.cad-proof-output/4c-understand-canary-981cd96192534cfebc42a739366700b5/canary-execution.json`.

The isolated authoring run was advanced far enough to claim its attempt before the transport assertion. It must not be resumed under this authorization. The guard failure requires separate offline diagnosis before any further paid authorization. No conclusion about model JSON reliability or reasoning consumption is possible from this attempt.

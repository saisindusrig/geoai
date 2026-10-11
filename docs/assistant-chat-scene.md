# Project chat and scene investigation

Issue #3's 2026-10-11 recording observations are the reproduction brief. The
recording itself is not present among local attachments. It shows profile
refresh completing, but no submitted generation request. This change does not
claim to repair a failed request demonstrated by that recording.

## Chat

The project Assistant retains server conversation history, exact saved site
selection/profile identity and frozen submission retries. Its transcript scrolls
independently of the composer and inspector. Enter submits; Shift+Enter inserts
a newline; IME composition and concurrent submissions cannot submit duplicates.
Current site context and requirements remain compact, reviewable disclosures.
Proposal review, assumption acknowledgment, approval and Generate remain
separate existing server-authorized actions.

The persisted Assistant currently routes model-backed work through NebiusProvider,
not through the older generic provider selector. Previously a non-template
request in mock mode could reach that transport. Mock mode now fails closed with
AI_PROVIDER_UNAVAILABLE before any provider invocation; the saved turn explains
the limitation. The unchanged opt-in deterministic 5 x 3 m template is the only
inference-free proposal path. Settings show a provider setup link; this neither
enables a provider nor grants billing authorization. No fabricated chat replies
or token streaming are added.

For future free-form local chat, a separately tested AIProvider adapter is needed
for the persisted structured classifier/tool schemas, with strict tool validation
and existing server authority. Merely changing AI_PROVIDER=ollama does not route
this persisted Assistant to a local model. No adapter or paid-provider enablement
is included here. Qwen PRIMARY and ModelRouter remain unchanged.

## Scene investigation

Confirmed source-level hazards: the camera gizmo's negative Z action requests a
below-globe flight even without explicit underground mode; normal interactive
tilt had no maximum angle. Controller collision alone does not cover camera
flights and terrain becoming available asynchronously. Ordinary scene navigation
now uses a two-metre visual surface clearance, a bounded tilt and loaded globe
height (including exaggeration). It leaves terrain providers, model placement and
survey evidence untouched. Explicit underground inspection remains available;
negative Z is disabled until that mode is enabled. Fit project remains the
recovery action. Engineering lighting remains independent of time-of-day Sun
and Realistic presets; intentional darkness in those presets is not reclassified
as a provider outage.

The duplicate “Draw an alignment or generate a concept” banner is removed.
First-run coaching hides while drawing, when unsaved site geometry exists, and
when opening Assistant; dismissal persists for the project during the session.
Drawing tools, alerts and site actions remain accessible.

Tests cover token-free ellipsoid reference and, locally, the already configured
world-terrain connection. Configured-world acceptance requires the actual loaded
provider and a resolved nonzero terrain height, rather than treating token
presence as success. It disables trace capture to avoid recording credentials.
CI skips this one test without a separately supplied existing connection.
No tokens are committed or printed. Screenshots and measured camera state are
the evidence; absence of a permanent black frame in these tests does not prove
the exact intermittent recording defect has been reproduced or eliminated.

## Verification

Run normal frontend lint, Vitest, TypeScript and build plus backend tests.
Playwright includes assistant-chat-scene.spec.ts and the existing fresh website
platform flow through nine parts, slab editing, revision save/reload and history.
Optional local configured-world testing uses GEOAI_TEST_CONFIGURED_TERRAIN_URL
pointing at the owner's existing local API, only for its read-only map config.
Do not supply production account resources or AI credentials.

The owner's five uncommitted UI files remain in the original checkout; this work
uses an isolated branch. No paid AI, native CAD enablement, approval bypass,
deployment or merge is part of this change.

# Offline website platform demo

This is an explicitly enabled deterministic template, not live AI authoring.
It uses the existing Assistant orchestration, strict AI3DDesign validation,
ProposalService, approval and generic 3D executor. Native CAD and BIM authoring
remain disabled; production model routing is unchanged.

For a local development API, set `AI_PROVIDER=mock`,
`GEOAI_OFFLINE_PLATFORM_DEMO=true`, `ENVIRONMENT=development`.
The template flag defaults to false and is ineffective for production or other
providers. No Nebius credential is required or used by the template path.

In an ordinary project workspace:

1. Draw and save a site boundary, then open Assistant and choose Refresh site.
2. Wait for the current site profile. The Assistant displays
   **Offline demo · supported platform template**.
3. Choose Use platform example or type:
   “Create a 5 m × 3 m industrial maintenance platform with columns, beams and a
   slab. Deck top around 3 m high.”
4. Review the persisted proposal, dimensions, unknowns and preview assumptions.
   Acknowledge those assumptions and explicitly approve the proposal.
5. Use the existing Generate 3D action. Reload the workspace to see the nine
   conceptual components, then select/edit and save a new 3D model revision.
   History comparison and reload use the ordinary persisted model workflow.

Only this narrow platform template is supported. Other dimensions, added
features or unspecified dimensions receive an explanation without a substitute
proposal. Unrelated Assistant requests retain their existing behavior.
Sending a message reads the saved site version and preserves its profile pair;
it does not create a new selection. A changed site must be saved and refreshed.
Server ownership, current-context and proposal validation still apply.

Placement uses the approximate saved-site local frame. Deck top is local visual
Z=3 m. Ground elevation remains null/UNKNOWN. Column/beam/slab sizes are visual
placeholders. Loads, foundations, clearances, structural adequacy and code
compliance remain unverified. Approval does not certify engineering safety.

CI enables the template only for the isolated mock E2E database. The fresh
website test draws/saves a boundary, refreshes a profile and submits the normal
Assistant message before reusing review, approval, Cesium selection, editing,
save/reload and comparison assertions at 1440/1920 pixels. The old seeded
fixture acceptance continues to run independently.

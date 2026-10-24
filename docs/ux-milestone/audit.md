# GeoAI local UX audit — 14 October 2026

Browser observations before implementation: projects 793 (unequal CAD frame), 789 (drawing practice review), and 784 (slab transfer). Initial inspection at 1280 × 720; Analysis inspected at 1600 × 900. Screenshots in this directory are actual browser captures.

## Priority 1 — model visibility and camera

- All three workspaces start at neighborhood scale. A few metres of model geometry are effectively invisible; Length, Width and Deck height labels overlap in the centre of the site. A beginner cannot distinguish a model from a site boundary.
- Selection from Layers works, but Frame selection does not produce a useful close inspection in the observed terrain view. The standalone /model page has generic layer transparency sliders and terrain rather than the semantic editing workflow.
- Fix in this milestone: a distinct Model presentation view with isolated background and close framing; keep Site view and accepted placement intact. Never change engineering coordinates to improve appearance.

## Priority 1 — workspace hierarchy

- Assistant opens by default and occupies 300 px at 1280 px. Layers opens over its position. Selection adds a 208 px text panel at left, competing with both model and inspector.
- Tool icons are available but labels are mostly hidden in tooltips. The small vertical Save icon competes with the header's unrelated Save site geometry action.
- Fix: viewport first; one visible side panel at a time; explicit workflow and save actions; concise selection bar and readable inspector.

## Priority 1 — engineering discoverability

- In 784, Analysis initially expands the collection of existing tools and a foundation input form before the saved slab solver result. Numerous inputs and warnings obscure the useful diagram actions farther down.
- 789 displays a temporary Failed to fetch message while CAD evidence loads. Saved review controls eventually need a clear retry rather than silent recovery.
- Fix: grouped collapsible analysis sections, preserve authorization controls, and keep saved numerical results and evidence reachable. No change to calculations.

## Priority 2 — inspector and appearance

- Inspect starts with identifiers and editing fields instead of an object summary. Material name/color appear together under Material, which can be confused with engineering declarations.
- CAD, conceptual platform and attachments lack an easily understood appearance legend. Selected labels stack with dimensions at distant zoom.
- Fix: name, role, geometry, dimensions/units, explicit appearance-only status, fit/edit actions; IDs and provenance collapsed. Lit surfaces, edge accents, clear selection and distance-limited labels.

## Priority 2 — assistant expectations

- Assistant advertises Nebius budget-controlled cloud regardless of the adjacent offline fixed-template availability. Empty state asks what to build but offers no workspace navigation.
- Fix: provider-independent engineering tools label and useful local navigation actions. Do not send inference during validation.

## Remaining outside this focused milestone

- Standalone legacy /model route needs convergence with the main workspace.
- Full beginner onboarding, all analysis forms' terminology, generated UUID-heavy names, and every import/provider failure are broader work.
- Usability findings are observed by the agent; comprehension by an independent beginner cannot be certified without user testing.

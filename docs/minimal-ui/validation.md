# GeoAI minimal UI milestone — local review

Review: http://localhost:3001/projects/788/workspace

## Outcome

1. **Understand the blocker — improved.** The Assistant now begins with its name, actual offline saved-data status and selected component name. The foundation answer explains missing anchor/contact data in two sentences, followed by one main action. Model preferences and technical identifiers are inside Settings, Details or Message context.
2. **Start the next task — improved.** The default conversation no longer displays 233 requirements. Review required inputs opens the exact saved connection input and its geometry-source prerequisite. Eight tasks separate geometry, contact, four anchors, assumptions and validation. Each screen shows one logical input step, units and its source requirements. Navigation does not mark requirements complete or invent values. The complete 233-row assessment remains available under Advanced requirements.
3. **Understand analysis — improved.** The default Analysis view shows the selected component/system, status, stored results with units or the blocker, and one main action. All existing forms, calculations, source references, solver logs and authorization tools remain under Advanced analysis. Saving a connection-input draft refreshes the overview from saved data; the authorization logic is unchanged.
4. **Inspect the model — improved.** Fit Model and Fit Selection use the viewport aspect ratio and camera field of view. Initial framing also recognizes project changes at the same geographic origin. Appearance, geometry, coordinates, material declarations and editing tools are retained. Dimensions remain off by default. Assistant resizing was exercised from 420 to 500 px and restored.
5. **Inspect evidence — retained.** Exact saved diagrams, CAD identities, complete original message text, actual producer/model metadata and technical evidence remain accessible on demand. Numerical verification is explicitly distinguished from structural design approval. Blocked and stale states never become PASS.

Fresh baseline audit: [audit.md](audit.md). Screenshots were captured through the actual local browser and individually inspected. No generated UI mockups are used.

## Browser acceptance

All four projects were exercised at **1280 × 900 and 1600 × 900**. These are developer walkthroughs using the visible controls, not an independent novice-user study.

| Project | Actual observations and checks |
| --- | --- |
| 788 | Existing conversation restored after reload. Plain-English anchor/contact blocker; one Review required inputs action. Exact input #354/revision 93 opens geometry-source screen. Next task moves to concrete; Anchor 2 opens its own material/source/load-path/diameter steps; diameter remains explicitly metres. Keyboard focus follows the step heading or requested input. Advanced requirements exposes all 233 rows and prerequisite/source explanations. Validate and authorize remains BLOCKED_MISSING_ENGINEERING_INPUTS; consent and Run are disabled. No draft, consent or solver action submitted. |
| 793 | Existing column, load-case, stale-context and bending-moment messages remain readable. Preferences are hidden until Settings opens and explicitly say no inference. Stored Horizontal, Gravity and Self weight references retained. Open saved results navigates to the existing physical-frame results. View saved diagram displays the existing bending diagram, OpenSees 3.8.0 and -28.809726 to 24.756664 kN·m. Collapsing Advanced leaves the concise overview. |
| 784 | Existing slab message shows 5 kN/m² over 24 m², 120 kN total and the one-way limitation. Overview retains -28.271072 to 22.694564 kN·m. Existing saved analysis #301 opens its bending diagram. Composer remains within the 1280 px viewport. |
| 789 | Existing six-component CAD explanation and history retained. Inspect drawing sources opens the original drawing workflow. Selecting CAD column SW selects its outline/handle 9C, preserves stable identity dxf:614f117ae2a74794:9C and enables Fit Selection. Assistant header updates to CAD column SW. Analysis labels it Geometry only and does not imply verified section, load or material properties. Existing mapping authorization restrictions remain present. |

Model navigation and selection did not dirty the model; Save model, Undo and Redo remained disabled when there were no edits. This milestone did not save original geometry or rerun calculations. Undo/redo behavior is covered by existing frontend regression tests; no new destructive browser edit was needed for these presentation changes.

## Before / after screenshots

Comparable conversation states at each requested width:

| Project / width | Before | After |
| --- | --- | --- |
| 788 / 1280 | [Before](before-788-chat-1280.jpg) | [After](after-788-chat-1280.jpg) |
| 788 / 1600 | [Before](before-788-chat-1600.jpg) | [After](after-788-chat-1600.jpg) |
| 793 / 1280 | [Before](before-793-chat-1280.jpg) | [After](after-793-chat-1280.jpg) |
| 793 / 1600 | [Before](before-793-chat-1600.jpg) | [After](after-793-chat-1600.jpg) |
| 784 / 1280 | [Before](before-784-chat-1280.jpg) | [After](after-784-chat-1280.jpg) |
| 784 / 1600 | [Before](before-784-chat-1600.jpg) | [After](after-784-chat-1600.jpg) |
| 789 / 1280 | [Before](before-789-chat-1280.jpg) | [After](after-789-chat-1280.jpg) |
| 789 / 1600 | [Before](before-789-chat-1600.jpg) | [After](after-789-chat-1600.jpg) |

Additional interaction evidence:

- Blocked Analysis: [before 1280](before-788-analysis-1280.jpg), [after 1280](after-788-analysis-1280.jpg), [after 1600](after-788-analysis-1600.jpg).
- Compact source task: [1280](after-788-geometry-task-1280.jpg), [1600](after-788-geometry-task-1600.jpg).
- [Blocked authorization](after-788-authorization-1600.jpg).
- [Frame bending diagram](after-793-diagram-1280.jpg), [concise frame overview](after-793-analysis-1600.jpg).
- [Slab overview](after-784-analysis-1280.jpg), [slab diagram](after-784-diagram-1600.jpg).
- [Selected CAD column and source](after-789-selected-column-1600.jpg), [geometry-only overview](after-789-analysis-1600.jpg), [expanded source workflow at 1280](after-789-analysis-1280.jpg).

Camera framing and panel width differ in some captures because Fit/resize were explicitly tested; screenshots compare content hierarchy and readability, not pixel-identical camera positions.

## Automated verification

- TypeScript: `tsc --noEmit` passed.
- Targeted ESLint: passed; [log](lint.log), [final status-change lint](final-status-lint.log).
- **61 tests passed across 14 frontend test files**: conversation persistence/context/recovery, proposal handling, physical-frame navigation, exact connection-input navigation, Analysis overview, presentation safety/units, camera framing, API transport, panel resize cleanup, viewport arbitration, transforms, analysis and component identity. [Regression log](regression-tests.log).
- After adding saved-input overview refresh, **3 affected tests passed**; includes project-scoped refresh isolation. [Final affected tests](final-status-tests.log).
- No backend methods, schemas, numerical algorithms, provider credentials, inference gates or budget settings changed. No paid inference calls, installations, commits, GitHub operations or deployment.

## Preservation evidence

Read-only SQLite snapshots were taken before and after browser acceptance. Every row in the following tables has an identical SHA-256 digest, not just an equal count:

| Table | Unchanged rows |
| --- | ---: |
| projects | 274 |
| model_revisions | 117 |
| engineering_analyses | 509 |
| engineering_audit_events | 98 |
| conversation_messages | 154 |
| project_conversations | 119 |
| usage_events | 1936 |

[Baseline](baseline.json) and [comparison](preservation.json). Existing source mappings and engineering evidence embedded in saved revisions/analyses are unchanged. Browser checks read existing conversation records; they did not add test messages or alter original projects.

## Remaining limitations

- Chat is deterministic offline saved-evidence guidance. No Nebius reasoning was tested or enabled. Arbitrary questions retain the existing supported-intent limits; historical responses remain stored unchanged, including earlier unhelpful messages.
- The compact step screens cover the existing physical foundation-connection input workflow. Other specialist engineering forms and CAD authoring controls remain in their original detailed form under Advanced analysis; they can still be dense when explicitly opened.
- Providing sourced inputs and engineering judgment is still substantial work. Task order is guidance, not a safety ranking; step counts do not mean validated completion.
- Small legacy toolbar text, nested specialist disclosures, fit-camera orientation and nearby geometry occluding a tightly fitted member can still require user navigation. No rendering or geometry rewrite was attempted.
- This was an agent walkthrough, not a human usability study or a full accessibility certification. No new solver execution, original-project save, mobile acceptance or paid-model evaluation was performed.

Stopped at this local UI milestone for review.

# Reviewed CAD drawing to parametric 3D — local review

Local website: http://localhost:3001/projects/789/workspace. Open Analysis → Reviewed drawing → parametric 3D → Fit generated CAD model. The original 73-entity DXF plan is displayed beside the editable geometry. All data is SYNTHETIC VERIFICATION, not a real construction project.

## Implemented scope

Explicit source selection, structural role, six geometry dimensions/elevations in millimetres, material identity and source, geometry source, connectivity declaration and reviewer attribution. Rectangular axis-aligned column, beam, slab and footing outlines are supported. Unsupported source circles, base plates, stairs, text and arbitrary shapes remain blocked. No section, elevation, material property or structural joint is inferred from plan outlines.

Five explicitly entered attachment points are bounded inside both connected envelopes. This verifies geometric consistency only, not physical connection capacity or analytical joint behavior. A user may instead explicitly declare isolated geometry with analysis blocked.

The immutable preview records link exact saved model revision, original drawing bytes/source record, unchanged corrections and explicit inputs. Approval applies the exact candidate to an undoable draft. The existing Save action creates a new model revision. Server-side checks reject forged/stale approvals and unapproved CAD-derived geometry edits, including attempts through the ordinary revision endpoint. Use Edit generated mapping for subsequent supervised changes. Existing context members are preserved and temporarily hidden only when framing CAD components.

## Independent geometry evidence

Initial entered column envelope: 300 × 300 × 3200 mm → 0.3 × 0.3 × 3.2 m; SW centre (0.15, 0.15, 1.6) m. Beam: 6000 × 200 × 300 mm, centre (3, 0.15, 3.25) m. Slab: 6000 × 4000 × 200 mm, centre (3, 2, 3.5) m. Footings: 1200 × 1200 × 450 mm, underside −0.45 m, top zero, centre Z −0.225 m. These are entered verification values, never material or structural design defaults.

Decimal arithmetic independently verifies mm/1000 conversion, sizeZ=(top−bottom)/1000 and centreZ=(top+bottom)/2000. Editing the SW column top to 3260 mm produces height 3.26 m and centre Z 1.63 m; stable identity is retained. Revision 97 contains the six initial mappings, revision 98 contains the one column edit. Comparing 97/98 reports 0 added, 0 removed, 1 modified; the other 50 components are unchanged.

## Verification

281 backend tests passed across the new geometry workflow, drawing review, versioned strength architecture, existing contact/interface methods and local OpenSees frame benchmarks. Includes missing-input blocking, unsupported entities, duplicate sources, unit conversions, update identity, independent arithmetic, explicit deviations, attachment references, original protection, approval bypass, source-byte changes, review changes and JavaScript number normalization. Existing solver methods were not changed.

Browser edit workflow passed on localhost:3001: explicit selection/input, blocked incomplete attachments, preview, exact authorization, undo/redo, save/reload, stable identity and revision comparison. Final read-only viewport picking and side-by-side responsive review are recorded in screenshots. TypeScript and targeted ESLint checks passed. Source-change tests use isolated databases/files; the live drawing and review are never changed.

Preservation snapshot checked 9,714 existing database rows: zero missing rows and zero unintended changed rows. Only project 789 update timestamp and scenario 577 current design-output pointer changed through authorized revision saves. All historical model/evidence rows, original 45 components and DXF SHA256 are unchanged. Zero new live inference calls. Original private source SHA256: 614f117ae2a74794b128ea983f99f10ed9898a069882666bcdb60ee1a2934e18.

## Limitations

Generated boxes are editable nominal geometry envelopes, not verified engineering sections. Loads, material E/fy/grades, supports, section A/I, joint stiffness, connection details, reinforcement and geotechnical properties remain missing. No FEA is automatically run. No structural adequacy or code approval is enabled. Curved, inclined or arbitrary outlines, openings, anchors, stairs and base plates are outside this milestone. Manual CAD-derived edits outside the mapping workflow cannot be saved without an exact reviewed authorization. Restoring historical CAD geometry requires a fresh supervised mapping/approval rather than bypassing the gate.

STOPPED for review. No GitHub, commits, deployment, installations or paid AI inference.

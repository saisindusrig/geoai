# CAD structure → foundation → soil review

Local website: http://localhost:3001/projects/796/workspace · Analysis. Separate copy of project 794 revision 105; copy revision 110. All 54 components are unchanged. Original solver results, DXF files, source corrections and revisions remain intact.

Completed scope: read all four actual OpenSees column-base demands from project 794 analysis #431; preserve column, beam, source node, model revision and solver run identities; explicitly review reaction-to-footing identities; audit missing source geometry and engineering inputs; run one authorized independently checked synthetic rigid-footing bearing method. Actual foundation/soil analysis remains BLOCKED.

Actual saved source demands (N is compression, V is East, M is about analytical -North):
- CAD column SW · drawing-cad:614f117ae2a74794:9C: N=29.953701030 kN; V=9.961989189 kN; M=-10.857803904 kN·m. Base ENU=[0.15, 0.15, 0.0] m. Source beam drawing-cad:614f117ae2a74794:96, retained node 1.
  Observed saved footings: ['drawing-cad:614f117ae2a74794:9A']; DXF outline handles: ['9A']. Proximity is not a structural connection.
- CAD column SE · drawing-cad:614f117ae2a74794:AE: N=30.046298970 kN; V=-9.961989189 kN; M=10.593899776 kN·m. Base ENU=[5.85, 0.15, 0.0] m. Source beam drawing-cad:614f117ae2a74794:96, retained node 4.
  Observed saved footings: ['drawing-cad:614f117ae2a74794:AC']; DXF outline handles: ['AC']. Proximity is not a structural connection.
- CAD column NW · drawing-cad:614f117ae2a74794:A5: N=29.953701030 kN; V=9.961989189 kN; M=-10.857803904 kN·m. Base ENU=[0.15, 3.85, 0.0] m. Source beam drawing-cad:614f117ae2a74794:97, retained node 1.
  Observed saved footings: []; DXF outline handles: ['A3']. Proximity is not a structural connection.
- CAD column NE · drawing-cad:614f117ae2a74794:B7: N=30.046298970 kN; V=-9.961989189 kN; M=10.593899776 kN·m. Base ENU=[5.85, 3.85, 0.0] m. Source beam drawing-cad:614f117ae2a74794:97, retained node 4.
  Observed saved footings: []; DXF outline handles: ['B5']. Proximity is not a structural connection.

The two south CAD footing outlines are 1.2×1.2×0.45 m at centre Up=-0.225 m (top 0, bottom -0.45 m). They are synthetic unverified geometric outlines, not engineered concrete supports. The two north CAD footings are absent from saved geometry, although original DXF FOOTINGS_CONCEPT outlines A3/B5 are present. Their depth, reference elevations, concrete properties and load path are not inferred. Existing supervised CAD entity mapping/preview/authorization can create reviewed foundation outlines if those inputs are supplied; this milestone creates none.

Explicit stable mappings can link south columns to their saved footing identities; north mapping stays missing/BLOCKED. Review sources and acknowledgments are saved as immutable engineering evidence. Wrong/unknown/duplicate identities and unsupported offset mappings are rejected. Mapping does not establish physical shear or moment resistance.

Required actual data: reviewed footing dimensions/source and geometry consistent with saved outlines; contact/reference elevations; sourced concrete properties and strength basis/applicability; reinforcement information; sourced geotechnical bearing/contact assumptions and applicability; supported physical column/base-plate/footing connections and moment/shear transfer. The new review controls record optional concrete, soil-bearing and contact-elevation declarations with MEASURED, MANUFACTURER_DATA, ENGINEER_DECLARED, SYNTHETIC_VERIFICATION or UNVERIFIED classification. Any entered numerical property requires its source. Entered assumptions never enable actual pressure or safety approval.

Reference-only eccentricities at the column-base plane are approximately -0.362486 m (west) and +0.352586 m (east). Both exceed the nominal 1.2 m outline kern B/6=0.2 m. The interface labels this as a nominal outline warning, not an actual soil pressure/contact conclusion. Moving shear to the soil contact plane would introduce an additional r×V moment; that physical transfer and elevation model are unverified. No actual pressure is calculated and no anchor or moment resistance is invented.

Independently verified synthetic footing method:
- Rigid rectangular B=L=2 m, gross full contact, compression N=200 kN: A=4 m²; q=N/A=50 kPa.
- M=+40 kN·m: e=M/N=0.2 m, kern=B/6=0.333333 m; S=LB²/6=1.333333 m³; q=N/A±M/S=50±30=20–80 kPa.
- Reversed moment swaps the pressure edges; half N/M gives 10–40 kPa with unchanged eccentricity.
- M=80 kN·m gives e=0.4 m outside kern: contact loss detected and partial-contact pressure withheld.
- M=200.001 kN·m places the resultant outside the 1 m half-width: compression-only equilibrium impossible, pressure withheld.
- Kern-boundary zero pressure, invalid/negative compression or dimensions and nonfinite values are tested.

Mechanics reuses the already validated nominal rigid-contact law. Independent Decimal hand calculations use kN, kN·m, metres → kPa, separately compare N/mm² dimensional conversion, and verify pressure-integrated N/M by exact Gauss quadrature. Pressure is compression-only and nonnegative for supported full-contact cases. No plate flexibility, footing self-weight, shear resistance, biaxial contact, anchor force, partial-contact distribution, reinforcement, soil stiffness, soil capacity or settlement is calculated.

The synthetic benchmark is expressly authorized against the exact saved review hash. It is not an actual-project footing or soil solution. No new OpenSees run is needed or represented: actual reaction provenance points to the existing two OpenSees 3.8.0 runs in analysis #431, whose full-slab force/moment equilibrium remains preserved. Independent source equilibrium and run IDs are in numerical-evidence.json.

Staleness and authorization: model hashes, all participating CAD slab/frame geometry, drawing source bytes and source/review record hashes, original structural result identity and current source status are checked. A newer identity review makes earlier benchmark evidence stale; changed or forged review authorization is rejected. Draft review edits label prior results stale; reload restores saved state. Original model undo/redo and CAD supervised editing are preserved; this milestone makes no model geometry changes.

Tests: 376-test engineering regression suite passed; 33 final targeted authorization/bearing/source-input tests passed after the sourced-input extension (four additional cases). Browser workflow tests actual four-demand mapping, missing footings, wrong/duplicate identities, missing engineering sources, exact benchmark authorization, forged hash rejection, contact-loss outputs, stale draft, saved reload and responsive 1280 px layout; no page errors. TypeScript and targeted ESLint passed. The local frontend port conflict was resolved by restarting the existing frontend on port 3001.

Preservation: 9,836 pre-existing database rows checked against a before-milestone SQLite backup; zero changed or missing. All 54 copied component bodies match project 794 revision 105, and the review copy has one model revision. Drawing bytes are identical in source/copy projects. Zero new paid inference calls. No GitHub, commits, deployment or installations.

Unsupported actual foundation/soil analysis remains BLOCKED wherever geometry, properties or load path are absent. No whole-building analysis, foundation capacity, physical connection strength, IS/US compliance or structural safety approval is enabled. Engineering approval remains DISABLED.

STOP for review.

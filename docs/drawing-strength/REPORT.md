# Drawing review and verified nominal steel tension — local milestone review

Local drawing workflow: **http://localhost:3001/projects/789/workspace**.

Local steel-method workflow: **http://localhost:3001/projects/790/workspace**.

Open **Analysis**. Both are separate review copies. The saved 45-component 3D contexts were copied from project 788, revision 93; **they were not generated from the uploaded drawing**. Original projects and calculations are preserved.

## Source classification and genuine-project limitation

The supplied ZIP contains a text DXF plan and two-sheet PDF practice set. Both explicitly identify synthetic training geometry, not construction information. The application rejects an attempted REAL_PROJECT classification for this source. **No genuine construction drawing was supplied or tested.** The import/review workflow is implemented, but a real-project analytical model remains blocked until an appropriate source drawing and supported engineering inputs are supplied.

The PDF was manually inspected with text extraction and rendered-page review using the existing bundled PDF tools. Its bytes are preserved in `sources/`; it is not automatically converted into structural geometry. Instructions or warnings inside documents were treated as source content, not authorization to perform extra development.

## Track A — working drawing-reference review

- Bounded text **DXF** reference import using the already-installed ezdxf runtime and existing application evidence/revision architecture. Explicit mm or m INSUNITS are required; unitless, binary/invalid, out-of-plane and unsupported formats fail clearly.
- Exact source bytes and SHA256, stable file-hash/DXF-handle identities, layers, original native coordinates, converted metre coordinates, dimensions and annotations are retained. Original source can be downloaded through an owned-project endpoint; browser testing confirmed byte-for-byte hash equality.
- The imported practice plan contains **73 entities**: 18 LWPOLYLINE outlines, 30 LINE entities, 16 reference CIRCLE entities and 9 TEXT annotations. Unsupported entities remain in the original file and are separately reported; curved polylines and transformed entity planes are not silently straightened.
- Independent unit check: source slab plan **6000 × 4000 mm**, converted using ×0.001 to **6 × 4 m**. All extracted material fields remain **null**. Drawing circles are reference marks, not physical bolts or effective tensile areas.
- Engineer/user review can correct labels, declare roles, record plan dimensions and material descriptions, retain source/sheet references and reasons, and explicitly associate a source identity with an existing saved component. The source remains unchanged; corrections are separately versioned evidence. No mapping or connection is inferred from touching outlines.
- Final drawing reference **357**, model revision **96**, review record **365**. The synthetic SL-01 review retains nominal 6000 × 4000 mm dimensions, leaves material blank, and explicitly maps the source reference to the separate saved conceptual deck. This is a review association, not certification or automatic 3D publication.
- The Analysis workspace shows source linework, dimension annotations and declared anchor locations on a clearly labeled local drawing plane. Camera framing uses imported bounds. Display Z=0 is a drawing-plane convention, **not a structural elevation**. The separate saved context is temporarily hidden and can be restored.

The analytical candidate record remains **BLOCKED_MISSING_SUPPORTED_3D_ENGINEERING_INPUTS**, with **zero fabricated nodes or members**. Missing: reviewed 3D centerlines/elevations and orientation, structural sections and A/I, elastic materials, load cases, supports, joints, connections, reinforcement, foundation behavior, soil data, surveyed datum and adopted code editions. Nominal geometry in a practice schedule does not replace these inputs.

### Audited capabilities and exclusions

- Existing survey DXF endpoint was tested locally and returned **HTTP 503**, requiring PostgreSQL/PostGIS. It handles LINE/LWPOLYLINE/POLYLINE as geospatial linework, lacks structural semantics and does not reliably normalize this local millimetre drawing. Its behavior was preserved; no database/service installation was performed.
- New local reference mode works with SQLite and retains explicit units and source identity. It is **not survey-grade ingestion or automatic structural-model generation**.
- IFC file-to-structural-model import: **NOT IMPLEMENTED / NOT VERIFIED**. Existing experimental BIM/CAD representations are not proof of IFC-file ingestion.
- DWG: **NOT IMPLEMENTED**; no converter installed or remote service used.
- PDF automatic geometry extraction, OCR and drawing-to-structure import: **NOT IMPLEMENTED**. Local manual PDF inspection and text source references do not establish such capability.
- Existing GeoJSON/site tools and saved 3D geometry/revision workflows were not replaced. No arbitrary BIM, slab/shell FEA or whole-building analysis was added.

## Track B — verified single nominal anchor-steel term

The only enabled method is **US/ACI318-19-INLB/anchor-steel-nominal-tension@1**, implementation **1.0.0**, representing the nominal steel term of [ACI 318-19 §17.6.1.2, original IN-LB edition](https://www.ocf.berkeley.edu/~chiep/wp-content/uploads/2024/01/CE-123-ACI-318-19.pdf). It uses supplied effective tensile area and reported material strengths, with the edition's strength limits. The UI explicitly identifies the edition and all excluded checks.

Synthetic benchmark:

- Effective tensile area **245 mm²**; fy **400 MPa**; fu **600 MPa**. These are explicit synthetic verification inputs, not properties extracted from the drawing or a real manufacturer certificate.
- futa_used = min(600, 1.9×400, 125000 psi converted to MPa) = **600 MPa**.
- Nsa = 245 mm² × 600 N/mm² = **147000 N = 147.000000 kN**.
- Independent IN-LB calculation uses A = 245 / 25.4² in² and converted stress, then converts lbf to N using **4.4482216152605 N/lbf**. It matches the SI result within numerical tolerance; Decimal hand evidence is stored separately.
- Yield-limit test: fy **250 MPa**, reported fu **600 MPa** → used fu **475 MPa**, Nsa **116.375 kN**.
- Edition-cap test: fy **600 MPa**, reported fu **1000 MPa** → original IN-LB cap **861.844661646 MPa**, Nsa **211.151942103 kN**. This is the conversion of 125000 psi; the application does not silently substitute the different native-SI edition's rounded cap.
- Area scaling, units, source requirements, unsupported editions/countries, unverified inputs, synthetic-to-real promotion, scope and arbitrary-argument rejection are tested.

Final proposal **368**, result **369**, model revision **95**, status **VERIFIED_NOMINAL_STEEL_TERM_ONLY**. The source link points to drawing project 789, reference 357 and circle handle **9D**. That is a traceable reference identity only: **the circle is not a verified bolt and does not supply tensile area or material properties**.

Explicit exact-proposal authorization is required to publish the numerical result. Evidence pins model/source hashes, linked drawing review, method descriptor and implementation hashes, input snapshot, independent calculation, canonical source references and authorization attribution. Changed input/material/source review/model/method makes old results stale. Input/result payloads are not overwritten by recalculation.

**Not enabled:** phi/design strength, factored demand utilization or pass/fail; concrete breakout, pullout, bond, shear/interaction; physical anchor-group capacity, plate bending/prying, welds, reinforcement, footing or soil checks. Nominal steel Nsa is not full connection capacity and is not a computed OpenSees force. **Engineering approval remains DISABLED.**

Indian IS 800:2007 and American AISC 360-22 entries are separate **NOT_IMPLEMENTED** registry branches. Unsupported country/edition/method selections fail closed; the ACI expression is never substituted for an Indian or AISC method. Jurisdiction, amendments/errata, applicability and independent verification must precede future adapter release. See `ARCHITECTURE.md` for the staged separation of source review, FEA demands and design checks.

## Local verification and preservation

- **250 unique backend tests passed**: 37 new drawing/steel tests plus 213 preserved engineering-input, contact, slab-transfer, gravity, eccentric and beam/frame tests. Existing local OpenSees was used for FEA regressions; its methods were not changed. An existing Starlette dependency deprecation warning remains, with no dependency installation or upgrade.
- **Three browser workflows passed**: the combined import/review/steel/authorization flow; final saved-state/responsive review; and read-only original project 787 3D pressure/rotation regression. No runtime browser errors were recorded.
- Browser checks cover synthetic promotion rejection (422), exact source-download hash, correction reload, four-state model preview/apply/undo/redo, revision staleness, unsupported IS request (422), forged authorization (409), linked drawing-review staleness (409), independent limit-case result, renewed exact authorization and save/reload. Desktop layouts checked at 1600×1000 and 1280×820 without horizontal overflow.
- TypeScript and ESLint pass for changed UI and test files.
- Database comparison across **62 tables / 9,681 pre-existing rows**: **zero changed, zero missing**. Both review copies preserve all **45 original component objects and origin coordinates** exactly. Original revisions, solver calculations, source evidence and all 22 prior inference usage records are unchanged.
- Uploaded ZIP contents, copied PDF/DXF and privately stored DXF were hash-verified. **Zero paid inference calls, no Git/GitHub operations, commits or deployment.**

Artifacts: `independent-evidence.json`, `browser-evidence.json`, `preservation-evidence.json`, `import-audit.json`, `test-results.json`, and `screenshots/`.

Stopped for review. This is a working source-review workflow and one verified synthetic nominal steel term, **not a completed real-construction analysis**. A genuine project drawing and explicit supported engineering inputs must be provided before that claim is possible.

# Saved slab-to-beam load transfer — local review

Open [project 784](http://localhost:3001/projects/784/workspace), then **Analysis**. Current numerical evidence is analysis **301**, saved model revision **86**. This separate review copy retains all 45 component objects and the origin from original project 768, revision 59.

The saved slab `industrial-platform-5x3:platform-deck` is **6 × 4 × 0.2 m**. North and south support beam centerlines are **3.7 m** apart, with equal **0.15 m** slab edge overhangs. The supported method is uniform, symmetric one-way tributary allocation to two simple vertical support lines. Slab support moment/torsion is excluded. Four beam-column rigid arms retain their actual **[±0.15, +0.10] m** East/Up offsets. No saved geometry was moved to create connectivity.

The review explicitly excludes the east/west transverse edge beams from slab sharing and all **22 attached stair parts** and their transmitted loads. Braces, connections, foundations and other project parts remain visible but are excluded from the two independent planar frame solves. Their presence does not establish capacity or whole-platform stiffness.

## Synthetic inputs and calculation evidence

The fixture uses imposed downward pressure **p = 5 kN/m²**, with slab/member self-weight excluded. Material and sections are explicit synthetic assumptions: **E = 200 GPa**, saved solid rectangular beam **A = 0.06 m², I = 0.0002 m⁴**, column **A = 0.09 m², I = 0.000675 m⁴**, fixed column bases, and approved massless rigid beam-column arms. These values do not certify the physical steel sections, joints or foundations. The UI keeps all idealization approval boxes unchecked when loading the fixture.

- Slab area: **A = 6 × 4 = 24 m²**.
- Tributary width per beam: **b = 3.7/2 + 0.15 = 2 m**; area **6 × 2 = 12 m²**.
- Equivalent downward beam load: **q = p × b = 10 kN/m**.
- Transferred load: **2 × q × 6 = 120 kN = p × A**; transfer error **0 kN**.

Actual local **OpenSees 3.8.0** runs on both saved frames give **30 kN vertical reaction per column base**, **120 kN total**, with total vertical balance error **−2.8422 × 10⁻¹⁴ kN**. Each beam has sampled bending moment range **−28.271072 to +16.728928 kN·m**, shear **−30 to +30 kN**, and midpoint vertical displacement **−1.024137 mm**. Left support horizontal reaction is **+10.765081 kN**, left support moment **−11.753694 kN·m**; the right support has opposite horizontal force and moment. Displacements and internal force diagrams map to the saved component IDs.

A separate real fixed-fixed beam example with the same **L = 6 m, w = −10,000 N/m, E and I** verifies **Ry = −wL/2 = 30 kN**, fixed-end moment magnitude **wL²/12 = 30 kN·m**, and midpoint **v = wL⁴/(384EI) = −0.843750 mm**. Every stored displacement, shear and moment sample is checked against its closed form. That beam has different boundary conditions from the portal; its deflection is not substituted for the physical frame result.

The saved portal results separately match an independently worked symmetric three-DOF strain-energy condensation and the existing independent NumPy stiffness implementation, including eccentric-arm kinematics and joint equilibrium. Actual frame global equilibrium residuals are below **4.4 × 10⁻¹¹ N / N·m**. Full hand formulas, numerical comparisons, stable identities, run IDs and verified raw artifact hashes are in [independent-evidence.json](independent-evidence.json). Solver input/output files and manifests are downloadable in the Analysis Evidence tab; full bundle evidence includes both beam-reference runs.

## Local verification and preservation

- **84 backend tests passed**: 24 new slab tests and 60 existing beam/frame/gravity/eccentric tests. Actual solver tests include 1/2/4-element frame meshes, N–mm/SI conversion, half pressure, conservation and independently verified diagrams. Fixed-fixed reference meshes use 2 elements because the solver explicitly rejects a one-element fully restrained model with no free DOFs.
- **3 browser tests passed**: the complete slab workflow; saved result/camera/screenshot review; and existing frame workspace regression. Tested saved slab selection, diagram clicks, both frame result mappings, deformation/axial/shear/moment/reaction views, manifests, missing-source rejection, forged authorization rejection, half-load results, geometry edit → undo → redo, save/new revision staleness, reapproval, reload, and 1600 × 1000 / 1280 × 820 layouts.
- TypeScript and targeted ESLint checks passed. The initial camera flight overriding analysis framing after reload was fixed. Empty solver stdout is displayed faithfully; version/provenance is taken from saved solver evidence, not invented log text.
- The database snapshot comparison checked **9,567 pre-existing rows across 62 tables**: **zero changed or missing original rows**. All 45 original component objects and origin remain unchanged in the review revision. See [preservation-evidence.json](preservation-evidence.json), [browser-evidence.json](browser-evidence.json), and [test-results.json](test-results.json).
- **Zero paid inference calls**, no installs, Git operations, commits or deployment. The existing offline AI and all prior solver evidence remain preserved.

## Scope and limitations

This milestone is a tributary load-path idealization, **not plate/shell slab FEA**. It rejects two-way distribution, openings/unknown slab attachments, incomplete or transformed geometry, mismatched beam lengths or elevations, additional interior supports, asymmetric or long overhangs, missing sources/sections, undeclared joints and incomplete exclusions. Only uniform synthetic pressure and two independent East-Up linear Euler–Bernoulli frames are supported. Slab stiffness, slab capacity, reinforcement, torsional transfer, shared-frame coupling, whole-building FEA, foundations and IS/US code compliance remain unsupported. Numerical verification is distinct from safety approval; engineering approval and code checks remain disabled.

Browser limitation: the Codex in-app browser could not load the local API/Cesium assets in this session. The completed browser tests and screenshots used local Chromium. Open the URL in Chrome or Edge for review.

Review screenshots: [load path](screenshots/final.png), [bending and member inspection](screenshots/review-moment.png), [deformation](screenshots/review-deformation.png), [responsive view](screenshots/responsive.png). Development stops here for review.

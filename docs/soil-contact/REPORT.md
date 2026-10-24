# Synthetic rigid-footing soil contact milestone

Local review: http://localhost:3001/projects/798/workspace → Analysis → Soil contact.
Source project 797 / revision 112 is preserved. Review project 798 / revision 113 contains the same 56 saved components and unchanged original DXF references. No soil properties are written into the actual CAD model.

## Supported mechanics and explicit assumptions

Only a rigid rectangular footing with vertical compression and one moment about North, resting on uniform independent compression-only linear Winkler springs. Inputs are explicitly classified SYNTHETIC_VERIFICATION. Width B, length L, N, My, stiffness k, load/contact reference elevation, source and applicability evidence are required. Dimensions and stiffness have bounded finite domains; rotation is limited to 0.05 rad. No soil continuum, tensile support, biaxial response or shear transfer is inferred.

Coordinates are right-handed East/North/Up. x is East from the footing centre. Foundation applied load Fz=-N and positive My require a positive-East compression resultant. Downward penetration w(x)=delta+theta*x; positive theta is rotation about North. Upward soil pressure p(x)=k max(w(x),0). Thus integral(p dA)=N and integral(x p dA)=My; the upward reaction moment is -My. Loads are declared at the contact plane; this benchmark does not infer a shear-induced reference-plane moment.

For full contact, A=BL and I=LB³/12: delta=N/(kA), theta=My/(kI), q=N/A+My*x/I. Full contact requires |My/N|≤B/6. At the kern boundary one edge pressure is zero.

For partial contact, e=My/N, a=3(B/2-|e|), active area=La, pmax=2N/(La). The triangular pressure resultant lies a/3 from the loaded edge. Let alpha=pmax/(ka); theta=sign(My)*alpha and delta=alpha*(a-B/2). The inactive region has zero pressure and may lift away from the spring bed. If |e|≥B/2, finite nonnegative pressure cannot equilibrate the load; pressure and displacement results are withheld. N≤0 is outside the positive-compression scope; a zero-load rigid displacement is nonunique.

## Independent hand calculations

Prescribed synthetic inputs: B=L=2 m, N=200 kN, k=20 MN/m³. These are verification values, not measured or manufacturer geotechnical properties.

- Concentric: e=0, area=4 m², q=50 kPa, delta=2.5 mm, theta=0.
- My=40 kN·m: e=.2 m within the .333333 m kern; q=20–80 kPa, delta=2.5 mm, theta=1.5 mrad.
- My=66.666667 kN·m: kern boundary; q=0–100 kPa, theta=2.5 mrad, area=4 m².
- My=100 kN·m: e=.5 m; a=1.5 m; contact interval x=[-.5,1] m and area=3 m². pmax=133.333333 kPa; delta=2.222222 mm; theta=4.444444 mrad; opposite-edge gap=2.222222 mm. Integrated triangular force is .5×133.333333×1.5×2=200 kN. Its centroid x=1−1.5/3=.5 m, giving My=100 kN·m.
- My=-100 kN·m reverses the contact side and rotation with identical area, pressure maximum and centre translation.
- My=200 kN·m places e at the 1 m footprint edge and is impossible with finite compression-only contact; 210 kN·m is outside the footprint.

Independent unit check: k=.02 N/mm³, concentric q=.05 N/mm², so penetration=q/k=2.5 mm. Scaling N and M together scales pressure and displacement while preserving contact extent; doubling k halves displacement/rotation without changing equilibrium pressure.

The numerical reference independently assembles a two-DOF stiffness matrix from 200/400/800 midpoint strip springs, solves active contact sets and integrates spring forces/moments. It does not call the closed-form contact formulas. A separate two-point Gaussian integration checks the analytical pressure field. Numerical evidence records convergence, residuals, individual input values and formulas. In the partial benchmark the analytical moment residual is approximately 1.46e-11 N·m.

## Actual CAD demands remain blocked

All four source demands are read from immutable authorized transport record 464, linked through project 797 revision 112 and original OpenSees slab/frame evidence. West column compression is 29.953701 kN, East 30.046299 kN; transported My is -15.340699 / +15.076795 kN·m respectively, shear East is -9.961989 / +9.961989 kN. Mx and torsion are zero in this source case. North/south pairs retain distinct stable component and footing IDs. These are demands only.

Actual soil calculations remain BLOCKED: sourced geotechnical contact stiffness/law, applicability and physically reviewed connection force transfer are insufficient. Synthetic k is never promoted into project properties. Soil suitability/capacity, allowable settlement, groundwater, shear transfer, concrete/reinforcement strength, anchors, welds, footing capacity, IS/US compliance and engineering approval remain disabled or unsupported.

## UI, persistence and verification

The Analysis panel exposes explicit synthetic inputs, saved preview, exact authorization, numerical results and expandable evidence. The isolated benchmark visualization shows the actual computed contact interval, pressure profile and displacement profile with stated display scales. It hides CAD objects while showing the synthetic diagram and provides Return to saved CAD geometry. Editing synthetic inputs clears the old diagram and marks results stale. New saved proposals invalidate prior authorization/results; model/source bindings are rechecked before calculation. Unsaved model edits and revision comparisons block execution.

483 selected backend regression tests passed, including the existing OpenSees structural workflows. Final 22 soil mechanics/authorization tests passed after bounded-input refinements. Browser evidence covers actual four-demand reading, missing/invalid stiffness/source rejection, forged/obsolete authorization rejection, partial/full contact, reload, staleness, rendered 3D diagrams, responsive layout and return to CAD geometry. TypeScript and targeted lint checks are recorded locally. Final browser outcome is in browser-tests.txt; screenshots and browser-evidence.json accompany this report.

Preservation evidence compares 9,887 pre-existing rows: none missing or changed, all 56 component bodies identical and original/copy DXF hashes identical. No paid inference calls. No Git operations, installations or deployment.

## Previous three metadata changes investigated

Project 796 updated_at changed when its persistent conversation was created at 15:48:06 UTC (21:18:06 IST). The matching POST conversations log and saved conversation ID are recorded. ConversationService.create calls lock_project, which executes UPDATE projects SET id=id; SQLAlchemy's onupdate default advances updated_at even though geometry is untouched.

Project 792 updated_at changed when a USER message was saved at 15:51:08 UTC (21:21:08 IST). Its conversation next_sequence advanced 1→2 for that sequence-1 message. Matching message/run IDs, request log and code paths are recorded in metadata-investigation.json. The run failed AI_PROVIDER_UNAVAILABLE. These are persistence/locking effects, not model/revision/calculation edits. The logs do not establish which human or browser tab initiated the requests. No legitimate metadata or message was restored or removed.

STOP for review. No actual CAD soil analysis or further discipline has been enabled.

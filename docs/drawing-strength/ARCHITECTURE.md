# Versioned engineering methods and source-review architecture

This milestone keeps geometry/source review, FEA demands, constitutive contact mechanics and design-code formulas separate. No design-code adapter modifies OpenSees inputs or solver methods.

## Source and geometry track

The existing ezdxf runtime parses bounded text DXF in explicit millimetres or metres. The new reference-review mode retains exact bytes, SHA256, DXF handles, layer names, original coordinates, converted metre coordinates, dimensions, annotations and unsupported-entity diagnostics. It does not treat layer names, circles or touching outlines as verified engineering components/connections. File contents are source data, not executable instructions.

`DRAWING_REFERENCE` stores immutable extracted evidence against a saved model revision. `DRAWING_REVIEW` stores independently editable labels, roles, plan dimensions, material descriptions, evidence references and explicit source-to-saved-component mappings without altering original bytes or the physical model. Source identities remain stable when the same file is reimported. Correction evidence, original extraction and copied physical context remain distinct.

Three classifications are explicit: **REAL_PROJECT**, **SYNTHETIC_VERIFICATION**, **UNVERIFIED**. A real-project classification is an engineer/user source declaration, not authentication of physical construction. Explicit synthetic source warnings cannot be relabeled as real. Review attribution does not confer professional approval.

An analytical candidate record carries reviewed source identities and missing prerequisites. Here nodes and members remain empty: no verified 3D centerlines, structural sections/materials, loads, supports or joint definitions have been supplied. Future geometry publication must use the existing parametric editor/revision contract, and supported analytical mapping must use the validated physical-frame graph. Merely importing a drawing never invokes a solver.

## Independent design-method track

Registry keys distinguish **country / standard / edition / method / implementation version**. A project supplies its jurisdiction; code adoption and amendments/errata require review. Historical editions are explicit choices, never assumed to be current or applicable.

- `US/ACI318-19-INLB/anchor-steel-nominal-tension@1`: implementation **1.0.0**, equation **17.6.1.2**, nominal steel tension term only. Independent benchmark `anchor-steel-tension-known-answer/v1`.
- `IN/IS800-2007/anchor-steel-tension@planned`: **NOT IMPLEMENTED**. Requires Indian anchor/bolt applicability, authoritative clause review, amendment snapshot, material/partial factors and independent benchmarks. No ACI formula is reused as an Indian check.
- `US/AISC360-22/anchor-design@planned`: **NOT IMPLEMENTED**. Requires its own applicability, errata snapshot, adapter and benchmarks. No ACI/AISC interchangeability is assumed.

The supported ACI term uses supplied effective tensile area, yield and ultimate strengths; the original IN-LB strength cap is converted to SI. A tensile area is never inferred from drawing circles or nominal diameter. Ase,N is in mm², strengths in MPa = N/mm² and output in N/kN. Source: [ACI 318-19 original publication, §17.6.1.2, PDF page 249](https://www.ocf.berkeley.edu/~chiep/wp-content/uploads/2024/01/CE-123-ACI-318-19.pdf).

The country/edition/method adapter validates all inputs and scope. Unsupported methods fail closed. Before releasing any adapter, freeze the formula/edition/source references, implementation version, unit convention, applicability bounds and independently verified benchmark manifest. A future strength-reduction or demand comparison is a separate implementation and verification step.

`ANCHOR_STEEL_INPUT` pins a reviewed proposal to the exact model hash and any owned drawing source/entity/review record. Explicit exact-hash authorization creates `ANCHOR_STEEL_RESULT` with the input snapshot, canonical formula descriptor, independent calculations and authorization attribution. Changed material inputs, revisions, linked drawing imports or source-review evidence make prior results stale. Input and result payloads remain inspectable and are not overwritten by recalculation.

FEA reaction/demand records retain their own solver artifacts, axes, signs, units, model and input hashes. **No automatic demand transfer into this nominal-strength demonstration** occurs: the actual four-anchor contact workflow is still blocked, and this isolated synthetic steel term is not an anchor demand/capacity check.

## Release exclusions

No phi/design strength, factored demand pass/fail, group-anchor action, concrete breakout, pullout, bond, shear/interaction, plate bending, prying, welds, reinforcement, footing or soil capacity checks are enabled. Engineer approval remains DISABLED. Future methods require explicit prerequisites and independently verified implementation; registry entries alone provide no numerical capability.

Authoritative architecture references: [BIS standard lookup](https://www.bis.gov.in/Know-Your-Standard/), [AISC 360-22 publication notice](https://www.aisc.org/news/aisc-releases-new-version-of-specification-for-structural-steel-buildings-ansiaisc-360-22/), and [AISC revisions/errata](https://www.aisc.org/aisc/publications/revisions-and-errata/). These are source/adoption references, not a claim that every provision has been implemented.

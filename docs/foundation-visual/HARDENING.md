# Independent engineering recheck

The earlier statement that IS one-way cut location was unresolved is corrected. **Amendment1 in the primary BIS-authored IS456:2000 publication** inserts the missing text into34.2.4.1(a): the section is at effective depth `d` for a soil-supported footing and `d/2` for piles. The insertion is on PDF page12 (zero-based screenshot page11); the uncorrected main body alone is insufficient. Source: https://law.resource.org/pub/in/bis/S03/is.456.2000.pdf .

The existing soil-cut demands are consistent with that amended location: for the synthetic1.2m square,0.3m patch,150kPa factored net pressure, `dEW=365mm` gives15.3kN and `dNS=345mm` gives18.9kN. Independent pressure integration tests confirm both. **IS one-way resistance remains disabled**: this milestone does not claim independently validated Table19 interpolation, applicability/depth provisions or a complete resistance implementation. The UI distinguishes the available demand from unsupported resistance.

The straight-bar failure is also confirmed independently using50-digit Decimal arithmetic. Under the existing explicitly declared **full design stress** method: M25 plain tension bond1.4MPa × deformed factor1.6 =2.24MPa; steel design stress0.87×500=435MPa; diameter20mm. `Ld=20×435/(4×2.24)=970.982142857…mm`. Straight available reach from the column face is `(1200−300)/2−75=375mm`. Shortfall595.982142857…mm. Both directions exceed this implemented check. Source: IS45626.2.1,26.2.1.1 and34.2.4.3 in the same primary publication.

The display rounds to **971mm required /375mm available** and retains exact saved values in expandable evidence. Dashed red geometry is a required dimension extension, not fabricated steel outside the footing. Actual straight bars retain their1.05m full length,20mm diameter and saved layer depths. No hook, reduced-stress assumption, anchorage device or material substitution was introduced to obtain a passing result. This conservative full-stress check is not asserted to be the only possible engineered anchorage design.

No existing action, geometry, resistance formula, authorization rule or original engineering result was changed. Only the disabled IS-check explanation was corrected, and independent tests were added. Existing implementation hashes make earlier module results stale rather than silently upgrading them.

Independent tests: `backend/tests/test_foundation_visual_hardening.py`; display-coordinate/immutability tests: `frontend/lib/foundation-visual.test.ts`.

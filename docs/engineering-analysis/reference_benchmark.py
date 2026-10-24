"""Independent reference evidence only: no production FEA or code-design checks.

Run with Python standard library. Uses a closed-form series solution and a
separately assembled two-degree-of-freedom stiffness equilibrium solution.
"""
import json
import math
from pathlib import Path


def reference(length, area, modulus, spring, force):
    kb = modulus * area / length
    # DOFs: foundation translation u0, column-head translation u1.
    a, b, c, d = spring + kb, -kb, -kb, kb
    determinant = a * d - b * c
    u0 = (-b * force) / determinant
    u1 = (a * force) / determinant
    closed = force / spring + force * length / (modulus * area)
    assert math.isclose(u1, closed, rel_tol=1e-12)
    assert math.isclose(spring * u0, force, rel_tol=1e-12)
    assert math.isclose(kb * (u1 - u0), force, rel_tol=1e-12)
    return dict(soil_translation=u0, head_translation=u1,
                column_shortening=u1-u0, stress=force/area,
                reaction=spring*u0, strain_energy=force*u1/2)


si = reference(3, 0.01, 200e9, 100e6, 100e3)
mm = reference(3000, 10000, 200000, 100000, 100000)
assert math.isclose(si['head_translation'] * 1000, mm['head_translation'], rel_tol=1e-12)
assert math.isclose(si['stress'] / 1e6, mm['stress'], rel_tol=1e-12)
assert math.isclose(si['strain_energy'] * 1000, mm['strain_energy'], rel_tol=1e-12)
evidence = dict(status='REFERENCE_VERIFIED_SOLVER_NOT_RUN',
    engineering_review='REQUIRED_NOT_APPROVED', code_checks='NONE_SUPPORTED',
    inputs_si=dict(length_m=3, area_m2=0.01, modulus_pa=200e9,
                   soil_spring_n_per_m=100e6, compression_n=100e3),
    results_si=si, results_n_mm=mm,
    assertions='Two independent formulations, equilibrium and N-mm unit equivalence passed',
    limitations=['Linear axial mechanics only', 'No self-weight, buckling or bending',
        'Rigid plate and footing; anchors inactive in this compression-only idealization',
        'Prescribed spring, not derived geotechnical bearing or settlement capacity',
        'No established solver executed and no design-standard checks implemented'])
if __name__ == '__main__':
    Path(__file__).with_name('reference-evidence.json').write_text(
        json.dumps(evidence, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(evidence, indent=2))

"""Local OpenSees axial/spring benchmark. No design-code or approval capability."""
from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
from datetime import datetime, timezone
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[4]
# Validation runs must never write into existing engineering evidence.
ARTIFACT_ROOT = Path(os.environ['GEOAI_ENGINEERING_ARTIFACT_ROOT']).resolve() if os.environ.get('GEOAI_ENGINEERING_ARTIFACT_ROOT') else None
ARTIFACTS = (ARTIFACT_ROOT / 'opensees-benchmark') if ARTIFACT_ROOT else ROOT / 'backend/storage/opensees-benchmark'
FILES = ('model.tcl', 'nodes.tsv', 'forces.tsv', 'summary.tsv', 'stdout.txt', 'stderr.txt', 'manifest.json')


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def executable():
    configured = os.environ.get('GEOAI_OPENSEES_EXECUTABLE')
    return Path(configured) if configured else ROOT / '.cache/opensees/OpenSees3.8.0/bin/OpenSees.exe'


def provenance():
    exe = executable().resolve()
    if not exe.is_file():
        raise RuntimeError('OpenSees executable unavailable; installation requires permission.')
    return {'name': 'OpenSees', 'executable': str(exe),
            'executable_sha256': hashlib.sha256(exe.read_bytes()).hexdigest()}


def axial_values(parameters=None):
    values = dict(parameters) if parameters is not None else {'length_m': 3, 'area_m2': .01,
        'elastic_modulus_pa': 200e9, 'soil_stiffness_n_per_m': 100e6, 'compression_n': 100000}
    k = values.get('support_stiffness_n_per_m', values.get('soil_stiffness_n_per_m'))
    required = [values.get(key) for key in ('length_m', 'area_m2', 'elastic_modulus_pa', 'compression_n')] + [k]
    if any(not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0 for value in required):
        raise ValueError('Explicit finite positive axial geometry/material/load/support values required.')
    return values, k


def model_text(elements=1, load_factor=1.0, units='SI', *, axial_parameters=None):
    if elements not in (1, 2, 4) or units not in ('SI', 'N-mm'):
        raise ValueError('Use 1, 2 or 4 elements and SI or N-mm units.')
    if not math.isfinite(load_factor) or load_factor < 0.1 or load_factor > 2:
        raise ValueError('Compression load factor must be finite and between 0.1 and 2.')
    s = 1 if units == 'SI' else 1000
    q, k = axial_values(axial_parameters)
    length, area, modulus, spring = q['length_m']*s, q['area_m2']*s*s, q['elastic_modulus_pa']/(s*s), k/s
    lines = ['# GeoAI saved physical-column / explicit axial-support model' if axial_parameters is not None else '# GeoAI isolated axial-column / prescribed-soil-spring verification model',
             f'# Units: {units}; no gravity, bending, buckling, contact or design checks',
             '# One-dimensional coordinate/DOF represents local vertical z, upward positive.',
             'wipe', 'model BasicBuilder -ndm 1 -ndf 1', 'node 1 0', 'fix 1 1', 'node 2 0',
             f'uniaxialMaterial Elastic 1 {modulus:.17g}',
             f'uniaxialMaterial Elastic 2 {spring:.17g}',
             'element zeroLength 1 1 2 -mat 2 -dir 1']
    for i in range(1, elements+1):
        lines += [f'node {i+2} {length*i/elements:.17g}',
                  f'element truss {i+1} {i+1} {i+2} {area:.17g} 1']
    lines += ['timeSeries Linear 1', f'pattern Plain 1 1 {{load {elements+2} {-q["compression_n"]*load_factor:.17g}}}',
              'constraints Plain', 'numberer Plain', 'system BandGeneral',
              'test NormUnbalance 1e-8 10 0', 'algorithm Linear',
              'integrator LoadControl 1.0', 'analysis Static', 'set rc [analyze 1]',
              'set f [open summary.tsv w]',
              'puts $f "version\t[version]"', 'puts $f "convergence\t$rc"',
              'if {$rc != 0} {close $f; exit 2}', 'reactions',
              'puts $f "reaction\t[format %.17g [nodeReaction 1 1]]"', 'close $f',
              'set f [open nodes.tsv w]']
    for i in range(elements+2):
        lines += [f'puts $f "{i+1}\t[format %.17g [nodeCoord {i+1} 1]]\t[format %.17g [nodeDisp {i+1} 1]]"']
    lines += ['close $f', 'set f [open forces.tsv w]']
    for i in range(elements):
        lines += [f'puts $f "{i+2}\t[format %.17g [lindex [eleResponse {i+2} axialForce] 0]]"']
    return '\n'.join(lines + ['close $f', 'wipe', 'exit 0', ''])


def parse_outputs(directory, elements, load_factor, units, *, axial_parameters=None):
    q, k = axial_values(axial_parameters)
    force = q['compression_n']*load_factor
    summary = dict(line.split('\t') for line in (directory/'summary.tsv').read_text().splitlines())
    if summary.get('convergence') != '0' or not summary.get('version'):
        raise ValueError('Solver did not converge or did not identify its version.')
    nodes = [[float(x) for x in line.split('\t')] for line in (directory/'nodes.tsv').read_text().splitlines()]
    forces = [[float(x) for x in line.split('\t')] for line in (directory/'forces.tsv').read_text().splitlines()]
    if len(nodes) != elements+2 or len(forces) != elements or any(len(row) != 3 for row in nodes) or any(len(row) != 2 for row in forces):
        raise ValueError('Incomplete or malformed solver output.')
    if [row[0] for row in nodes] != list(range(1, elements+3)) or [row[0] for row in forces] != list(range(2, elements+2)):
        raise ValueError('Unexpected output node/element identities.')
    s = 1 if units == 'SI' else 1000
    reaction = float(summary['reaction'])
    if not all(math.isfinite(x) for row in nodes+forces for x in row) or not math.isfinite(reaction):
        raise ValueError('Nonfinite solver output.')
    settlements = [-row[2]/s for row in nodes]
    actual = {'column_shortening_m': settlements[-1]-settlements[1],
              'spring_settlement_m': settlements[1], 'total_displacement_m': settlements[-1],
              'compression_stress_pa': -forces[0][1]/q['area_m2'], 'reaction_n': reaction}
    shortening = force*q['length_m']/(q['elastic_modulus_pa']*q['area_m2'])
    settlement = force/k
    expected = dict(zip(actual, (shortening, settlement, shortening+settlement, force/q['area_m2'], force)))
    comparisons = {key: {'computed': value, 'reference': expected[key],
                         'relative_error': abs(value-expected[key])/abs(expected[key]),
                         'passed': math.isclose(value, expected[key], rel_tol=1e-6, abs_tol=1e-12)} for key, value in actual.items()}
    residual = abs(reaction-force)
    force_errors = [abs(row[1]+force) for row in forces]
    positions = [0, 0] + [q['length_m']*i/elements for i in range(1, elements+1)]
    mesh_ok = all(math.isclose(row[1]/s, expected_z, abs_tol=1e-9) for row, expected_z in zip(nodes, positions))
    restraint_ok = abs(nodes[0][2]/s) <= 1e-12
    nodal_ok = all(math.isclose(-row[2]/s, settlement+force*row[1]/s/(q['elastic_modulus_pa']*q['area_m2']), rel_tol=1e-6, abs_tol=1e-12) for row in nodes[1:])
    passed = all(row['passed'] for row in comparisons.values()) and residual <= .1 and max(force_errors) <= .1 and mesh_ok and restraint_ok and nodal_ok
    if not passed:
        raise ValueError('Solver result failed independent reference/equilibrium/mesh/restraint verification.')
    return {'solver_version': summary['version'], 'convergence_code': 0, 'verified': True,
            'values_si': actual, 'comparisons': comparisons, 'force_residual_n': residual,
            'nodes': [{'id': int(row[0]), 'z_m': row[1]/s, 'displacement_m': row[2]/s} for row in nodes],
            'elements': [{'id': int(row[0]), 'axial_force_n': row[1]} for row in forces]}


def run_case(*, elements=1, load_factor=1.0, units='SI', timeout=15, axial_parameters=None):
    text = model_text(elements, load_factor, units) if axial_parameters is None else model_text(elements, load_factor, units, axial_parameters=axial_parameters)
    solver = provenance()
    run_id = str(uuid4())
    folder = ARTIFACTS/run_id
    folder.mkdir(parents=True)
    (folder/'model.tcl').write_text(text, encoding='utf-8')
    inputs, _ = axial_values(axial_parameters)
    inputs.update(compression_n=inputs['compression_n']*load_factor, load_factor=load_factor, elements=elements, solver_units=units)
    result = {'run_id': run_id, 'timestamp': datetime.now(timezone.utc).isoformat(), 'solver': solver,
              'inputs': inputs, 'inputs_sha256': digest(inputs), 'input_file_sha256': hashlib.sha256(text.encode()).hexdigest(),
              'status': 'FAILED', 'engineering_approval': 'DISABLED', 'code_checks': 'DISABLED',
              'scope': 'Isolated 3 m axial benchmark; not analysis of the platform or physical footing/anchors',
              'limitations': ['Linear axial elasticity only', 'Rigid plate/footing idealization; anchors inactive',
                             'Prescribed soil spring; no soil capacity check', 'No bending, buckling, self-weight or design-code checks']}
    try:
        proc = subprocess.run([solver['executable'], 'model.tcl'], cwd=folder, capture_output=True,
                              text=True, timeout=timeout, shell=False, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        (folder/'stdout.txt').write_text(proc.stdout, encoding='utf-8')
        (folder/'stderr.txt').write_text(proc.stderr, encoding='utf-8')
        result['exit_code'] = proc.returncode
        if proc.returncode != 0:
            raise ValueError(f'OpenSees exited with code {proc.returncode}; inspect stderr artifact.')
        result.update(parse_outputs(folder, elements, load_factor, units) if axial_parameters is None else parse_outputs(folder, elements, load_factor, units, axial_parameters=axial_parameters))
        result['status'] = 'VERIFIED'
    except (subprocess.TimeoutExpired, OSError, ValueError, KeyError) as error:
        result['error'] = str(error)
        for name in ('stdout', 'stderr'):
            path = folder/f'{name}.txt'
            if not path.exists():
                captured = getattr(error, name, None) or ''
                if isinstance(captured, bytes): captured = captured.decode(errors='replace')
                path.write_text(captured, encoding='utf-8')
    result['artifact_sha256'] = {name: hashlib.sha256((folder/name).read_bytes()).hexdigest() for name in FILES[:-1] if (folder/name).exists()}
    (folder/'manifest.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    return result


def verification_suite():
    cases = [run_case(elements=n) for n in (1, 2, 4)]
    cases += [run_case(elements=2, load_factor=f) for f in (.5, 2)]
    cases += [run_case(elements=2, units='N-mm')]
    return {'status': 'VERIFIED' if all(case['status'] == 'VERIFIED' for case in cases) else 'FAILED',
            'cases': cases, 'engineering_approval': 'DISABLED', 'code_checks': 'DISABLED'}

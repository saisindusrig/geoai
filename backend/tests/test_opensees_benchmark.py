import json
from pathlib import Path
import subprocess

import pytest

from app.services.design import opensees_benchmark as solver


@pytest.fixture(autouse=True)
def artifacts(tmp_path, monkeypatch):
    monkeypatch.setattr(solver, 'ARTIFACTS', tmp_path)


@pytest.mark.parametrize('elements,factor,units', [(1,1,'SI'),(2,1,'SI'),(4,1,'SI'),(2,.5,'SI'),(2,2,'SI'),(2,1,'N-mm')])
def test_real_solver_reference_equilibrium_mesh_and_scaling(elements, factor, units):
    if not solver.executable().is_file():
        pytest.skip('Authorized local OpenSees installation required')
    result = solver.run_case(elements=elements, load_factor=factor, units=units)
    assert result['status'] == 'VERIFIED', result.get('error')
    assert result['convergence_code'] == 0
    assert result['force_residual_n'] < .1
    assert all(x['relative_error'] < 1e-6 for x in result['comparisons'].values())
    assert result['values_si']['total_displacement_m'] == pytest.approx(.00115*factor, rel=1e-6)
    folder = solver.ARTIFACTS/result['run_id']
    assert all((folder/name).is_file() for name in solver.FILES)
    assert json.loads((folder/'manifest.json').read_text())['solver_version'] == result['solver_version']
    assert 'OpenSees' in (folder/'stderr.txt').read_text()


@pytest.mark.parametrize('kwargs', [{'elements':3}, {'load_factor':0}, {'load_factor':float('nan')}, {'load_factor':float('inf')}, {'units':'inch'}])
def test_invalid_inputs_fail_before_process(kwargs):
    with pytest.raises(ValueError):
        solver.run_case(**kwargs)


def test_missing_executable(monkeypatch, tmp_path):
    monkeypatch.setattr(solver, 'executable', lambda: tmp_path/'missing.exe')
    with pytest.raises(RuntimeError, match='unavailable'):
        solver.run_case()


def test_actual_solver_tcl_error_is_captured(monkeypatch):
    monkeypatch.setattr(solver, 'model_text', lambda *args: 'invalidGeoAICommand\nexit 3\n')
    result = solver.run_case()
    assert result['status'] == 'FAILED'
    assert not result.get('verified')
    assert 'invalid command' in (solver.ARTIFACTS/result['run_id']/'stderr.txt').read_text()


def test_timeout_retains_logs(monkeypatch):
    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(args[0], 15, output=b'partial output', stderr=b'partial error')
    monkeypatch.setattr(subprocess, 'run', timeout)
    result = solver.run_case()
    assert result['status'] == 'FAILED'
    assert (solver.ARTIFACTS/result['run_id']/'stderr.txt').read_text() == 'partial error'


def test_actual_solver_timeout(monkeypatch):
    monkeypatch.setattr(solver, 'model_text', lambda *args: 'after 2000\nexit 0\n')
    result = solver.run_case(timeout=.05)
    assert result['status'] == 'FAILED' and 'timed out' in result['error']


def test_actual_singular_model_nonconvergence(monkeypatch):
    original = solver.model_text
    # Deliberately release the sole ground restraint: a linear mechanism.
    monkeypatch.setattr(solver, 'model_text', lambda *args: original(*args).replace('fix 1 1', 'fix 1 0'))
    result = solver.run_case()
    assert result['status'] == 'FAILED' and not result.get('verified')
    assert (solver.ARTIFACTS/result['run_id']/'stderr.txt').is_file()


def test_actual_zero_stiffness_nonconvergence(monkeypatch):
    original = solver.model_text
    monkeypatch.setattr(solver, 'model_text', lambda *args: original(*args).replace('uniaxialMaterial Elastic 1 200000000000', 'uniaxialMaterial Elastic 1 0'))
    result = solver.run_case()
    assert result['status'] == 'FAILED' and result['exit_code'] == 2
    summary = (solver.ARTIFACTS/result['run_id']/'summary.tsv').read_text()
    assert 'convergence\t0\n' not in summary


def test_process_error_is_not_verified(monkeypatch):
    def failure(*args, **kwargs):
        raise OSError('Cannot start process')
    monkeypatch.setattr(subprocess, 'run', failure)
    result = solver.run_case()
    assert result['status'] == 'FAILED' and 'Cannot start' in result['error']


@pytest.mark.parametrize('change', ['nonconvergence','missing','nan','wrong_force','wrong_nodes','wrong_restraint'])
def test_rejects_corrupt_missing_and_nonconverged_output(change):
    result = solver.run_case()
    folder = solver.ARTIFACTS/result['run_id']
    if change == 'nonconvergence':
        (folder/'summary.tsv').write_text('version\t3.8.0\nconvergence\t-3\n')
    if change == 'missing': (folder/'nodes.tsv').write_text('')
    if change == 'nan': (folder/'forces.tsv').write_text('2\tnan\n')
    if change == 'wrong_force': (folder/'forces.tsv').write_text('2\t-1\n')
    if change == 'wrong_nodes': (folder/'nodes.tsv').write_text('1\t0\t0\n2\t0\t-.001\n3\t30\t-.00115\n')
    if change == 'wrong_restraint': (folder/'nodes.tsv').write_text('1\t0\t.001\n2\t0\t-.001\n3\t3\t-.00115\n')
    with pytest.raises(ValueError): solver.parse_outputs(folder,1,1,'SI')


def test_nonzero_exit_even_with_outputs_is_not_verified(monkeypatch):
    original = subprocess.run
    def failure(*args, **kwargs):
        result = original(*args, **kwargs)
        result.returncode = 9
        return result
    monkeypatch.setattr(subprocess, 'run', failure)
    result = solver.run_case()
    assert result['status'] == 'FAILED' and result['exit_code'] == 9


def test_hashes_are_key_order_independent_and_change_on_inputs():
    assert solver.digest({'a':1,'b':2}) == solver.digest({'b':2,'a':1})
    assert solver.digest({'a':1}) != solver.digest({'a':2})

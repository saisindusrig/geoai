"""Read-only local diagnostics. Never executes analysis or calls an AI provider."""
import re
import subprocess
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.infrastructure import database_status
from app.core.production import collect_production_warnings
from app.core.security import get_current_user_id
from app.db.session import get_db
from app.services.design import opensees_benchmark
from app.api.routes.analysis_capabilities import capabilities

router = APIRouter(prefix='/api/system', tags=['system'])


def check(name, status, summary, action='No recovery action needed.'):
    return dict(name=name, status=status, summary=summary, action=action)


def solver_status():
    # Fixed version-only Tcl on stdin: no model, files, loads or FEA commands.
    try:
        exe = opensees_benchmark.executable()
        if not exe.is_file():
            return check('Local solver', 'UNAVAILABLE', 'OpenSees executable was not found.', 'Check the existing local solver configuration; do not install or rerun an analysis automatically.')
        result = subprocess.run([str(exe)], input='puts "GEOAI_VERSION:[version]"\nexit\n', text=True, capture_output=True, timeout=3)
        match = re.search(r'GEOAI_VERSION:([0-9]+(?:\.[0-9]+){1,3})', result.stdout + '\n' + result.stderr)
        if result.returncode == 0 and match:
            return check('Local solver', 'HEALTHY', 'OpenSees ' + match[1] + ' answered a version-only probe. No FEA was run.')
    except (OSError, subprocess.SubprocessError):
        pass
    return check('Local solver', 'DEGRADED', 'OpenSees version could not be verified within the bounded probe.', 'Check executable access and local solver logs, then Retry. Do not infer analysis validity from executable presence.')


@router.get('/diagnostics')
def diagnostics(response: Response, project_id: int | None = Query(None, gt=0), model_revision_id: int | None = Query(None, gt=0), db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    response.headers['Cache-Control'] = 'no-store'
    checks = [check('Backend', 'HEALTHY', 'API request reached the running backend. This is liveness, not engineering approval.')]
    database = database_status()
    connected = database['status'] == 'AVAILABLE'
    checks.append(check('Database', 'HEALTHY' if connected and database['schema'] == 'CURRENT' else 'DEGRADED' if connected else 'UNAVAILABLE',
        'Read-only connection succeeded; schema ' + database['schema'].lower() + '.' if connected else 'Read-only database connection failed.',
        'Review database connectivity and existing migration logs. Never repair or migrate original data from diagnostics.' if not connected or database['schema'] != 'CURRENT' else 'No recovery action needed.'))
    checks.append(solver_status())
    offline = settings.AI_PROVIDER == 'mock' and settings.ENGINEERING_AI_MODE == 'mock' and not settings.ENGINEERING_AI_BUDGET_APPROVED and settings.ENGINEERING_AI_BUDGET_USD == 0
    cloud_configured = any(bool(getattr(settings, key)) for key in ('NEBIUS_API_KEY', 'OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'GEMINI_API_KEY'))
    checks.append(check('AI controls', 'HEALTHY' if offline and not cloud_configured else 'BLOCKED',
        'Offline deterministic modes; engineering budget disabled; cloud credentials absent from this process.' if offline and not cloud_configured else 'Offline-only controls are not fully confirmed. Provider reachability and inference are not tested.',
        'No inference was requested.' if offline and not cloud_configured else 'Use the existing offline run-website.bat launcher. Do not test a provider or authorize spending from diagnostics.'))
    # Existing warnings use fixed messages. Export only their codes, never config values.
    warnings = collect_production_warnings()
    checks.append(check('Production qualification', 'BLOCKED',
        str(len(warnings)) + ' existing configuration warnings; production operations and release qualification remain unverified.',
        'Review docs/PRODUCTION_BETA_READINESS.md and existing system readiness evidence. Healthy local services do not approve a release.'))
    methods = []
    if (project_id is None) != (model_revision_id is None):
        checks.append(check('Saved model / results', 'BLOCKED', 'Both project and saved revision are required.', 'Open diagnostics from Analysis for the saved model context.'))
    elif project_id is not None:
        if not connected:
            checks.append(check('Saved model / results', 'UNAVAILABLE', 'Database is unavailable; saved evidence could not be read.', 'Restore database connectivity manually, then Retry.'))
        else:
            try:
                cap = capabilities(project_id, model_revision_id, '', db, user_id)
                for name, item in cap['methods'].items():
                    methods.append(dict(method=name, status=item['status'], current_results=len(item['current_results']), historical_results=sum(not r['current'] for r in item['history'])))
                count = sum(m['current_results'] for m in methods)
                checks.append(check('Saved model / results', 'HEALTHY' if count else 'DEGRADED',
                    f'Saved context is accessible; {count} current result(s). Historical, failed and stale evidence is excluded from current visualization.',
                    'Return to Analysis to select an exact saved result and case; review missing inputs or stale evidence there.'))
            except HTTPException as exc:
                if exc.status_code in (401, 403):
                    raise
                checks.append(check('Saved model / results', 'BLOCKED', 'The requested saved context is unavailable or no longer accessible.', 'Return to the project and select an accessible saved revision; no substitute result is chosen.'))
            except Exception:
                checks.append(check('Saved model / results', 'UNAVAILABLE', 'Saved evidence could not be read.', 'Check backend logs for this request, then Retry. No analysis has been rerun.'))
    else:
        checks.append(check('Saved model / results', 'BLOCKED', 'No saved project context selected.', 'Open Diagnostics from the Analysis panel to inspect saved model freshness and capabilities.'))
    return dict(checked_at=datetime.now(timezone.utc).isoformat(), checks=checks, methods=methods,
        warning_codes=[w['code'] for w in warnings], engineering_approval='DISABLED', inference_requested=False)

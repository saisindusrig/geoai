"""Arq worker definitions for production deployments.

Run with: arq app.workers.tasks.WorkerSettings
In dev (no Redis / USE_ARQ_WORKER=false), the API process runs jobs inline via
app.services.jobs.submit_design_generation.
"""

import asyncio

from arq.connections import RedisSettings

from app.core.config import settings
from app.services import jobs
from app.services.job_errors import JobCancelledError, JobTimeoutError


async def generate_design_task(
    ctx, job_id: str, project_id: int, scenario_id: int, mode: str = "balanced"
) -> dict:
    try:
        result = await asyncio.wait_for(
            jobs.run_design_job(job_id, project_id, scenario_id, mode),
            timeout=settings.GENERATION_JOB_TIMEOUT_SECONDS,
        )
        if not jobs.is_cancelled(job_id):
            jobs.update_job(
                job_id,
                stage="completed",
                status="completed",
                progress=100,
                message="Design generation completed",
                result=result,
            )
        return result
    except JobCancelledError:
        jobs.cancel_job(job_id)
        raise
    except asyncio.TimeoutError:
        jobs.fail_job(
            job_id,
            JobTimeoutError("Generation timed out"),
            failed_stage=(jobs.get_status(job_id) or {}).get("stage"),
        )
        raise
    except Exception as exc:
        jobs.fail_job(job_id, exc, failed_stage=(jobs.get_status(job_id) or {}).get("stage"))
        raise


class WorkerSettings:
    functions = [generate_design_task]
    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
    job_timeout = settings.GENERATION_JOB_TIMEOUT_SECONDS + 30

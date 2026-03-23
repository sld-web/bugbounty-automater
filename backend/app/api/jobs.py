"""Background jobs API endpoints."""
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends
from pydantic import BaseModel

from app.services.jobs import scheduler, sync_cve_intelligence, monitor_leaks

router = APIRouter(prefix="/jobs", tags=["jobs"])


class JobStatusResponse(BaseModel):
    name: str
    enabled: bool
    last_run: str | None
    last_status: str | None
    last_error: str | None
    interval_minutes: int


class JobTriggerResponse(BaseModel):
    job: str
    triggered: bool
    message: str


@router.get("", response_model=list[JobStatusResponse])
async def list_jobs():
    """List all registered background jobs."""
    return scheduler.list_jobs()


@router.get("/{job_name}", response_model=JobStatusResponse)
async def get_job_status(job_name: str):
    """Get status of a specific job."""
    status = scheduler.get_job_status(job_name)
    if not status:
        from fastapi import HTTPException, status as http_status
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_name} not found",
        )
    return status


@router.post("/{job_name}/trigger", response_model=JobTriggerResponse)
async def trigger_job(job_name: str, background_tasks: BackgroundTasks):
    """Manually trigger a job to run."""
    job_map = {
        "cve_sync": sync_cve_intelligence,
        "leak_monitor": monitor_leaks,
    }

    if job_name not in job_map:
        from fastapi import HTTPException, status as http_status
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_name} not found",
        )

    background_tasks.add_task(job_map[job_name])
    return JobTriggerResponse(
        job=job_name,
        triggered=True,
        message=f"Job {job_name} triggered successfully",
    )


@router.post("/{job_name}/enable", response_model=JobStatusResponse)
async def enable_job(job_name: str):
    """Enable a background job."""
    if job_name not in scheduler.jobs:
        from fastapi import HTTPException, status as http_status
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_name} not found",
        )

    scheduler.jobs[job_name]["enabled"] = True
    return scheduler.get_job_status(job_name)


@router.post("/{job_name}/disable", response_model=JobStatusResponse)
async def disable_job(job_name: str):
    """Disable a background job."""
    if job_name not in scheduler.jobs:
        from fastapi import HTTPException, status as http_status
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_name} not found",
        )

    scheduler.jobs[job_name]["enabled"] = False
    return scheduler.get_job_status(job_name)

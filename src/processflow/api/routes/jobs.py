"""Job CRUD and artifact download endpoints."""

from __future__ import annotations

import json
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from processflow.api.database.engine import async_session_factory, get_db
from processflow.api.database.models import Job
from processflow.api.schemas import (
    JobCreateRequest,
    JobListItem,
    JobListResponse,
    JobResponse,
    RerunRequest,
    TEASummary,
)
from processflow.api.services.job_runner import process_job
from processflow.api.storage import delete_job_artifacts, get_artifact_path

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


def _job_to_response(job: Job) -> JobResponse:
    """Convert a Job ORM instance to a JobResponse."""
    artifact_urls: dict[str, str] = {}
    for attr, filename in [
        ("spec_path", job.spec_path),
        ("mermaid_path", job.mermaid_path),
        ("svg_path", job.svg_path),
        ("xlsx_path", job.xlsx_path),
    ]:
        if filename:
            artifact_urls[attr.replace("_path", "")] = (
                f"/api/jobs/{job.id}/artifacts/{filename}"
            )

    tea = None
    if job.mesp_usd_per_gal is not None:
        tea = TEASummary(
            mesp_usd_per_gal=job.mesp_usd_per_gal,
            mesp_usd_per_kg=job.mesp_usd_per_kg,
            tci_usd=job.tci_usd,
            aoc_usd_per_yr=job.aoc_usd_per_yr,
            irr=job.irr,
            npv_usd=job.npv_usd,
            product_flow_kg_hr=job.product_flow_kg_hr,
        )

    return JobResponse(
        id=job.id,
        status=job.status,
        input_type=job.input_type,
        process_name=job.process_name,
        skip_simulation=job.skip_simulation,
        pfd_format=job.pfd_format,
        validation_errors=json.loads(job.validation_errors)
        if job.validation_errors
        else None,
        validation_warnings=json.loads(job.validation_warnings)
        if job.validation_warnings
        else None,
        tea=tea,
        error_message=job.error_message,
        error_type=job.error_type,
        artifact_urls=artifact_urls,
        mermaid_text=job.mermaid_text,
        created_at=job.created_at,
        updated_at=job.updated_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
    )


def _job_to_list_item(job: Job) -> JobListItem:
    tea = None
    if job.mesp_usd_per_gal is not None:
        tea = TEASummary(
            mesp_usd_per_gal=job.mesp_usd_per_gal,
            mesp_usd_per_kg=job.mesp_usd_per_kg,
            tci_usd=job.tci_usd,
            aoc_usd_per_yr=job.aoc_usd_per_yr,
            irr=job.irr,
            npv_usd=job.npv_usd,
            product_flow_kg_hr=job.product_flow_kg_hr,
        )
    return JobListItem(
        id=job.id,
        status=job.status,
        input_type=job.input_type,
        process_name=job.process_name,
        created_at=job.created_at,
        tea=tea,
    )


# ---------- Endpoints ----------


@router.post("", status_code=201, response_model=JobResponse)
async def create_job(
    request: JobCreateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    job_id = str(uuid4())

    job = Job(
        id=job_id,
        status="submitted",
        input_type=request.input_type,
        skip_simulation=request.skip_simulation,
        pfd_format=request.pfd_format,
    )

    if request.input_type == "nl":
        job.input_text = request.description
    elif request.input_type == "template":
        job.template_name = request.template_name
    elif request.input_type == "json":
        job.process_spec = json.dumps(request.spec)

    db.add(job)
    await db.commit()
    await db.refresh(job)

    background_tasks.add_task(process_job, job_id, async_session_factory)

    return _job_to_response(job)


@router.get("", response_model=JobListResponse)
async def list_jobs(
    page: int = 1,
    per_page: int = 20,
    db: AsyncSession = Depends(get_db),
):
    # Count
    count_result = await db.execute(select(func.count(Job.id)))
    total = count_result.scalar() or 0

    # Page
    offset = (page - 1) * per_page
    stmt = select(Job).order_by(Job.created_at.desc()).offset(offset).limit(per_page)
    result = await db.execute(stmt)
    jobs = result.scalars().all()

    return JobListResponse(
        jobs=[_job_to_list_item(j) for j in jobs],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(job_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return _job_to_response(job)


@router.delete("/{job_id}", status_code=204)
async def delete_job(job_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    delete_job_artifacts(job_id)
    await db.delete(job)
    await db.commit()


@router.get("/{job_id}/artifacts/{filename:path}")
async def download_artifact(job_id: str, filename: str):
    path = get_artifact_path(job_id, filename)
    if path is None:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return FileResponse(path, filename=filename)


@router.get("/{job_id}/spec")
async def get_spec(job_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.process_spec is None:
        raise HTTPException(status_code=404, detail="ProcessSpec not yet available")
    return json.loads(job.process_spec)


@router.post("/{job_id}/rerun", status_code=201, response_model=JobResponse)
async def rerun_job(
    job_id: str,
    request: RerunRequest | None = None,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Job).where(Job.id == job_id))
    original = result.scalar_one_or_none()
    if original is None:
        raise HTTPException(status_code=404, detail="Job not found")

    new_id = str(uuid4())
    skip_sim = request.skip_simulation if request else original.skip_simulation

    new_job = Job(
        id=new_id,
        status="submitted",
        input_type="json",
        skip_simulation=skip_sim,
        pfd_format=original.pfd_format,
    )

    if request and request.spec:
        new_job.process_spec = json.dumps(request.spec)
    elif original.process_spec:
        new_job.process_spec = original.process_spec
    else:
        raise HTTPException(
            status_code=400,
            detail="Original job has no ProcessSpec to rerun",
        )

    db.add(new_job)
    await db.commit()
    await db.refresh(new_job)

    background_tasks.add_task(process_job, new_id, async_session_factory)

    return _job_to_response(new_job)

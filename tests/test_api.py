"""Tests for the ProcessFlow AI REST API.

Uses httpx AsyncClient against the FastAPI app with an in-memory SQLite
database so tests are fast and isolated.
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from processflow.api.app import create_app
from processflow.api.database.models import Base, Job


@pytest_asyncio.fixture
async def db_session_factory():
    """Create an in-memory async SQLite engine and tables."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    yield factory
    await engine.dispose()


@pytest_asyncio.fixture
async def client(db_session_factory):
    """Create an httpx AsyncClient wired to the FastAPI app with test DB."""
    from processflow.api.database import engine as engine_module

    original_factory = engine_module.async_session_factory
    original_get_db = engine_module.get_db

    # Patch session factory and get_db dependency
    engine_module.async_session_factory = db_session_factory

    async def _test_get_db():
        async with db_session_factory() as session:
            yield session

    engine_module.get_db = _test_get_db

    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    engine_module.async_session_factory = original_factory
    engine_module.get_db = original_get_db


# ---------- Health ----------


@pytest.mark.asyncio
async def test_health(client):
    resp = await client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "version" in data


# ---------- Templates ----------


@pytest.mark.asyncio
async def test_list_templates(client):
    resp = await client.get("/api/templates")
    assert resp.status_code == 200
    data = resp.json()
    assert "templates" in data
    assert isinstance(data["templates"], list)
    assert len(data["templates"]) > 0


@pytest.mark.asyncio
async def test_get_template(client):
    # First get a valid template name
    resp = await client.get("/api/templates")
    templates = resp.json()["templates"]
    name = templates[0]

    resp = await client.get(f"/api/templates/{name}")
    assert resp.status_code == 200
    data = resp.json()
    assert "process_name" in data


@pytest.mark.asyncio
async def test_get_template_not_found(client):
    resp = await client.get("/api/templates/nonexistent_template_xyz")
    assert resp.status_code == 404


# ---------- Job CRUD ----------


@pytest.mark.asyncio
async def test_create_job_template(client):
    with patch("processflow.api.routes.jobs.process_job", new_callable=AsyncMock):
        resp = await client.post(
            "/api/jobs",
            json={
                "input_type": "template",
                "template_name": "corn_stover_ethanol",
            },
        )
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "submitted"
    assert data["input_type"] == "template"
    assert "id" in data


@pytest.mark.asyncio
async def test_create_job_nl(client):
    with patch("processflow.api.routes.jobs.process_job", new_callable=AsyncMock):
        resp = await client.post(
            "/api/jobs",
            json={
                "input_type": "nl",
                "description": "A simple ethanol fermentation process",
            },
        )
    assert resp.status_code == 201
    assert resp.json()["input_type"] == "nl"


@pytest.mark.asyncio
async def test_create_job_json(client):
    spec = {
        "process_name": "test_process",
        "feedstock": {"name": "corn stover", "flow_rate_kg_hr": 100.0},
        "product": {"name": "ethanol"},
        "units": [],
        "streams": [],
    }
    with patch("processflow.api.routes.jobs.process_job", new_callable=AsyncMock):
        resp = await client.post(
            "/api/jobs",
            json={"input_type": "json", "spec": spec},
        )
    assert resp.status_code == 201
    assert resp.json()["input_type"] == "json"


@pytest.mark.asyncio
async def test_create_job_skip_simulation(client):
    with patch("processflow.api.routes.jobs.process_job", new_callable=AsyncMock):
        resp = await client.post(
            "/api/jobs",
            json={
                "input_type": "template",
                "template_name": "corn_stover_ethanol",
                "skip_simulation": True,
            },
        )
    assert resp.status_code == 201
    assert resp.json()["skip_simulation"] is True


@pytest.mark.asyncio
async def test_get_job(client):
    with patch("processflow.api.routes.jobs.process_job", new_callable=AsyncMock):
        create_resp = await client.post(
            "/api/jobs",
            json={
                "input_type": "template",
                "template_name": "corn_stover_ethanol",
            },
        )
    job_id = create_resp.json()["id"]

    resp = await client.get(f"/api/jobs/{job_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == job_id


@pytest.mark.asyncio
async def test_get_job_not_found(client):
    resp = await client.get("/api/jobs/nonexistent-id")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_jobs(client):
    # Create a couple of jobs
    with patch("processflow.api.routes.jobs.process_job", new_callable=AsyncMock):
        for _ in range(3):
            await client.post(
                "/api/jobs",
                json={
                    "input_type": "template",
                    "template_name": "corn_stover_ethanol",
                },
            )

    resp = await client.get("/api/jobs")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 3
    assert len(data["jobs"]) == 3
    assert data["page"] == 1


@pytest.mark.asyncio
async def test_list_jobs_pagination(client):
    with patch("processflow.api.routes.jobs.process_job", new_callable=AsyncMock):
        for _ in range(5):
            await client.post(
                "/api/jobs",
                json={
                    "input_type": "template",
                    "template_name": "corn_stover_ethanol",
                },
            )

    resp = await client.get("/api/jobs", params={"page": 1, "per_page": 2})
    data = resp.json()
    assert data["total"] == 5
    assert len(data["jobs"]) == 2
    assert data["page"] == 1
    assert data["per_page"] == 2

    resp2 = await client.get("/api/jobs", params={"page": 3, "per_page": 2})
    data2 = resp2.json()
    assert len(data2["jobs"]) == 1


@pytest.mark.asyncio
async def test_delete_job(client):
    with patch("processflow.api.routes.jobs.process_job", new_callable=AsyncMock):
        create_resp = await client.post(
            "/api/jobs",
            json={
                "input_type": "template",
                "template_name": "corn_stover_ethanol",
            },
        )
    job_id = create_resp.json()["id"]

    resp = await client.delete(f"/api/jobs/{job_id}")
    assert resp.status_code == 204

    # Verify gone
    resp = await client.get(f"/api/jobs/{job_id}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_job_not_found(client):
    resp = await client.delete("/api/jobs/nonexistent-id")
    assert resp.status_code == 404


# ---------- Job Spec ----------


@pytest.mark.asyncio
async def test_get_spec_not_available(client):
    with patch("processflow.api.routes.jobs.process_job", new_callable=AsyncMock):
        create_resp = await client.post(
            "/api/jobs",
            json={
                "input_type": "template",
                "template_name": "corn_stover_ethanol",
            },
        )
    job_id = create_resp.json()["id"]

    # Job was just created, process_job was mocked, so no spec yet
    resp = await client.get(f"/api/jobs/{job_id}/spec")
    assert resp.status_code == 404
    assert "not yet available" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_get_spec_available(client, db_session_factory):
    with patch("processflow.api.routes.jobs.process_job", new_callable=AsyncMock):
        create_resp = await client.post(
            "/api/jobs",
            json={
                "input_type": "template",
                "template_name": "corn_stover_ethanol",
            },
        )
    job_id = create_resp.json()["id"]

    # Manually set process_spec on the job
    spec_data = {"process_name": "test", "feedstock": {}, "product": {}, "units": [], "streams": []}
    from sqlalchemy import select

    async with db_session_factory() as session:
        result = await session.execute(select(Job).where(Job.id == job_id))
        job = result.scalar_one()
        job.process_spec = json.dumps(spec_data)
        await session.commit()

    resp = await client.get(f"/api/jobs/{job_id}/spec")
    assert resp.status_code == 200
    assert resp.json()["process_name"] == "test"


# ---------- Rerun ----------


@pytest.mark.asyncio
async def test_rerun_job(client, db_session_factory):
    with patch("processflow.api.routes.jobs.process_job", new_callable=AsyncMock):
        create_resp = await client.post(
            "/api/jobs",
            json={
                "input_type": "template",
                "template_name": "corn_stover_ethanol",
            },
        )
    job_id = create_resp.json()["id"]

    # Set process_spec so rerun can use it
    spec_data = {"process_name": "rerun_test", "feedstock": {}, "product": {}, "units": [], "streams": []}
    from sqlalchemy import select

    async with db_session_factory() as session:
        result = await session.execute(select(Job).where(Job.id == job_id))
        job = result.scalar_one()
        job.process_spec = json.dumps(spec_data)
        await session.commit()

    with patch("processflow.api.routes.jobs.process_job", new_callable=AsyncMock):
        resp = await client.post(f"/api/jobs/{job_id}/rerun")
    assert resp.status_code == 201
    data = resp.json()
    assert data["id"] != job_id
    assert data["input_type"] == "json"
    assert data["status"] == "submitted"


@pytest.mark.asyncio
async def test_rerun_with_new_spec(client, db_session_factory):
    with patch("processflow.api.routes.jobs.process_job", new_callable=AsyncMock):
        create_resp = await client.post(
            "/api/jobs",
            json={
                "input_type": "template",
                "template_name": "corn_stover_ethanol",
            },
        )
    job_id = create_resp.json()["id"]

    # Set process_spec on original
    from sqlalchemy import select

    async with db_session_factory() as session:
        result = await session.execute(select(Job).where(Job.id == job_id))
        job = result.scalar_one()
        job.process_spec = json.dumps({"process_name": "original"})
        await session.commit()

    new_spec = {"process_name": "modified", "feedstock": {}, "product": {}, "units": [], "streams": []}
    with patch("processflow.api.routes.jobs.process_job", new_callable=AsyncMock):
        resp = await client.post(
            f"/api/jobs/{job_id}/rerun",
            json={"spec": new_spec, "skip_simulation": True},
        )
    assert resp.status_code == 201
    assert resp.json()["skip_simulation"] is True


@pytest.mark.asyncio
async def test_rerun_no_spec(client):
    """Rerun fails if original job has no ProcessSpec."""
    with patch("processflow.api.routes.jobs.process_job", new_callable=AsyncMock):
        create_resp = await client.post(
            "/api/jobs",
            json={
                "input_type": "template",
                "template_name": "corn_stover_ethanol",
            },
        )
    job_id = create_resp.json()["id"]

    with patch("processflow.api.routes.jobs.process_job", new_callable=AsyncMock):
        resp = await client.post(f"/api/jobs/{job_id}/rerun")
    assert resp.status_code == 400
    assert "no ProcessSpec" in resp.json()["detail"]


# ---------- Artifact download ----------


@pytest.mark.asyncio
async def test_artifact_not_found(client):
    with patch("processflow.api.routes.jobs.process_job", new_callable=AsyncMock):
        create_resp = await client.post(
            "/api/jobs",
            json={
                "input_type": "template",
                "template_name": "corn_stover_ethanol",
            },
        )
    job_id = create_resp.json()["id"]

    resp = await client.get(f"/api/jobs/{job_id}/artifacts/nonexistent.xlsx")
    assert resp.status_code == 404


# ---------- Validation ----------


@pytest.mark.asyncio
async def test_create_job_missing_description(client):
    """NL job without description should fail validation."""
    resp = await client.post(
        "/api/jobs",
        json={"input_type": "nl"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_job_missing_template_name(client):
    """Template job without template_name should fail validation."""
    resp = await client.post(
        "/api/jobs",
        json={"input_type": "template"},
    )
    assert resp.status_code == 422

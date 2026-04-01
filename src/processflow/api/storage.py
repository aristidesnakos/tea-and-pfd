"""Artifact file storage helpers."""

from __future__ import annotations

import shutil
from pathlib import Path

from processflow.api.config import settings


def ensure_job_dir(job_id: str) -> Path:
    """Create and return the artifact directory for a job."""
    job_dir = settings.artifacts_dir / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    return job_dir


def get_artifact_path(job_id: str, filename: str) -> Path | None:
    """Return the full path to a job artifact, or None if it doesn't exist."""
    path = settings.artifacts_dir / job_id / filename
    return path if path.exists() else None


def delete_job_artifacts(job_id: str) -> None:
    """Remove the entire artifact directory for a job."""
    job_dir = settings.artifacts_dir / job_id
    if job_dir.exists():
        shutil.rmtree(job_dir)

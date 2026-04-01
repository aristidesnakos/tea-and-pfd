"""Pydantic request/response models for the API."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


# ---------- Requests ----------


class JobCreateNL(BaseModel):
    input_type: Literal["nl"]
    description: str = Field(..., min_length=1)
    skip_simulation: bool = False
    pfd_format: str = "both"


class JobCreateTemplate(BaseModel):
    input_type: Literal["template"]
    template_name: str = Field(..., min_length=1)
    skip_simulation: bool = False
    pfd_format: str = "both"


class JobCreateSpec(BaseModel):
    input_type: Literal["json"]
    spec: dict[str, Any]
    skip_simulation: bool = False
    pfd_format: str = "both"


JobCreateRequest = JobCreateNL | JobCreateTemplate | JobCreateSpec


class RerunRequest(BaseModel):
    spec: dict[str, Any] | None = None
    skip_simulation: bool = False


# ---------- Responses ----------


class TEASummary(BaseModel):
    mesp_usd_per_gal: float | None = None
    mesp_usd_per_kg: float | None = None
    tci_usd: float | None = None
    aoc_usd_per_yr: float | None = None
    irr: float | None = None
    npv_usd: float | None = None
    product_flow_kg_hr: float | None = None


class JobResponse(BaseModel):
    id: str
    status: str
    input_type: str
    process_name: str | None = None
    skip_simulation: bool = False
    pfd_format: str = "both"

    # Validation
    validation_errors: list[str] | None = None
    validation_warnings: list[str] | None = None

    # TEA
    tea: TEASummary | None = None

    # Error
    error_message: str | None = None
    error_type: str | None = None

    # Artifacts
    artifact_urls: dict[str, str] = {}
    mermaid_text: str | None = None

    # Timestamps
    created_at: str
    updated_at: str
    started_at: str | None = None
    completed_at: str | None = None


class JobListItem(BaseModel):
    id: str
    status: str
    input_type: str
    process_name: str | None = None
    created_at: str
    tea: TEASummary | None = None


class JobListResponse(BaseModel):
    jobs: list[JobListItem]
    total: int
    page: int
    per_page: int


class TemplateListResponse(BaseModel):
    templates: list[str]

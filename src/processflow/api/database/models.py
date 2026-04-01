"""SQLAlchemy ORM model for jobs."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, Float, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="submitted")

    # Input
    input_type: Mapped[str] = mapped_column(Text, nullable=False)  # nl, template, json
    input_text: Mapped[str | None] = mapped_column(Text)
    template_name: Mapped[str | None] = mapped_column(Text)
    process_spec: Mapped[str | None] = mapped_column(Text)  # JSON string
    process_name: Mapped[str | None] = mapped_column(Text)
    skip_simulation: Mapped[bool] = mapped_column(Boolean, default=False)
    pfd_format: Mapped[str] = mapped_column(Text, default="both")

    # Validation
    validation_errors: Mapped[str | None] = mapped_column(Text)  # JSON array
    validation_warnings: Mapped[str | None] = mapped_column(Text)  # JSON array

    # TEA results (denormalized for fast listing)
    mesp_usd_per_gal: Mapped[float | None] = mapped_column(Float)
    mesp_usd_per_kg: Mapped[float | None] = mapped_column(Float)
    tci_usd: Mapped[float | None] = mapped_column(Float)
    aoc_usd_per_yr: Mapped[float | None] = mapped_column(Float)
    irr: Mapped[float | None] = mapped_column(Float)
    npv_usd: Mapped[float | None] = mapped_column(Float)
    product_flow_kg_hr: Mapped[float | None] = mapped_column(Float)

    # Error info
    error_message: Mapped[str | None] = mapped_column(Text)
    error_type: Mapped[str | None] = mapped_column(Text)

    # Artifact paths (relative filenames within artifacts/{job_id}/)
    spec_path: Mapped[str | None] = mapped_column(Text)
    mermaid_path: Mapped[str | None] = mapped_column(Text)
    svg_path: Mapped[str | None] = mapped_column(Text)
    xlsx_path: Mapped[str | None] = mapped_column(Text)
    mermaid_text: Mapped[str | None] = mapped_column(Text)

    # Timestamps
    created_at: Mapped[str] = mapped_column(
        Text, default=lambda: datetime.now(timezone.utc).isoformat()
    )
    updated_at: Mapped[str] = mapped_column(
        Text,
        default=lambda: datetime.now(timezone.utc).isoformat(),
        onupdate=lambda: datetime.now(timezone.utc).isoformat(),
    )
    started_at: Mapped[str | None] = mapped_column(Text)
    completed_at: Mapped[str | None] = mapped_column(Text)

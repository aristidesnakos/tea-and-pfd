"""Background job processing pipeline.

Mirrors the flow in cli.py's generate command:
  parse → validate → enrich → render PFD → simulate → write XLSX
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from processflow.api.config import settings
from processflow.api.storage import ensure_job_dir

logger = logging.getLogger(__name__)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def process_job(job_id: str, session_factory: async_sessionmaker) -> None:
    """Run the full processing pipeline for a job.

    Called as a FastAPI BackgroundTask. Updates the job record at each stage
    so the frontend can poll for progress.
    """
    from processflow.api.database.models import Job

    async with session_factory() as session:
        try:
            stmt = select(Job).where(Job.id == job_id)
            result = await session.execute(stmt)
            job = result.scalar_one_or_none()
            if job is None:
                logger.error("Job %s not found", job_id)
                return

            job.started_at = _now()
            job_dir = ensure_job_dir(job_id)

            # --- Step 1: Obtain ProcessSpec ---
            spec = await _parse_input(job)
            job.process_spec = spec.to_json()
            job.process_name = spec.process_name
            await session.commit()

            # --- Step 2: Validate ---
            job.status = "validating"
            job.updated_at = _now()
            await session.commit()

            from processflow.topology.engine import TopologyEngine

            engine = TopologyEngine()
            validation = engine.validate(spec)

            if validation.errors:
                job.validation_errors = json.dumps(validation.errors)
            if validation.warnings:
                job.validation_warnings = json.dumps(validation.warnings)

            if not validation.valid:
                job.status = "failed"
                job.error_message = "; ".join(validation.errors)
                job.error_type = "ValidationError"
                job.completed_at = _now()
                job.updated_at = _now()
                await session.commit()
                return

            # --- Step 3: Enrich ---
            spec = engine.enrich(spec)
            job.process_spec = spec.to_json()

            # Save ProcessSpec artifact
            spec.to_json(job_dir / "process_spec.json")
            job.spec_path = "process_spec.json"

            # --- Step 4: Render PFDs ---
            job.status = "rendering"
            job.updated_at = _now()
            await session.commit()

            await _render_pfds(job, spec, job_dir)
            await session.commit()

            # --- Step 5: Simulate ---
            if not job.skip_simulation:
                job.status = "simulating"
                job.updated_at = _now()
                await session.commit()

                await _run_simulation(job, spec, job_dir)
                await session.commit()

            # --- Done ---
            job.status = "completed"
            job.completed_at = _now()
            job.updated_at = _now()
            await session.commit()

        except Exception:
            logger.exception("Job %s failed", job_id)
            # Re-fetch in case the session is dirty
            stmt = select(Job).where(Job.id == job_id)
            result = await session.execute(stmt)
            job = result.scalar_one_or_none()
            if job is not None:
                import traceback

                job.status = "failed"
                job.error_message = traceback.format_exc()[-500:]
                job.error_type = "UnhandledException"
                job.completed_at = _now()
                job.updated_at = _now()
                await session.commit()


async def _parse_input(job):
    """Parse the job input into a ProcessSpec."""
    from processflow.api.database.models import Job  # noqa: F811

    if job.input_type == "nl":
        job.status = "parsing"
        job.updated_at = _now()

        from processflow.parser.nl_parser import parse_nl_to_spec

        api_key = settings.get_api_key()
        spec = await asyncio.to_thread(
            parse_nl_to_spec,
            job.input_text,
            api_key=api_key,
            model=settings.llm_model,
            provider=settings.llm_provider,
        )

    elif job.input_type == "template":
        from processflow.parser.nl_parser import load_template

        spec = await asyncio.to_thread(load_template, job.template_name)

    elif job.input_type == "json":
        from processflow.schema.process_spec import ProcessSpec

        spec = ProcessSpec.model_validate(json.loads(job.process_spec))

    else:
        raise ValueError(f"Unknown input_type: {job.input_type}")

    return spec


async def _render_pfds(job, spec, job_dir):
    """Generate Mermaid and/or Graphviz PFDs."""
    pfd_format = job.pfd_format or "both"

    if pfd_format in ("mermaid", "both"):
        from processflow.renderer.mermaid_renderer import render_mermaid, save_mermaid

        job.mermaid_text = render_mermaid(spec)
        save_mermaid(spec, job_dir / "pfd.md")
        job.mermaid_path = "pfd.md"

    if pfd_format in ("graphviz", "both"):
        try:
            from processflow.renderer.graphviz_renderer import save_graphviz

            save_graphviz(spec, job_dir / "pfd", format="svg")
            job.svg_path = "pfd.svg"
        except RuntimeError:
            logger.warning("Graphviz not available, skipping SVG for job %s", job.id)


async def _run_simulation(job, spec, job_dir):
    """Run BioSTEAM simulation and write XLSX."""
    import warnings

    warnings.filterwarnings("ignore")

    try:
        from processflow.tea.simulation import run_simulation

        results = await asyncio.to_thread(run_simulation, spec)

        # Extract key metrics
        job.mesp_usd_per_gal = results.mesp_usd_per_gal
        job.mesp_usd_per_kg = results.mesp_usd_per_kg
        job.tci_usd = results.tci_usd
        job.aoc_usd_per_yr = results.aoc_usd_per_yr
        job.irr = results.irr
        job.npv_usd = results.npv_usd
        job.product_flow_kg_hr = results.product_flow_kg_hr

        # Write XLSX
        from processflow.tea.xlsx_writer import write_tea_xlsx

        write_tea_xlsx(results, spec, job_dir / "tea_report.xlsx")
        job.xlsx_path = "tea_report.xlsx"

    except NotImplementedError as e:
        logger.warning("Simulation not supported for job %s: %s", job.id, e)

        # Try generic TEA if economic data is available
        if spec.economic.capex_usd is not None or spec.economic.annual_costs:
            try:
                from processflow.tea.generic_tea import run_generic_tea
                from processflow.tea.xlsx_writer import write_generic_tea_xlsx

                generic = await asyncio.to_thread(run_generic_tea, spec)
                job.tci_usd = generic.tci_usd
                job.aoc_usd_per_yr = generic.aoc_usd_per_yr
                job.npv_usd = generic.npv_usd

                write_generic_tea_xlsx(generic, spec, job_dir / "tea_report.xlsx")
                job.xlsx_path = "tea_report.xlsx"

                logger.info(
                    "Generic TEA completed for job %s: NPV=$%.0f",
                    job.id, generic.npv_usd,
                )
            except Exception:
                logger.exception("Generic TEA failed for job %s", job.id)
                warnings_list = json.loads(job.validation_warnings or "[]")
                warnings_list.append(f"Generic TEA failed: {e}")
                job.validation_warnings = json.dumps(warnings_list)
        else:
            warnings_list = json.loads(job.validation_warnings or "[]")
            warnings_list.append(f"Simulation skipped: {e}")
            job.validation_warnings = json.dumps(warnings_list)

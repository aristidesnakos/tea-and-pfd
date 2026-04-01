"""Template listing and retrieval endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from processflow.api.schemas import TemplateListResponse

router = APIRouter(prefix="/api/templates", tags=["templates"])


@router.get("", response_model=TemplateListResponse)
async def list_templates():
    from processflow.parser.nl_parser import list_templates as _list

    return TemplateListResponse(templates=_list())


@router.get("/{name}")
async def get_template(name: str):
    from processflow.parser.nl_parser import load_template

    try:
        spec = load_template(name)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Template '{name}' not found")
    return spec.model_dump(mode="json")

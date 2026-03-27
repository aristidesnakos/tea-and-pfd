"""Shared fixtures for ProcessFlow AI tests."""

from pathlib import Path

import pytest

from processflow.schema.process_spec import ProcessSpec

TEMPLATES_DIR = Path(__file__).parent.parent / "src" / "processflow" / "parser" / "templates"


@pytest.fixture
def corn_stover_spec() -> ProcessSpec:
    """Load the corn stover ethanol template as a ProcessSpec."""
    return ProcessSpec.from_json(TEMPLATES_DIR / "corn_stover_ethanol.json")


@pytest.fixture
def tmp_output(tmp_path: Path) -> Path:
    """Provide a temporary output directory."""
    return tmp_path

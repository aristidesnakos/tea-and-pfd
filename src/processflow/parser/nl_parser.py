"""Natural Language Parser — converts process descriptions to ProcessSpec via LLM.

Uses the Anthropic Claude API with structured JSON output. The prompt includes
the ProcessSpec schema, unit operation type definitions, and reference examples.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from processflow.schema.process_spec import ProcessSpec, UnitType

TEMPLATES_DIR = Path(__file__).parent / "templates"

SYSTEM_PROMPT = """You are a chemical process engineering expert. Your task is to convert
a natural language description of a chemical or industrial process into a structured
ProcessSpec JSON that can be used for process flow diagram generation and techno-economic
analysis.

## Rules

1. Identify all unit operations described or implied by the process description.
2. Assign each unit a unique ID following convention: U-{area}{number} (e.g., U-101, U-201).
3. Group units into sections (feedstock_handling, pretreatment, reaction, fermentation,
   separation, purification, wastewater, utilities).
4. Define material streams connecting each unit to the next in the process flow.
5. Identify all chemical species involved and their roles.
6. Specify reactions with stoichiometry and conversions when described or well-known.
7. Use reasonable engineering defaults for any parameters not specified.
8. Track which parameters you inferred vs. which came from the user's description —
   list inferred parameter paths in metadata.auto_filled_params.

## Available Unit Operation Types

{unit_types}

## Output Format

Return ONLY valid JSON conforming to the ProcessSpec schema. No markdown, no explanation.
The JSON must be parseable by json.loads().

## ProcessSpec JSON Schema

{json_schema}

## Reference Example

Below is a complete example of a ProcessSpec for corn stover to ethanol:

{reference_example}
"""


def _build_system_prompt() -> str:
    """Build the system prompt with schema, types, and reference example."""
    unit_types = "\n".join(f"- {ut.value}: {ut.name}" for ut in UnitType)

    schema = json.dumps(ProcessSpec.json_schema(), indent=2)

    template_path = TEMPLATES_DIR / "corn_stover_ethanol.json"
    reference = template_path.read_text() if template_path.exists() else "{}"

    return SYSTEM_PROMPT.format(
        unit_types=unit_types,
        json_schema=schema,
        reference_example=reference,
    )


def parse_nl_to_spec(
    description: str,
    api_key: str | None = None,
    model: str = "claude-sonnet-4-20250514",
) -> ProcessSpec:
    """Parse a natural language process description into a ProcessSpec.

    Args:
        description: Natural language process description
        api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
        model: Claude model to use

    Returns:
        Validated ProcessSpec

    Raises:
        ValueError: If the LLM output cannot be parsed into a valid ProcessSpec
        RuntimeError: If the API call fails
    """
    import anthropic

    api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError(
            "No Anthropic API key found. Set ANTHROPIC_API_KEY environment variable "
            "or pass api_key parameter."
        )

    client = anthropic.Anthropic(api_key=api_key)
    system_prompt = _build_system_prompt()

    try:
        response = client.messages.create(
            model=model,
            max_tokens=8192,
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": f"Convert this process description to ProcessSpec JSON:\n\n{description}",
                }
            ],
        )
    except Exception as e:
        raise RuntimeError(f"Claude API call failed: {e}") from e

    # Extract text content from response
    raw_text = ""
    for block in response.content:
        if block.type == "text":
            raw_text += block.text

    # Strip markdown code fences if present
    raw_text = raw_text.strip()
    if raw_text.startswith("```"):
        lines = raw_text.split("\n")
        # Remove first line (```json) and last line (```)
        lines = [l for l in lines if not l.strip().startswith("```")]
        raw_text = "\n".join(lines)

    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"LLM output is not valid JSON: {e}\n\nRaw output:\n{raw_text[:500]}"
        ) from e

    try:
        spec = ProcessSpec.model_validate(data)
    except Exception as e:
        raise ValueError(
            f"LLM output does not conform to ProcessSpec schema: {e}"
        ) from e

    return spec


def load_template(name: str) -> ProcessSpec:
    """Load a pre-built ProcessSpec template by name.

    Args:
        name: Template name (without .json extension)

    Returns:
        ProcessSpec loaded from the template

    Raises:
        FileNotFoundError: If template doesn't exist
    """
    path = TEMPLATES_DIR / f"{name}.json"
    if not path.exists():
        available = [p.stem for p in TEMPLATES_DIR.glob("*.json")]
        raise FileNotFoundError(
            f"Template '{name}' not found. Available: {available}"
        )
    return ProcessSpec.from_json(path)


def list_templates() -> list[str]:
    """List available template names."""
    return sorted(p.stem for p in TEMPLATES_DIR.glob("*.json"))

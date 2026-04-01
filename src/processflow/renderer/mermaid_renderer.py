"""Mermaid.js PFD renderer — generates Mermaid flowchart syntax from ProcessSpec."""

from __future__ import annotations

from pathlib import Path

from processflow.schema.process_spec import ProcessSpec, UnitType

# Color mapping for process sections
SECTION_COLORS: dict[str, str] = {
    "feedstock_handling": "#e8f5e9",
    "pretreatment": "#fff3e0",
    "saccharification_fermentation": "#e3f2fd",
    "separation": "#fce4ec",
    "wastewater": "#f3e5f5",
    "utilities": "#e0f2f1",
}

# Shape mapping: unit type string -> mermaid node shape
UNIT_SHAPES: dict[str, tuple[str, str]] = {
    UnitType.REACTOR.value: ("{{", "}}"),
    UnitType.FERMENTOR.value: ("{{", "}}"),
    UnitType.ENZYMATIC_HYDROLYSIS.value: ("{{", "}}"),
    UnitType.PRETREATMENT.value: ("{{", "}}"),
    UnitType.DISTILLATION.value: ("([", "])"),
    UnitType.MOLECULAR_SIEVE.value: ("([", "])"),
    UnitType.EVAPORATOR.value: ("([", "])"),
    UnitType.FLASH.value: ("([", "])"),
    UnitType.BOILER.value: ("[/", "\\]"),
    UnitType.TURBINE.value: ("[/", "\\]"),
    UnitType.PUMP.value: (">", "]"),
    UnitType.HEAT_EXCHANGER.value: ("[", "]"),
    UnitType.STORAGE_TANK.value: ("[(", ")]"),
    UnitType.WASTEWATER_TREATMENT.value: ("[[", "]]"),
}

DEFAULT_SHAPE = ("[", "]")


def _node_id(unit_id: str) -> str:
    """Convert unit ID to valid Mermaid node ID (no hyphens)."""
    return unit_id.replace("-", "_")


def _node_label(unit_id: str, name: str | None, unit_type: str) -> str:
    """Create the display label for a unit node."""
    label = name or unit_type
    return f"{unit_id}\\n{label}"


def render_mermaid(spec: ProcessSpec, direction: str = "LR") -> str:
    """Generate Mermaid flowchart syntax from a ProcessSpec.

    Args:
        spec: Validated ProcessSpec
        direction: Flow direction ('LR', 'TB', 'RL', 'BT')

    Returns:
        Mermaid flowchart string
    """
    lines: list[str] = []
    lines.append(f"flowchart {direction}")

    # Collect units by section for subgraph grouping
    sections: dict[str, list[str]] = {}
    for unit in spec.units:
        section = unit.section or "other"
        sections.setdefault(section, []).append(unit.id)

    # Render subgraphs by section
    for section, unit_ids in sections.items():
        section_label = section.replace("_", " ").title()
        lines.append(f"    subgraph {_node_id(section)}[\"{section_label}\"]")

        for uid in unit_ids:
            unit = spec.get_unit_by_id(uid)
            if unit is None:
                continue
            nid = _node_id(uid)
            label = _node_label(uid, unit.name, unit.type)
            open_s, close_s = UNIT_SHAPES.get(unit.type, DEFAULT_SHAPE)
            lines.append(f"        {nid}{open_s}\"{label}\"{close_s}")

        lines.append("    end")

    # Render feed and product nodes
    lines.append('    feed(["Feed: ' + spec.feedstock.name + '"])')
    for product in spec.products:
        lines.append(f'    product(["{product.name} Product"])')
    lines.append('    waste(["Waste"])')
    lines.append('    utility(["Utilities"])')

    # Render streams as edges
    for stream in spec.streams:
        from_nid = _node_id(stream.from_id)
        to_nid = _node_id(stream.to_id)

        # Build edge label from components
        label_parts = []
        if stream.components:
            names = stream.component_names
            label_parts.append(", ".join(names[:3]))
            if len(names) > 3:
                label_parts.append("...")
        if stream.flow_rate_kg_hr:
            label_parts.append(f"{stream.flow_rate_kg_hr:.0f} kg/hr")

        if label_parts:
            label = " | ".join(label_parts)
            lines.append(f"    {from_nid} -->|\"{label}\"| {to_nid}")
        else:
            lines.append(f"    {from_nid} --> {to_nid}")

    # Apply section colors via style
    for section, color in SECTION_COLORS.items():
        if section in sections:
            lines.append(f"    style {_node_id(section)} fill:{color},stroke:#999")

    return "\n".join(lines)


def render_mermaid_markdown(spec: ProcessSpec, direction: str = "LR") -> str:
    """Generate a Markdown document with embedded Mermaid PFD.

    Args:
        spec: Validated ProcessSpec
        direction: Flow direction

    Returns:
        Markdown string with Mermaid code block
    """
    mermaid = render_mermaid(spec, direction)
    return f"""# Process Flow Diagram: {spec.process_name}

{spec.description}

```mermaid
{mermaid}
```

## Unit Operations

| ID | Type | Name | Section |
|----|------|------|---------|
""" + "\n".join(
        f"| {u.id} | {u.type} | {u.name or '-'} | {u.section or '-'} |"
        for u in spec.units
    )


def save_mermaid(spec: ProcessSpec, path: str | Path, direction: str = "LR") -> Path:
    """Save Mermaid PFD as a Markdown file.

    Args:
        spec: Validated ProcessSpec
        path: Output file path (.md)
        direction: Flow direction

    Returns:
        Path to the saved file
    """
    path = Path(path)
    content = render_mermaid_markdown(spec, direction)
    path.write_text(content)
    return path

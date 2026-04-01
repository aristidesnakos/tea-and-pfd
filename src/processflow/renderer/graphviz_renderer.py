"""Graphviz PFD renderer — generates DOT diagrams from ProcessSpec.

Supports two modes:
1. Standalone: generates DOT from ProcessSpec directly (no BioSTEAM needed)
2. BioSTEAM native: uses BioSTEAM's system.diagram() when a System is available
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import TYPE_CHECKING

from processflow.schema.process_spec import ProcessSpec, UnitType

if TYPE_CHECKING:
    import graphviz as gv

# Graphviz shape mapping for unit operation types (keyed by string)
UNIT_SHAPES: dict[str, dict[str, str]] = {
    UnitType.REACTOR.value: {"shape": "octagon", "style": "filled", "fillcolor": "#BBDEFB"},
    UnitType.FERMENTOR.value: {"shape": "octagon", "style": "filled", "fillcolor": "#C8E6C9"},
    UnitType.ENZYMATIC_HYDROLYSIS.value: {"shape": "octagon", "style": "filled", "fillcolor": "#C8E6C9"},
    UnitType.PRETREATMENT.value: {"shape": "hexagon", "style": "filled", "fillcolor": "#FFE0B2"},
    UnitType.DISTILLATION.value: {"shape": "trapezium", "style": "filled", "fillcolor": "#F8BBD0"},
    UnitType.MOLECULAR_SIEVE.value: {"shape": "trapezium", "style": "filled", "fillcolor": "#F8BBD0"},
    UnitType.EVAPORATOR.value: {"shape": "trapezium", "style": "filled", "fillcolor": "#F8BBD0"},
    UnitType.FLASH.value: {"shape": "invtrapezium", "style": "filled", "fillcolor": "#F8BBD0"},
    UnitType.BOILER.value: {"shape": "doubleoctagon", "style": "filled", "fillcolor": "#B2DFDB"},
    UnitType.TURBINE.value: {"shape": "doubleoctagon", "style": "filled", "fillcolor": "#B2DFDB"},
    UnitType.PUMP.value: {"shape": "triangle", "style": "filled", "fillcolor": "#E0E0E0"},
    UnitType.HEAT_EXCHANGER.value: {"shape": "diamond", "style": "filled", "fillcolor": "#FFF9C4"},
    UnitType.STORAGE_TANK.value: {"shape": "cylinder", "style": "filled", "fillcolor": "#D7CCC8"},
    UnitType.WASTEWATER_TREATMENT.value: {"shape": "box3d", "style": "filled", "fillcolor": "#E1BEE7"},
    UnitType.MIXER.value: {"shape": "invtriangle", "style": "filled", "fillcolor": "#E0E0E0"},
    UnitType.SPLITTER.value: {"shape": "triangle", "style": "filled", "fillcolor": "#E0E0E0"},
}

DEFAULT_NODE_ATTRS = {"shape": "box", "style": "filled", "fillcolor": "#E8EAF6"}

SECTION_COLORS: dict[str, str] = {
    "feedstock_handling": "#E8F5E9",
    "pretreatment": "#FFF3E0",
    "saccharification_fermentation": "#E3F2FD",
    "separation": "#FCE4EC",
    "wastewater": "#F3E5F5",
    "utilities": "#E0F2F1",
}


def _check_graphviz_binary() -> bool:
    """Check if the Graphviz system binary (dot) is available."""
    return shutil.which("dot") is not None


def render_graphviz(spec: ProcessSpec) -> gv.Digraph:
    """Generate a Graphviz Digraph from a ProcessSpec.

    Args:
        spec: Validated ProcessSpec

    Returns:
        graphviz.Digraph object (call .render() to save)

    Raises:
        RuntimeError: If Graphviz system binary is not installed
    """
    if not _check_graphviz_binary():
        raise RuntimeError(
            "Graphviz system binary ('dot') not found. "
            "Install it with: brew install graphviz (macOS) or "
            "apt install graphviz (Linux)"
        )

    import graphviz as gv

    dot = gv.Digraph(
        name=spec.process_name,
        format="svg",
        graph_attr={
            "rankdir": "LR",
            "label": spec.process_name,
            "labelloc": "t",
            "fontsize": "16",
            "fontname": "Helvetica",
            "bgcolor": "white",
            "pad": "0.5",
        },
        node_attr={
            "fontname": "Helvetica",
            "fontsize": "10",
        },
        edge_attr={
            "fontname": "Helvetica",
            "fontsize": "8",
        },
    )

    # Group units by section into subgraphs
    sections: dict[str, list[str]] = {}
    for unit in spec.units:
        section = unit.section or "other"
        sections.setdefault(section, []).append(unit.id)

    for section, unit_ids in sections.items():
        section_label = section.replace("_", " ").title()
        bg_color = SECTION_COLORS.get(section, "#F5F5F5")

        with dot.subgraph(name=f"cluster_{section}") as sub:
            sub.attr(
                label=section_label,
                style="filled,rounded",
                fillcolor=bg_color,
                color="#999999",
            )

            for uid in unit_ids:
                unit = spec.get_unit_by_id(uid)
                if unit is None:
                    continue
                label = f"{uid}\n{unit.name or unit.type}"
                attrs = UNIT_SHAPES.get(unit.type, DEFAULT_NODE_ATTRS).copy()
                sub.node(uid, label=label, **attrs)

    # Feed and product nodes
    dot.node("feed", label=f"Feed\n{spec.feedstock.name}", shape="parallelogram",
             style="filled", fillcolor="#A5D6A7")
    for product in spec.products:
        dot.node("product", label=f"Product\n{product.name}", shape="parallelogram",
                 style="filled", fillcolor="#EF9A9A")
    dot.node("waste", label="Waste", shape="parallelogram",
             style="filled", fillcolor="#BDBDBD")
    dot.node("utility", label="Utilities", shape="parallelogram",
             style="filled", fillcolor="#80CBC4")

    # Edges from streams
    for stream in spec.streams:
        label_parts = []
        if stream.components:
            names = stream.component_names
            label_parts.append(", ".join(names[:3]))
        if stream.flow_rate_kg_hr:
            label_parts.append(f"{stream.flow_rate_kg_hr:.0f} kg/hr")
        label = "\n".join(label_parts) if label_parts else ""

        edge_attrs: dict[str, str] = {}
        if label:
            edge_attrs["label"] = label
        if stream.phase == "vapor":
            edge_attrs["style"] = "dashed"
        elif stream.phase == "solid":
            edge_attrs["style"] = "bold"

        dot.edge(stream.from_id, stream.to_id, **edge_attrs)

    return dot


def save_graphviz(
    spec: ProcessSpec,
    path: str | Path,
    format: str = "svg",
) -> Path:
    """Render and save a Graphviz PFD.

    Args:
        spec: Validated ProcessSpec
        path: Output file path (without extension)
        format: Output format ('svg', 'pdf', 'png')

    Returns:
        Path to the rendered file
    """
    dot = render_graphviz(spec)
    dot.format = format
    path = Path(path)
    rendered = dot.render(filename=str(path.with_suffix("")), cleanup=True)
    return Path(rendered)


def render_from_biosteam_system(
    system: object,
    path: str | Path,
    format: str = "svg",
    kind: str = "thorough",
) -> Path:
    """Render PFD from an existing BioSTEAM System using its native diagram method.

    Args:
        system: A biosteam.System object
        path: Output file path
        format: Output format
        kind: BioSTEAM diagram kind ('thorough', 'surface', 'minimal', 'cluster')

    Returns:
        Path to the rendered file
    """
    import biosteam as bst

    if not isinstance(system, bst.System):
        raise TypeError(f"Expected biosteam.System, got {type(system)}")

    path = Path(path)
    digraph = system.diagram(kind=kind, display=False)
    digraph.format = format
    rendered = digraph.render(filename=str(path.with_suffix("")), cleanup=True)
    return Path(rendered)

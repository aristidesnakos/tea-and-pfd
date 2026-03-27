"""Tests for PFD renderers (Mermaid and Graphviz)."""

import pytest

from processflow.renderer.mermaid_renderer import (
    render_mermaid,
    render_mermaid_markdown,
    save_mermaid,
)
from processflow.schema.process_spec import ProcessSpec


class TestMermaidRenderer:
    def test_basic_output(self, corn_stover_spec: ProcessSpec):
        """Mermaid output contains expected flowchart structure."""
        result = render_mermaid(corn_stover_spec)
        assert result.startswith("flowchart LR")
        assert "subgraph" in result
        assert "U_101" in result  # node ID (hyphen converted to underscore)
        assert "-->" in result  # edges

    def test_all_units_present(self, corn_stover_spec: ProcessSpec):
        """All unit operations appear in the Mermaid output."""
        result = render_mermaid(corn_stover_spec)
        for unit in corn_stover_spec.units:
            node_id = unit.id.replace("-", "_")
            assert node_id in result, f"Unit {unit.id} missing from Mermaid output"

    def test_feed_and_product_nodes(self, corn_stover_spec: ProcessSpec):
        """Feed and product nodes are included."""
        result = render_mermaid(corn_stover_spec)
        assert "feed" in result
        assert "product" in result

    def test_markdown_output(self, corn_stover_spec: ProcessSpec):
        """Markdown wrapper includes title and mermaid code block."""
        result = render_mermaid_markdown(corn_stover_spec)
        assert "# Process Flow Diagram" in result
        assert "```mermaid" in result
        assert "| ID |" in result  # unit operations table

    def test_save_to_file(self, corn_stover_spec: ProcessSpec, tmp_output):
        """Mermaid PFD saves to file correctly."""
        path = save_mermaid(corn_stover_spec, tmp_output / "test.md")
        assert path.exists()
        content = path.read_text()
        assert "flowchart" in content

    def test_direction_parameter(self, corn_stover_spec: ProcessSpec):
        """Direction parameter is respected."""
        lr = render_mermaid(corn_stover_spec, direction="LR")
        tb = render_mermaid(corn_stover_spec, direction="TB")
        assert lr.startswith("flowchart LR")
        assert tb.startswith("flowchart TB")


class TestGraphvizRenderer:
    def test_basic_output(self, corn_stover_spec: ProcessSpec):
        """Graphviz DOT output contains expected structure."""
        from processflow.renderer.graphviz_renderer import render_graphviz
        dot = render_graphviz(corn_stover_spec)
        source = dot.source
        assert "digraph" in source
        assert "U-101" in source
        assert "cluster_" in source  # subgraphs

    def test_save_svg(self, corn_stover_spec: ProcessSpec, tmp_output):
        """Graphviz renders to SVG file."""
        from processflow.renderer.graphviz_renderer import save_graphviz
        path = save_graphviz(corn_stover_spec, tmp_output / "test", format="svg")
        assert path.exists()
        assert path.suffix == ".svg"

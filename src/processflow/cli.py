"""ProcessFlow AI CLI — command-line interface for the NL → PFD + TEA pipeline."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click


@click.group()
@click.version_option(version="0.1.0")
def main() -> None:
    """ProcessFlow AI — Natural language to process flow diagrams and TEA."""


@main.command()
@click.argument("description", required=False)
@click.option("--spec", type=click.Path(exists=True), help="Path to existing ProcessSpec JSON file")
@click.option("--template", type=str, help="Use a built-in template (e.g., 'corn_stover_ethanol')")
@click.option("--output", "-o", type=click.Path(), default="./results", help="Output directory")
@click.option("--api-key", envvar="ANTHROPIC_API_KEY", help="Anthropic API key")
@click.option("--skip-simulation", is_flag=True, help="Skip BioSTEAM simulation (PFD only)")
@click.option("--format", "pfd_format", type=click.Choice(["mermaid", "graphviz", "both"]),
              default="both", help="PFD output format")
def generate(
    description: str | None,
    spec: str | None,
    template: str | None,
    output: str,
    api_key: str | None,
    skip_simulation: bool,
    pfd_format: str,
) -> None:
    """Generate PFD and TEA from a process description, spec file, or template.

    Examples:

      processflow generate "corn stover to ethanol with dilute acid pretreatment"

      processflow generate --template corn_stover_ethanol

      processflow generate --spec my_process.json
    """
    from processflow.schema.process_spec import ProcessSpec
    from processflow.topology.engine import TopologyEngine

    output_dir = Path(output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: Get or create ProcessSpec
    if spec:
        click.echo(f"Loading ProcessSpec from {spec}...")
        process_spec = ProcessSpec.from_json(spec)
    elif template:
        click.echo(f"Loading template: {template}...")
        from processflow.parser.nl_parser import load_template
        process_spec = load_template(template)
    elif description:
        click.echo("Parsing natural language description with Claude API...")
        from processflow.parser.nl_parser import parse_nl_to_spec
        process_spec = parse_nl_to_spec(description, api_key=api_key)
    else:
        click.echo("Error: Provide a description, --spec file, or --template name.", err=True)
        sys.exit(1)

    # Step 2: Validate and enrich
    engine = TopologyEngine()
    result = engine.validate(process_spec)
    if not result.valid:
        click.echo(f"Validation errors: {result.errors}", err=True)
        sys.exit(1)
    if result.warnings:
        for w in result.warnings:
            click.echo(f"Warning: {w}", err=True)

    process_spec = engine.enrich(process_spec)

    # Save the ProcessSpec
    spec_path = output_dir / "process_spec.json"
    process_spec.to_json(spec_path)
    click.echo(f"ProcessSpec saved to {spec_path}")

    # Step 3: Generate PFD
    if pfd_format in ("mermaid", "both"):
        from processflow.renderer.mermaid_renderer import save_mermaid
        mermaid_path = save_mermaid(process_spec, output_dir / "pfd.md")
        click.echo(f"Mermaid PFD saved to {mermaid_path}")

    if pfd_format in ("graphviz", "both"):
        try:
            from processflow.renderer.graphviz_renderer import save_graphviz
            svg_path = save_graphviz(process_spec, output_dir / "pfd", format="svg")
            click.echo(f"Graphviz PFD saved to {svg_path}")
        except RuntimeError as e:
            click.echo(f"Graphviz skipped: {e}", err=True)

    # Step 4: Run simulation and generate TEA
    if not skip_simulation:
        click.echo("Running BioSTEAM simulation...")
        try:
            from processflow.tea.simulation import run_simulation
            from processflow.tea.xlsx_writer import write_tea_xlsx

            results = run_simulation(process_spec)
            xlsx_path = write_tea_xlsx(results, process_spec, output_dir / "tea_report.xlsx")
            click.echo(f"TEA report saved to {xlsx_path}")
            click.echo(f"\nKey Results:")
            click.echo(f"  MESP: ${results.mesp_usd_per_gal:.2f}/gal (${results.mesp_usd_per_kg:.2f}/kg)")
            click.echo(f"  Total Capital Investment: ${results.tci_usd/1e6:.1f}M")
            click.echo(f"  Annual Operating Cost: ${results.aoc_usd_per_yr/1e6:.1f}M/yr")
        except NotImplementedError as e:
            click.echo(f"Simulation skipped: {e}", err=True)
        except Exception as e:
            click.echo(f"Simulation failed: {e}", err=True)
    else:
        click.echo("Simulation skipped (--skip-simulation)")

    click.echo(f"\nAll outputs saved to {output_dir}/")


@main.command()
@click.option("--spec", type=click.Path(exists=True), required=True, help="ProcessSpec JSON file")
@click.option("--format", "fmt", type=click.Choice(["mermaid", "graphviz"]), default="mermaid")
@click.option("--output", "-o", type=click.Path(), required=True, help="Output file path")
def pfd(spec: str, fmt: str, output: str) -> None:
    """Generate only a PFD from a ProcessSpec file."""
    from processflow.schema.process_spec import ProcessSpec

    process_spec = ProcessSpec.from_json(spec)

    if fmt == "mermaid":
        from processflow.renderer.mermaid_renderer import save_mermaid
        path = save_mermaid(process_spec, output)
    else:
        from processflow.renderer.graphviz_renderer import save_graphviz
        path = save_graphviz(process_spec, output, format="svg")

    click.echo(f"PFD saved to {path}")


@main.command()
@click.option("--spec", type=click.Path(exists=True), required=True, help="ProcessSpec JSON file")
@click.option("--output", "-o", type=click.Path(), required=True, help="Output XLSX path")
def tea(spec: str, output: str) -> None:
    """Generate only a TEA spreadsheet from a ProcessSpec file."""
    from processflow.schema.process_spec import ProcessSpec
    from processflow.tea.simulation import run_simulation
    from processflow.tea.xlsx_writer import write_tea_xlsx

    process_spec = ProcessSpec.from_json(spec)

    click.echo("Running simulation...")
    results = run_simulation(process_spec)

    path = write_tea_xlsx(results, process_spec, output)
    click.echo(f"TEA report saved to {path}")
    click.echo(f"MESP: ${results.mesp_usd_per_gal:.2f}/gal")


@main.command()
def templates() -> None:
    """List available process templates."""
    from processflow.parser.nl_parser import list_templates
    names = list_templates()
    if names:
        click.echo("Available templates:")
        for name in names:
            click.echo(f"  - {name}")
    else:
        click.echo("No templates found.")


if __name__ == "__main__":
    main()

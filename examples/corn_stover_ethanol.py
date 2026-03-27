"""Example: Corn Stover to Ethanol — full pipeline demonstration.

This script demonstrates the complete ProcessFlow AI pipeline:
1. Load the corn stover ethanol template (or parse from NL)
2. Validate and enrich the ProcessSpec
3. Generate Mermaid and Graphviz PFDs
4. Run BioSTEAM simulation
5. Generate TEA XLSX report

Usage:
    python examples/corn_stover_ethanol.py
"""

import warnings
from pathlib import Path

warnings.filterwarnings("ignore")


def main():
    from processflow.parser.nl_parser import load_template
    from processflow.renderer.graphviz_renderer import save_graphviz
    from processflow.renderer.mermaid_renderer import render_mermaid, save_mermaid
    from processflow.tea.simulation import run_cornstover_simulation
    from processflow.tea.xlsx_writer import write_tea_xlsx
    from processflow.topology.engine import TopologyEngine

    output_dir = Path("results")
    output_dir.mkdir(exist_ok=True)

    # Step 1: Load template
    print("Loading corn stover ethanol template...")
    spec = load_template("corn_stover_ethanol")
    print(f"  Process: {spec.process_name}")
    print(f"  Units: {len(spec.units)}")
    print(f"  Streams: {len(spec.streams)}")

    # Step 2: Validate and enrich
    engine = TopologyEngine()
    result = engine.validate(spec)
    print(f"\n  Validation: {'PASS' if result.valid else 'FAIL'}")
    if result.warnings:
        for w in result.warnings:
            print(f"  Warning: {w}")

    spec = engine.enrich(spec)
    print(f"  Auto-filled {len(spec.metadata.auto_filled_params)} parameters")

    # Step 3: Save ProcessSpec
    spec.to_json(output_dir / "process_spec.json")
    print(f"\n  ProcessSpec saved to {output_dir / 'process_spec.json'}")

    # Step 4: Generate PFDs
    save_mermaid(spec, output_dir / "pfd.md")
    print(f"  Mermaid PFD saved to {output_dir / 'pfd.md'}")

    try:
        save_graphviz(spec, output_dir / "pfd", format="svg")
        print(f"  Graphviz PFD saved to {output_dir / 'pfd.svg'}")
    except RuntimeError as e:
        print(f"  Graphviz skipped: {e}")

    # Step 5: Run simulation
    print("\nRunning BioSTEAM simulation...")
    results = run_cornstover_simulation(spec)

    print(f"\n{'='*50}")
    print(f"  RESULTS: {spec.process_name}")
    print(f"{'='*50}")
    print(f"  MESP: ${results.mesp_usd_per_gal:.2f}/gal (${results.mesp_usd_per_kg:.2f}/kg)")
    print(f"  IRR:  {results.irr:.1%}")
    print(f"  TCI:  ${results.tci_usd/1e6:.1f}M")
    print(f"  AOC:  ${results.aoc_usd_per_yr/1e6:.1f}M/yr")
    print(f"  Product: {results.product_flow_kg_hr:.0f} kg/hr ethanol")
    print(f"  Equipment units with costs: {len(results.unit_costs)}")
    print(f"{'='*50}")

    # Step 6: Generate TEA XLSX
    xlsx_path = write_tea_xlsx(results, spec, output_dir / "tea_report.xlsx")
    print(f"\n  TEA report saved to {xlsx_path}")
    print(f"\nAll outputs in {output_dir}/:")
    for f in sorted(output_dir.iterdir()):
        print(f"  {f.name} ({f.stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    main()

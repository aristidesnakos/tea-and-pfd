# ProcessFlow AI

Natural language to process flow diagrams (PFDs) and techno-economic analysis (TEA).

## Quick Start

```bash
# Prerequisites: Python 3.12+, Graphviz
brew install graphviz  # macOS

# Install
python3.12 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Generate PFD + TEA from a template
processflow generate --template corn_stover_ethanol --output ./results/

# Generate from natural language (requires ANTHROPIC_API_KEY)
export ANTHROPIC_API_KEY=sk-...
processflow generate "corn stover to ethanol with dilute acid pretreatment" -o ./results/

# Generate from an existing ProcessSpec JSON
processflow generate --spec process_spec.json -o ./results/
```

## What It Does

ProcessFlow AI converts process descriptions into two outputs:

1. **Process Flow Diagram (PFD)** - Mermaid.js and Graphviz SVG
2. **TEA Spreadsheet (XLSX)** - 8-sheet workbook with MESP, CAPEX, OPEX, cash flow

## Architecture

```
Natural Language Description
         |
         v
[NL Parser (Claude API)] --> ProcessSpec JSON (canonical IR)
         |
         v
[Topology Engine] --> Validated + Enriched ProcessSpec
         |
    +---------+
    |         |
    v         v
[PFD Renderer]  [TEA Generator]
 Mermaid/SVG     BioSTEAM + XLSX
```

## CLI Commands

```bash
processflow generate   # Full pipeline: NL/template/spec -> PFD + TEA
processflow pfd        # PFD only from ProcessSpec
processflow tea        # TEA only from ProcessSpec
processflow templates  # List available templates
```

## Project Structure

```
src/processflow/
  schema/process_spec.py     # ProcessSpec Pydantic models (canonical IR)
  parser/nl_parser.py        # Claude API NL parser
  parser/templates/           # Reference ProcessSpec templates
  topology/engine.py         # Validation + enrichment
  topology/registry.py       # Unit operation -> BioSTEAM class mappings
  renderer/mermaid_renderer.py  # Mermaid PFD generation
  renderer/graphviz_renderer.py # Graphviz PFD generation
  tea/simulation.py          # BioSTEAM simulation wrapper
  tea/xlsx_writer.py         # 8-sheet XLSX TEA report
  cli.py                     # Click CLI
```

## Supported Processes (MVP)

- Corn stover to ethanol (validated against NREL benchmark: MESP ~$2.05/gal)

## Tests

```bash
pytest tests/ -v  # 39 tests, including NREL benchmark validation
```

## Dependencies

- **BioSTEAM** - Process simulation + TEA engine
- **Anthropic Claude API** - Natural language parsing
- **Graphviz** - PFD rendering (system binary + Python bindings)
- **openpyxl** - XLSX generation
- **Pydantic** - Schema validation

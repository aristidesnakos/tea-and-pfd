# ProcessFlow AI — Operating Manual

**Version:** 0.1.0
**Status:** Alpha — CLI only, corn stover → ethanol simulation validated
**Last updated:** 2026-03-28

---

## 1. What This Product Is

ProcessFlow AI converts process descriptions into two engineering deliverables:

1. **Process Flow Diagram (PFD)** — Graphviz SVG and/or Mermaid.js flowchart, color-coded by process section
2. **Techno-Economic Analysis (TEA)** — 8-sheet Excel workbook with CAPEX, OPEX, MESP, IRR, cash flow, and sensitivity placeholders

There is **no web interface**. The product is a Python CLI tool installed in a virtual environment. Everything runs locally on the user's machine.

---

## 2. System Requirements

| Requirement | Version |
|---|---|
| Python | 3.12+ |
| Graphviz system binary (`dot`) | Any recent version |
| Anthropic API key | Required for NL mode only |
| Operating system | macOS or Linux |

Install Graphviz:
```bash
brew install graphviz        # macOS
apt install graphviz         # Ubuntu/Debian
```

---

## 3. Installation

```bash
# Clone the repo
git clone <repo-url>
cd tea-and-pfd

# Create and activate virtualenv
python3.12 -m venv .venv
source .venv/bin/activate     # macOS/Linux

# Install in editable mode
pip install -e ".[dev]"

# Verify
processflow --version         # should print 0.1.0
```

> **Important:** Always use `.venv/bin/python` or activate the venv before running commands. The system Python does not have the package installed.

---

## 4. Input Modes

There are three ways to provide a process to the tool:

### Mode 1 — Natural Language (requires API key)

Describe the process in plain English. Claude parses it into a `ProcessSpec`.

```bash
export ANTHROPIC_API_KEY=sk-ant-...

processflow generate "corn stover to ethanol via dilute acid pretreatment, \
  enzymatic hydrolysis, and co-fermentation" -o ./results/
```

- Uses `claude-sonnet-4-20250514` by default
- Injects the full ProcessSpec JSON schema + corn stover reference example into the system prompt
- Flags which parameters were inferred vs. user-specified in `metadata.auto_filled_params`
- **Limitation:** LLM output quality varies. Always inspect the generated `process_spec.json` before trusting TEA numbers.

### Mode 2 — Template

Use a bundled reference design. Currently only one template exists.

```bash
processflow generate --template corn_stover_ethanol -o ./results/
processflow templates   # list all available templates
```

Templates live at:
```
src/processflow/parser/templates/*.json
```

To add a new template: create a valid `ProcessSpec` JSON file in that directory.

### Mode 3 — ProcessSpec JSON

Load a previously generated or manually edited spec file.

```bash
processflow generate --spec ./results/process_spec.json -o ./results/
```

This is the primary editing workflow — generate a spec from NL or template, edit the JSON, then re-run.

---

## 5. CLI Reference

### `processflow generate`

Full pipeline: input → ProcessSpec → topology validation → PFD + TEA.

```
processflow generate [DESCRIPTION] [OPTIONS]

Arguments:
  DESCRIPTION           Natural language process description (optional)

Options:
  --spec PATH           Load from existing ProcessSpec JSON
  --template TEXT       Use a built-in template name
  --output, -o PATH     Output directory [default: ./results]
  --api-key TEXT        Anthropic API key (or set ANTHROPIC_API_KEY)
  --skip-simulation     Generate PFD only, skip BioSTEAM simulation
  --format [mermaid|graphviz|both]  PFD format [default: both]
```

**Outputs written to `--output` dir:**

| File | Description |
|---|---|
| `process_spec.json` | Canonical intermediate representation — edit this to modify the process |
| `pfd.md` | Mermaid.js flowchart wrapped in Markdown |
| `pfd.svg` | Graphviz vector diagram (requires `dot` binary) |
| `tea_report.xlsx` | 8-sheet TEA workbook |

---

### `processflow pfd`

Generate only a PFD from an existing spec.

```
processflow pfd --spec process_spec.json --format mermaid --output pfd.md
processflow pfd --spec process_spec.json --format graphviz --output pfd
```

---

### `processflow tea`

Generate only a TEA workbook from an existing spec.

```
processflow tea --spec process_spec.json --output tea_report.xlsx
```

---

### `processflow templates`

List available built-in templates.

```
processflow templates
```

---

## 6. The ProcessSpec — Canonical Intermediate Representation

Every pipeline run produces `process_spec.json`. This is the central artifact — all rendering and simulation derive from it.

**Key fields:**

```json
{
  "process_name": "Corn Stover to Ethanol (NREL 2011 Design)",
  "feedstock": { "name": "corn_stover", "flow_rate_kg_hr": 83333.33 },
  "products": [{ "name": "Ethanol", "target_purity": 0.995 }],
  "units": [ ... ],      // 10 unit operations
  "streams": [ ... ],    // 12 material streams
  "reactions": [ ... ],  // stoichiometry + conversions
  "chemicals": [ ... ],  // species list
  "economic_params": { "plant_lifetime_yr": 30, "irr": 0.10, ... },
  "metadata": {
    "auto_filled_params": [ ... ]   // params inferred by the tool
  }
}
```

**To modify a process:** edit `process_spec.json` directly, then re-run:
```bash
processflow generate --spec process_spec.json -o ./results/
```

---

## 7. TEA Report Structure

The generated `tea_report.xlsx` has 8 sheets:

| Sheet | Contents |
|---|---|
| **Summary** | MESP, IRR, NPV, TCI, AOC — the headline numbers |
| **Process Inputs** | Feedstock price, flow rates, economic parameters |
| **Mass Balance** | Stream-by-stream component flows |
| **Energy Balance** | Heating, cooling, and power per unit operation |
| **Equipment Costs** | Purchase and installed cost per BioSTEAM unit (45 units for corn stover) |
| **Operating Costs** | Raw materials, utilities, fixed costs, totals |
| **Cash Flow** | Year-by-year DCF analysis over 30-year plant life |
| **Sensitivity** | Parameter table (Monte Carlo values: TBD — placeholder in v0.1.0) |

**Key output numbers (corn stover ethanol, NREL 2011 design):**

| Metric | Value | Benchmark |
|---|---|---|
| MESP | $1.90/gal | $2.15/gal (NREL) |
| TCI | $376M | — |
| AOC | $72.4M/yr | — |
| IRR | 10.0% | — |
| Ethanol production | 21,978 kg/hr | — |

---

## 8. Supported Processes (v0.1.0)

| Process | Template | NL Parsing | Full TEA Simulation |
|---|---|---|---|
| Corn stover → ethanol (NREL 2011) | `corn_stover_ethanol` | Yes | **Yes — validated** |
| Any other process | No template | Yes (PFD only) | No — raises `NotImplementedError` |

For any process other than corn stover, `--skip-simulation` is automatically needed for the TEA step. NL parsing and PFD generation work for any described process.

---

## 9. Architecture

```
User Input (NL text / JSON spec / template name)
        |
        v
[NL Parser]  ──  Claude API (claude-sonnet-4-20250514)
        |           System prompt includes: schema + unit types + corn stover example
        v
[ProcessSpec JSON]  ── canonical intermediate representation (Pydantic)
        |
        v
[Topology Engine]
  - Validates: connectivity, no duplicate IDs, no orphan units, feed/product streams present
  - Enriches: fills in missing parameters from registry defaults
        |
        +──────────────────────────────────+
        |                                  |
        v                                  v
[PFD Renderer]                    [BioSTEAM Simulation]
  Mermaid (.md)                     biorefineries.cornstover
  Graphviz (.svg)                         |
  Color-coded by section                  v
                                   [XLSX Writer]
                                     8-sheet TEA report
```

**Key files:**

```
src/processflow/
  cli.py                          # Entry point — all CLI commands
  schema/process_spec.py          # Pydantic models (ProcessSpec, UnitOperation, Stream, ...)
  parser/nl_parser.py             # Claude API integration + template loading
  parser/templates/               # Reference ProcessSpec JSON files
  topology/engine.py              # Validation + enrichment logic
  topology/registry.py            # Unit type → BioSTEAM class mappings (25 types)
  renderer/mermaid_renderer.py    # Mermaid flowchart generation
  renderer/graphviz_renderer.py   # Graphviz DOT generation
  tea/simulation.py               # BioSTEAM wrapper (corn stover only in v0.1.0)
  tea/xlsx_writer.py              # 8-sheet XLSX writer
```

---

## 10. Running Tests

```bash
source .venv/bin/activate
pytest tests/ -v
```

39 tests across 5 files:

| File | What it covers |
|---|---|
| `test_schema.py` | Pydantic validation, JSON roundtrip, invalid references |
| `test_topology.py` | Connectivity validation, duplicate IDs, orphan units, enrichment |
| `test_parser.py` | Template loading, API key validation |
| `test_renderer.py` | Mermaid output structure, subgraph sections, node shapes |
| `test_tea.py` | BioSTEAM simulation, **NREL benchmark** (MESP within ±15% of $2.15/gal) |

The NREL benchmark test (`test_mesp_benchmark`) is the most important — it fails if the simulation drifts outside 15% of the published reference value.

---

## 11. Known Limitations (v0.1.0)

1. **Simulation is corn stover only.** Any other process raises `NotImplementedError` in `tea/simulation.py`. Use `--skip-simulation` to generate PFDs for other processes.
2. **Sensitivity sheet is a placeholder.** Sheet 8 of the XLSX has parameter ranges but no computed MESP impact values. Monte Carlo analysis is not yet implemented.
3. **No web interface.** The product is CLI-only. A Streamlit or Gradio frontend does not exist yet.
4. **One template.** Only `corn_stover_ethanol` is bundled. New templates must be authored manually as ProcessSpec JSON.
5. **Graphviz system binary required.** If `dot` is not installed, SVG output is silently skipped and only the Mermaid `.md` is produced.
6. **NL parsing quality.** The LLM-generated ProcessSpec is a starting point, not a production-ready spec. Always review `process_spec.json` before using TEA numbers for decision-making.

---

## 12. What Doesn't Exist Yet (Roadmap)

| Feature | Status |
|---|---|
| Web UI (Streamlit / Gradio) | Not built |
| Generic BioSTEAM simulation (any process) | Not built |
| Sensitivity / Monte Carlo analysis | Placeholder only |
| Additional templates (sugarcane, biodiesel, etc.) | Not built |
| PDF report export | Not built |
| Multi-turn NL refinement | Not built |
| PyPI package | Not published |
| CI/CD (GitHub Actions) | Not set up |

---

## 13. Example Workflow

```bash
# 1. Activate environment
source .venv/bin/activate

# 2. Generate from template (no API key needed)
processflow generate --template corn_stover_ethanol -o ./results/

# 3. Inspect and edit the spec
open results/process_spec.json   # review auto-filled params

# 4. Re-run after edits
processflow generate --spec results/process_spec.json -o ./results/

# 5. Open the outputs
open results/pfd.svg             # PFD in browser
open results/tea_report.xlsx     # TEA in Excel

# 6. NL mode (needs API key)
export ANTHROPIC_API_KEY=sk-ant-...
processflow generate "sugarcane to ethanol via juice extraction and fermentation" \
  --skip-simulation -o ./sugarcane/
```

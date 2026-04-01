# ProcessSpec JSON Authoring Guide

This document defines the contract for writing ProcessSpec JSON files that the ProcessFlow AI system can load, render as PFDs, and run techno-economic analysis on.

## Minimum Viable JSON

```json
{
  "process_name": "My Process",
  "feedstock": {
    "name": "input_material",
    "flow_rate_kg_hr": 1000.0
  },
  "units": [
    {"id": "U-101", "type": "Reactor", "name": "Main Reactor"}
  ],
  "streams": [
    {"from_id": "feed", "to_id": "U-101"}
  ]
}
```

Five top-level fields are required: `process_name`, `feedstock`, `units`, `streams`. Everything else is optional.

## Unit Types

### Known Types (BioSTEAM-backed)

These types have default parameters and BioSTEAM class mappings for simulation:

`Mixer`, `Splitter`, `HeatExchanger`, `Pump`, `Flash`, `Distillation`, `Reactor`, `Fermentor`, `EnzymaticHydrolysis`, `Pretreatment`, `MolecularSieve`, `Evaporator`, `Filter`, `Centrifuge`, `Dryer`, `StorageTank`, `Boiler`, `Turbine`, `CoolingTower`, `WastewaterTreatment`, `Conveyor`, `ScrewFeeder`, `SizeReduction`, `Compressor`, `Adsorption`, `Crystallizer`

### Custom Types

Any string is accepted as a unit type. Use `snake_case` for custom types:

```json
{"id": "U-001", "type": "sox_prescrubber", "name": "SOx Pre-Scrubber"}
{"id": "U-002", "type": "amine_absorber", "name": "MEA Absorber Column"}
{"id": "U-003", "type": "co2_compressor", "name": "CO2 Compressor (3-stage)"}
```

Custom types render as rectangular boxes in PFDs and skip BioSTEAM simulation (generic TEA is used instead if economic data is provided).

## Unit Operation Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | yes | Unique identifier (e.g., `U-101`, `U-EH01`) |
| `type` | string | yes | Unit type (known or custom) |
| `name` | string | no | Human-readable display name |
| `section` | string | no | Process section for PFD grouping |
| `params` | object | no | Operating parameters (any key-value pairs) |

**Alias**: `parameters` is accepted as an alias for `params`.

## Stream Wiring

### Boundary Nodes

Streams connect units to each other and to boundary nodes. Any `from_id` or `to_id` that doesn't match a declared unit ID is treated as a boundary node:

| Common Boundary | Usage |
|----------------|-------|
| `feed` / `FEED` | Process feed input |
| `product` | Primary product output |
| `waste` | Waste output |
| `utility` | Utility connections |
| `VENT` | Exhaust/vent to atmosphere |
| `ENGINE` | Engine/power source |

You can use any string as a boundary node. Case doesn't matter for standard ones (`feed` = `FEED`).

### Stream Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `from_id` | string | yes | Source unit ID or boundary node |
| `to_id` | string | yes | Destination unit ID or boundary node |
| `phase` | string | no | `liquid`, `vapor`/`gas`, `solid`, `mixed` |
| `components` | list or dict | no | Component names (list) or `{name: fraction}` dict |
| `flow_rate_kg_hr` | number | no | Mass flow rate |

Both component formats are accepted:

```json
{"components": ["ethanol", "water"]}
{"components": {"CO2": 0.95, "H2O": 0.05}}
```

## Feedstock & Products

| Field | Type | Aliases | Description |
|-------|------|---------|-------------|
| `name` | string | | Material name |
| `flow_rate_kg_hr` | number | | Mass flow rate (required for feedstock) |
| `price_usd_per_ton` | number | `price_per_ton` | Price in USD/ton |
| `expected_yield_kg_hr` | number | `yield_kg_hr` | Expected production rate (products only) |
| `purity` | number | | Target purity 0-1 (products only) |

Extra fields (e.g., `notes`) are preserved but not used by the calculator.

## Chemicals

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | yes | Chemical name |
| `role` | string | yes | `feedstock`, `product`, `intermediate`, `waste`, `utility`, `catalyst` |
| `formula` | string | no | Molecular formula |
| `cas_number` | string | no | CAS registry number |

Extra fields like `price_per_kg`, `consumption_rate_kg_hr`, `initial_charge_kg` are preserved.

## Economic Data (for Generic TEA)

The generic TEA calculator needs three fields in the `economic` block:

```json
"economic": {
  "capex_usd": 8000000,
  "annual_costs": {
    "maintenance": 150000,
    "solvent": 95000,
    "fuel_penalty": 445500,
    "storage": 100980
  },
  "annual_revenues": {
    "ets_savings": 167580
  },
  "operating_days": 300,
  "plant_lifetime_years": 15,
  "discount_rate": 0.08
}
```

### TEA Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `capex_usd` | number | null | Total capital expenditure |
| `annual_costs` | object | `{}` | Named annual cost items |
| `annual_revenues` | object | `{}` | Named annual revenue/savings items |
| `operating_days` | integer | 330 | Operating days per year |
| `plant_lifetime_years` | integer | 20 | Project lifetime |
| `discount_rate` | number | 0.10 | Discount rate (0-1) |
| `income_tax_rate` | number | 0.21 | Income tax rate (alias: `tax_rate`) |

Extra fields (e.g., `notes`, `capex` breakdown notes) are preserved.

### What the Calculator Computes

| Metric | Formula | Required Input |
|--------|---------|----------------|
| Capital Recovery Factor (CRF) | `r(1+r)^n / ((1+r)^n - 1)` | `discount_rate`, `plant_lifetime_years` |
| Annualized CAPEX | `capex_usd * CRF` | `capex_usd` |
| Total Annual OPEX | `sum(annual_costs)` | `annual_costs` |
| Total Annual Revenue | `sum(annual_revenues)` | `annual_revenues` |
| Net Annual Cash Flow | `revenue - opex` | both |
| NPV | `-CAPEX + sum(net_cf / (1+r)^t)` | all above |
| Simple Payback | `CAPEX / (revenue - opex)` | net > 0 |
| LCOP | `(ann_capex + opex) / annual_output` | first product's `expected_yield_kg_hr` |

### LCOP Calculation

LCOP (Levelized Cost of Product) is computed automatically if the first product has `expected_yield_kg_hr` set:

```
annual_output_tonnes = expected_yield_kg_hr * operating_days * 24 / 1000
LCOP = (annualized_capex + total_annual_costs) / annual_output_tonnes
```

## Reactions (Optional)

```json
"reactions": [
  {
    "unit_id": "U-CC01",
    "reactants": ["CO2", "MEA"],
    "products": ["MEA-CO2_carbamate"],
    "conversion": 0.40,
    "stoichiometry": "CO2 + 2 MEA -> MEA-CO2-carbamate + MEA-H+"
  }
]
```

Extra fields like `name` and `notes` are preserved.

## Metadata (Optional)

```json
"metadata": {
  "source": "user",
  "references": ["NREL 2011 report"],
  "key_finding": "NPV is negative at current prices"
}
```

All extra fields are preserved.

## Field Name Flexibility

The preprocessor normalizes these field names before validation:

| You Write | System Reads |
|-----------|-------------|
| `price_per_ton` | `price_usd_per_ton` |
| `yield_kg_hr` | `expected_yield_kg_hr` |
| `parameters` | `params` |
| `tax_rate` | `income_tax_rate` |

## Output

When a ProcessSpec JSON is submitted:

1. **PFD** — Mermaid flowchart (always generated)
2. **TEA Report** — XLSX workbook:
   - For known processes (corn stover ethanol): full BioSTEAM simulation with MESP, equipment costs, energy balance
   - For custom processes with `capex_usd`/`annual_costs`: generic TEA with NPV, payback, LCOP, cash flow table
   - For custom processes without economic data: PFD only, simulation skipped

"""Generic TEA Calculator — NPV, payback, LCOP from JSON-specified CAPEX/OPEX.

Unlike simulation.py which requires BioSTEAM, this module computes TEA metrics
directly from economic data provided in the ProcessSpec JSON. This enables
TEA for any process type (maritime CCS, DAC, industrial chemistry, etc.)
without needing a process simulator.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from processflow.schema.process_spec import ProcessSpec


@dataclass
class GenericTEAResults:
    """Results from generic (non-simulation) TEA calculation."""

    # Key metrics (required — no defaults)
    npv_usd: float
    simple_payback_years: float | None
    lcop_usd_per_unit: float | None
    capex_usd: float
    annualized_capex_usd: float
    total_annual_costs_usd: float
    total_annual_revenues_usd: float
    net_annual_cashflow_usd: float

    # Fields with defaults
    lcop_unit: str = ""  # e.g., "$/ton CO2"
    annual_cost_items: dict[str, float] = field(default_factory=dict)
    annual_revenue_items: dict[str, float] = field(default_factory=dict)
    discount_rate: float = 0.10
    plant_lifetime_years: int = 20
    operating_days: int = 330
    cashflow_table: pd.DataFrame | None = None

    # For compatibility with job_runner metric extraction
    tci_usd: float = 0.0
    aoc_usd_per_yr: float = 0.0


def capital_recovery_factor(rate: float, years: int) -> float:
    """CRF = r(1+r)^n / ((1+r)^n - 1).

    At zero discount rate, CRF simplifies to 1/n (straight-line).
    """
    if rate == 0:
        return 1.0 / years
    factor = (1 + rate) ** years
    return rate * factor / (factor - 1)


def run_generic_tea(spec: ProcessSpec) -> GenericTEAResults:
    """Compute TEA metrics from ProcessSpec economic data.

    Reads capex_usd, annual_costs, and annual_revenues from the economic block.
    Computes NPV, simple payback, and optionally LCOP if product output is
    available.

    Args:
        spec: ProcessSpec with populated economic fields

    Returns:
        GenericTEAResults with computed metrics and cash flow table
    """
    eco = spec.economic

    capex = eco.capex_usd or 0.0
    r = eco.discount_rate
    n = eco.plant_lifetime_years

    # Annualized CAPEX via capital recovery factor
    crf = capital_recovery_factor(r, n)
    annualized_capex = capex * crf

    # Sum annual costs and revenues
    total_costs = sum(eco.annual_costs.values())
    total_revenues = sum(eco.annual_revenues.values())

    # Net annual operating cash flow (revenues minus costs, before CAPEX)
    net_operating = total_revenues - total_costs

    # Simple payback (CAPEX / net annual operating surplus)
    payback = capex / net_operating if net_operating > 0 else None

    # NPV = -CAPEX + sum of discounted net operating cash flows
    npv = -capex
    cf_rows = []
    cumulative_npv = -capex
    for year in range(1, n + 1):
        discount_factor = 1 / (1 + r) ** year
        discounted = net_operating * discount_factor
        cumulative_npv += discounted
        cf_rows.append({
            "Year": year,
            "Revenue ($)": total_revenues,
            "Costs ($)": total_costs,
            "Net Cash Flow ($)": net_operating,
            "Discount Factor": discount_factor,
            "Discounted CF ($)": discounted,
            "Cumulative NPV ($)": cumulative_npv,
        })

    npv = cumulative_npv
    cashflow_df = pd.DataFrame(cf_rows)

    # LCOP — levelized cost of product
    # Try to infer annual product output from the first product's yield
    lcop = None
    lcop_unit = ""
    annual_output = None

    if spec.products:
        primary = spec.products[0]
        if primary.expected_yield_kg_hr and primary.expected_yield_kg_hr > 0:
            annual_output = primary.expected_yield_kg_hr * eco.operating_days * 24 / 1000  # tonnes/yr
            lcop = (annualized_capex + total_costs) / annual_output if annual_output > 0 else None
            lcop_unit = "$/tonne"

    return GenericTEAResults(
        npv_usd=npv,
        simple_payback_years=payback,
        lcop_usd_per_unit=lcop,
        lcop_unit=lcop_unit,
        capex_usd=capex,
        annualized_capex_usd=annualized_capex,
        total_annual_costs_usd=total_costs,
        total_annual_revenues_usd=total_revenues,
        net_annual_cashflow_usd=net_operating,
        annual_cost_items=dict(eco.annual_costs),
        annual_revenue_items=dict(eco.annual_revenues),
        discount_rate=r,
        plant_lifetime_years=n,
        operating_days=eco.operating_days,
        cashflow_table=cashflow_df,
        tci_usd=capex,
        aoc_usd_per_yr=total_costs,
    )

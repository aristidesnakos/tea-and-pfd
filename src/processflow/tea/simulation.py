"""BioSTEAM Simulation Wrapper — runs process simulation and extracts TEA results.

For MVP, this primarily delegates to pre-built biorefinery models in the
`biorefineries` package, with parameter overrides from the ProcessSpec.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from processflow.schema.process_spec import ProcessSpec

# Ethanol density for unit conversion
ETHANOL_DENSITY_KG_PER_GAL = 0.789 * 3.78541  # ~2.987 kg/gal


@dataclass
class UnitCost:
    """Cost breakdown for a single unit operation."""

    id: str
    name: str
    unit_class: str
    purchase_cost_usd: float
    installed_cost_usd: float


@dataclass
class StreamData:
    """Mass balance data for a single stream."""

    id: str
    phase: str
    total_flow_kg_hr: float
    components: dict[str, float]  # component name -> mass flow kg/hr


@dataclass
class UtilityData:
    """Utility consumption for a unit."""

    unit_id: str
    unit_name: str
    heating_duty_kW: float
    cooling_duty_kW: float
    power_kW: float


@dataclass
class SimulationResults:
    """Complete results from a BioSTEAM simulation run."""

    # Key metrics
    mesp_usd_per_kg: float
    mesp_usd_per_gal: float
    irr: float
    npv_usd: float

    # Capital costs
    installed_equipment_cost_usd: float
    dpi_usd: float  # Direct Permanent Investment
    tdc_usd: float  # Total Depreciable Capital
    fci_usd: float  # Fixed Capital Investment
    tci_usd: float  # Total Capital Investment

    # Operating costs
    material_cost_usd_per_yr: float
    utility_cost_usd_per_yr: float
    foc_usd_per_yr: float  # Fixed Operating Costs
    aoc_usd_per_yr: float  # Annual Operating Cost

    # Operating parameters
    operating_hours: float
    operating_days: float
    plant_lifetime_years: int

    # Detailed breakdowns
    unit_costs: list[UnitCost] = field(default_factory=list)
    streams: list[StreamData] = field(default_factory=list)
    utilities: list[UtilityData] = field(default_factory=list)
    cashflow_table: pd.DataFrame | None = None

    # Production
    product_flow_kg_hr: float = 0.0
    product_name: str = ""
    feedstock_flow_kg_hr: float = 0.0


def run_cornstover_simulation(
    spec: ProcessSpec | None = None,
) -> SimulationResults:
    """Run the NREL corn stover to ethanol biorefinery simulation.

    This uses BioSTEAM's built-in cornstover biorefinery model. If a ProcessSpec
    is provided, it applies parameter overrides where possible.

    Args:
        spec: Optional ProcessSpec with parameter overrides

    Returns:
        SimulationResults with full TEA data
    """
    warnings.filterwarnings("ignore")

    from biorefineries.cornstover import Biorefinery

    br = Biorefinery()
    tea = br.tea
    sys = br.sys

    # Apply feedstock rate override if specified
    if spec and spec.feedstock.flow_rate_kg_hr:
        br.cornstover.F_mass = spec.feedstock.flow_rate_kg_hr

    # Apply economic parameter overrides
    if spec:
        eco = spec.economic
        if eco.operating_days != 330:
            tea.operating_days = eco.operating_days
        if eco.discount_rate != 0.10:
            tea.IRR = eco.discount_rate

    # Solve for MESP
    mesp = tea.solve_price(br.ethanol)
    mesp_gal = mesp * ETHANOL_DENSITY_KG_PER_GAL

    # Extract unit costs
    unit_costs = []
    for unit in sys.units:
        purchase = sum(unit.purchase_costs.values()) if hasattr(unit, "purchase_costs") else 0
        installed = unit.installed_cost if hasattr(unit, "installed_cost") else 0
        if purchase > 0 or installed > 0:
            unit_costs.append(UnitCost(
                id=unit.ID,
                name=type(unit).__name__,
                unit_class=type(unit).__name__,
                purchase_cost_usd=purchase,
                installed_cost_usd=installed,
            ))

    # Extract utility data
    utilities = []
    for unit in sys.units:
        heating = getattr(unit, "heat_utilities", [])
        h_duty = sum(hu.duty for hu in heating if hu.duty > 0) / 3600 if heating else 0  # kJ/hr -> kW
        c_duty = sum(abs(hu.duty) for hu in heating if hu.duty < 0) / 3600 if heating else 0
        power = getattr(unit, "power_utility", None)
        p_kw = power.consumption if power else 0
        if h_duty > 0 or c_duty > 0 or p_kw > 0:
            utilities.append(UtilityData(
                unit_id=unit.ID,
                unit_name=type(unit).__name__,
                heating_duty_kW=h_duty,
                cooling_duty_kW=c_duty,
                power_kW=p_kw,
            ))

    # Get cashflow table
    cf_table = tea.get_cashflow_table()

    # Compute AOC
    aoc = tea.material_cost + tea.utility_cost + tea.FOC

    results = SimulationResults(
        mesp_usd_per_kg=mesp,
        mesp_usd_per_gal=mesp_gal,
        irr=tea.IRR,
        npv_usd=tea.NPV,
        installed_equipment_cost_usd=tea.installed_equipment_cost,
        dpi_usd=tea.DPI,
        tdc_usd=tea.TDC,
        fci_usd=tea.FCI,
        tci_usd=tea.TCI,
        material_cost_usd_per_yr=tea.material_cost,
        utility_cost_usd_per_yr=tea.utility_cost,
        foc_usd_per_yr=tea.FOC,
        aoc_usd_per_yr=aoc,
        operating_hours=tea.operating_hours,
        operating_days=tea.operating_days,
        plant_lifetime_years=int(tea.duration[1] - tea.duration[0]),
        unit_costs=unit_costs,
        utilities=utilities,
        cashflow_table=cf_table,
        product_flow_kg_hr=br.ethanol.F_mass,
        product_name="Ethanol",
        feedstock_flow_kg_hr=br.cornstover.F_mass,
    )

    return results


def run_simulation(spec: ProcessSpec) -> SimulationResults:
    """Run simulation for a ProcessSpec, dispatching to the appropriate biorefinery model.

    For MVP, only corn stover ethanol is supported via the dedicated BioSTEAM model.
    Other processes will raise NotImplementedError.

    Args:
        spec: Validated and enriched ProcessSpec

    Returns:
        SimulationResults

    Raises:
        NotImplementedError: If the process type is not yet supported
    """
    name_lower = spec.process_name.lower()

    if "corn stover" in name_lower and "ethanol" in name_lower:
        return run_cornstover_simulation(spec)

    # Check for other supported processes (Phase 2)
    raise NotImplementedError(
        f"Process '{spec.process_name}' is not yet supported for BioSTEAM simulation. "
        "Currently supported: corn stover to ethanol. "
        "You can still generate PFDs and template-based TEA spreadsheets."
    )

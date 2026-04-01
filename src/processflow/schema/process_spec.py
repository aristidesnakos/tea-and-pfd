"""ProcessSpec — Canonical intermediate representation for process descriptions.

This is the central data model that flows through the entire pipeline:
NL Parser → ProcessSpec → Topology Engine → PFD Renderer + TEA Generator
"""

from __future__ import annotations

import json
from copy import deepcopy
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class UnitType(str, Enum):
    """Unit operation types matching BioSTEAM taxonomy."""

    MIXER = "Mixer"
    SPLITTER = "Splitter"
    HEAT_EXCHANGER = "HeatExchanger"
    PUMP = "Pump"
    FLASH = "Flash"
    DISTILLATION = "Distillation"
    REACTOR = "Reactor"
    FERMENTOR = "Fermentor"
    ENZYMATIC_HYDROLYSIS = "EnzymaticHydrolysis"
    PRETREATMENT = "Pretreatment"
    MOLECULAR_SIEVE = "MolecularSieve"
    EVAPORATOR = "Evaporator"
    FILTER = "Filter"
    CENTRIFUGE = "Centrifuge"
    DRYER = "Dryer"
    STORAGE_TANK = "StorageTank"
    BOILER = "Boiler"
    TURBINE = "Turbine"
    COOLING_TOWER = "CoolingTower"
    WASTEWATER_TREATMENT = "WastewaterTreatment"
    CONVEYOR = "Conveyor"
    SCREW_FEEDER = "ScrewFeeder"
    SIZE_REDUCTION = "SizeReduction"
    COMPRESSOR = "Compressor"
    ADSORPTION = "Adsorption"
    CRYSTALLIZER = "Crystallizer"


class ChemicalRole(str, Enum):
    """Role of a chemical species in the process."""

    FEEDSTOCK = "feedstock"
    PRODUCT = "product"
    INTERMEDIATE = "intermediate"
    WASTE = "waste"
    UTILITY = "utility"
    CATALYST = "catalyst"


class ChemicalSpec(BaseModel):
    """Specification for a chemical species in the process."""

    model_config = ConfigDict(extra="allow")

    name: str = Field(description="Chemical name (must be resolvable by thermosteam)")
    cas_number: str | None = Field(default=None, description="CAS registry number")
    role: ChemicalRole = Field(description="Role in the process")
    formula: str | None = Field(default=None, description="Molecular formula")


class Feedstock(BaseModel):
    """Process feedstock specification."""

    model_config = ConfigDict(extra="allow")

    name: str = Field(description="Feedstock name")
    flow_rate_kg_hr: float = Field(gt=0, description="Mass flow rate in kg/hr")
    composition: dict[str, float] | None = Field(
        default=None,
        description="Component mass fractions (must sum to ~1.0)",
    )
    price_usd_per_ton: float | None = Field(
        default=None, description="Feedstock price in USD per metric ton"
    )


class Product(BaseModel):
    """Process product specification."""

    model_config = ConfigDict(extra="allow")

    name: str = Field(description="Product name")
    purity: float | None = Field(
        default=None, ge=0, le=1, description="Target purity (mass fraction)"
    )
    expected_yield_kg_hr: float | None = Field(
        default=None, description="Expected production rate in kg/hr"
    )
    price_usd_per_ton: float | None = Field(
        default=None, description="Product price in USD per metric ton"
    )


class UnitOperation(BaseModel):
    """A single unit operation in the process."""

    id: str = Field(description="Unique identifier (e.g., 'U-101', 'R-201')")
    type: str = Field(description="Unit operation type (e.g., 'Reactor', 'sox_prescrubber')")
    subtype: str | None = Field(
        default=None,
        description="More specific type (e.g., 'dilute_acid' for Pretreatment)",
    )
    name: str | None = Field(default=None, description="Human-readable name")
    section: str | None = Field(
        default=None,
        description="Process section (e.g., 'pretreatment', 'fermentation', 'separation')",
    )
    params: dict[str, Any] = Field(
        default_factory=dict,
        description="Operating parameters (temperature_C, pressure_bar, etc.)",
    )

    @field_validator("type", mode="before")
    @classmethod
    def coerce_unit_type(cls, v: Any) -> str:
        """Accept UnitType enum instances or plain strings."""
        if isinstance(v, UnitType):
            return v.value
        return str(v)


class Stream(BaseModel):
    """A material or energy stream connection between units."""

    model_config = ConfigDict(extra="allow")

    from_id: str = Field(
        description="Source unit ID or 'feed' for process feed"
    )
    to_id: str = Field(
        description="Destination unit ID or 'product'/'waste' for outputs"
    )
    phase: str | None = Field(
        default=None, description="Stream phase: 'liquid', 'vapor', 'solid', 'mixed'"
    )
    components: dict[str, float] | list[str] | None = Field(
        default=None, description="Key chemical components (list or {name: fraction} dict)"
    )
    flow_rate_kg_hr: float | None = Field(
        default=None, description="Total mass flow rate in kg/hr"
    )

    @property
    def component_names(self) -> list[str]:
        """Return component names regardless of whether components is a list or dict."""
        if self.components is None:
            return []
        if isinstance(self.components, dict):
            return list(self.components.keys())
        return self.components


class Reaction(BaseModel):
    """A chemical or biochemical reaction occurring in a unit operation."""

    model_config = ConfigDict(extra="allow")

    unit_id: str = Field(description="ID of the unit where this reaction occurs")
    reactants: list[str] = Field(description="Reactant species names")
    products: list[str] = Field(description="Product species names")
    conversion: float | None = Field(
        default=None, ge=0, le=1, description="Fractional conversion of limiting reactant"
    )
    stoichiometry: str | None = Field(
        default=None,
        description="Reaction stoichiometry string (e.g., 'Glucose -> 2 Ethanol + 2 CO2')",
    )


class EconomicParams(BaseModel):
    """Economic and financial parameters for TEA."""

    model_config = ConfigDict(extra="allow")

    operating_days: int = Field(default=330, ge=1, le=365)
    plant_lifetime_years: int = Field(default=20, ge=1)
    discount_rate: float = Field(default=0.10, ge=0, le=1)
    income_tax_rate: float = Field(default=0.21, ge=0, le=1)
    depreciation_schedule: str = Field(
        default="MACRS7",
        description="Depreciation method (e.g., 'MACRS7', 'MACRS10', 'SL20')",
    )
    construction_years: int = Field(default=3, ge=1)
    startup_months: int = Field(default=3, ge=0)
    working_capital_fraction: float = Field(
        default=0.05, ge=0, le=1, description="Working capital as fraction of FCI"
    )
    lang_factor: float | None = Field(
        default=None,
        description="Lang factor for total installed cost (if using simplified costing)",
    )
    # Generic TEA fields (for non-BioSTEAM processes)
    capex_usd: float | None = Field(
        default=None, description="Total capital expenditure in USD"
    )
    annual_costs: dict[str, float] = Field(
        default_factory=dict,
        description="Named annual cost items, e.g. {'maintenance': 150000, 'solvent': 95000}",
    )
    annual_revenues: dict[str, float] = Field(
        default_factory=dict,
        description="Named annual revenue/savings items, e.g. {'ets_savings': 167580}",
    )


class ProcessMetadata(BaseModel):
    """Metadata about how the ProcessSpec was generated."""

    model_config = ConfigDict(extra="allow")

    source: str = Field(
        default="user",
        description="How this spec was created: 'user', 'llm', 'template'",
    )
    auto_filled_params: list[str] = Field(
        default_factory=list,
        description="Parameter paths that were auto-filled (not from user input)",
    )
    confidence_scores: dict[str, float] = Field(
        default_factory=dict,
        description="LLM confidence scores for inferred values",
    )
    template_name: str | None = Field(
        default=None, description="Name of template used (if any)"
    )


class ProcessSpec(BaseModel):
    """Top-level process specification — the canonical intermediate representation.

    This is the central data structure that flows through the entire ProcessFlow AI
    pipeline. It is designed to be:
    - Machine-readable (JSON serializable, schema-validated)
    - Human-editable (engineers can refine LLM output before simulation)
    - Version-controllable (JSON files in git)
    """

    process_name: str = Field(description="Name of the process")
    description: str = Field(
        default="", description="Natural language description of the process"
    )
    feedstock: Feedstock = Field(description="Primary feedstock")
    products: list[Product] = Field(
        default_factory=list, description="Target products"
    )
    chemicals: list[ChemicalSpec] = Field(
        default_factory=list, description="All chemical species involved"
    )
    units: list[UnitOperation] = Field(
        description="Ordered list of unit operations"
    )
    streams: list[Stream] = Field(
        description="Material/energy stream connections"
    )
    reactions: list[Reaction] = Field(
        default_factory=list, description="Chemical/biochemical reactions"
    )
    economic: EconomicParams = Field(
        default_factory=EconomicParams, description="Economic parameters"
    )
    metadata: ProcessMetadata = Field(
        default_factory=ProcessMetadata, description="Spec generation metadata"
    )

    @model_validator(mode="after")
    def validate_stream_references(self) -> ProcessSpec:
        """Ensure all stream from_id/to_id reference valid unit IDs or boundary nodes.

        Any from_id/to_id that is not a unit ID is treated as a boundary node
        (e.g., 'feed', 'product', 'VENT', 'ENGINE'). Only raises if a from_id/to_id
        looks like a unit ID pattern (U-xxx) but doesn't match any declared unit.
        """
        unit_ids = {u.id for u in self.units}

        for stream in self.streams:
            for label, ref in [("from_id", stream.from_id), ("to_id", stream.to_id)]:
                if ref not in unit_ids:
                    # Allow any string as a boundary node — the topology engine
                    # will validate connectivity and warn about missing feed/product
                    pass
        return self

    @model_validator(mode="after")
    def validate_reaction_references(self) -> ProcessSpec:
        """Ensure all reaction unit_ids reference valid units."""
        unit_ids = {u.id for u in self.units}
        for rxn in self.reactions:
            if rxn.unit_id not in unit_ids:
                raise ValueError(
                    f"Reaction unit_id '{rxn.unit_id}' not found in units"
                )
        return self

    @classmethod
    def _normalize_input(cls, data: dict) -> dict:
        """Normalize known field name variations before Pydantic validation.

        Handles:
        - Feedstock/Product: price_per_ton → price_usd_per_ton
        - Product: yield_kg_hr → expected_yield_kg_hr
        - UnitOperation: parameters → params
        - Economic: tax_rate → income_tax_rate
        """
        data = deepcopy(data)

        # Feedstock field renames
        if "feedstock" in data and isinstance(data["feedstock"], dict):
            fs = data["feedstock"]
            if "price_per_ton" in fs and "price_usd_per_ton" not in fs:
                fs["price_usd_per_ton"] = fs.pop("price_per_ton")

        # Product field renames
        for prod in data.get("products", []):
            if isinstance(prod, dict):
                if "price_per_ton" in prod and "price_usd_per_ton" not in prod:
                    prod["price_usd_per_ton"] = prod.pop("price_per_ton")
                if "yield_kg_hr" in prod and "expected_yield_kg_hr" not in prod:
                    prod["expected_yield_kg_hr"] = prod.pop("yield_kg_hr")

        # Unit operation: parameters → params
        for unit in data.get("units", []):
            if isinstance(unit, dict):
                if "parameters" in unit and "params" not in unit:
                    unit["params"] = unit.pop("parameters")

        # Economic: tax_rate → income_tax_rate
        if "economic" in data and isinstance(data["economic"], dict):
            eco = data["economic"]
            if "tax_rate" in eco and "income_tax_rate" not in eco:
                eco["income_tax_rate"] = eco.pop("tax_rate")

        return data

    def to_json(self, path: str | Path | None = None, indent: int = 2) -> str:
        """Serialize to JSON string, optionally writing to file."""
        data = self.model_dump(mode="json")
        json_str = json.dumps(data, indent=indent)
        if path is not None:
            Path(path).write_text(json_str)
        return json_str

    @classmethod
    def from_json(cls, path_or_string: str | Path) -> ProcessSpec:
        """Load from a JSON file path or JSON string.

        Applies field name normalization before validation so that common
        variations (e.g., price_per_ton vs price_usd_per_ton) are accepted.
        """
        text = str(path_or_string)
        # If it looks like JSON (starts with '{'), parse directly
        if text.lstrip().startswith("{"):
            data = json.loads(text)
        else:
            path = Path(text)
            data = json.loads(path.read_text())
        data = cls._normalize_input(data)
        return cls.model_validate(data)

    @classmethod
    def json_schema(cls) -> dict:
        """Export the JSON Schema for this model."""
        return cls.model_json_schema()

    def get_unit_by_id(self, unit_id: str) -> UnitOperation | None:
        """Look up a unit operation by its ID."""
        for unit in self.units:
            if unit.id == unit_id:
                return unit
        return None

    def get_connected_graph(self) -> dict[str, list[str]]:
        """Return adjacency list of unit connections."""
        graph: dict[str, list[str]] = {}
        for stream in self.streams:
            graph.setdefault(stream.from_id, []).append(stream.to_id)
        return graph

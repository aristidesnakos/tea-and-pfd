"""Unit Operation Registry — maps ProcessSpec unit types to BioSTEAM classes.

Each entry provides the BioSTEAM class path, default parameters sourced from
published TEA studies, and metadata about the unit.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from processflow.schema.process_spec import UnitType


@dataclass
class UnitRegistryEntry:
    """Registry entry mapping a ProcessSpec unit type to BioSTEAM."""

    unit_type: UnitType
    biosteam_class: str  # Dotted path, e.g., 'biosteam.units.Mixer'
    default_params: dict[str, Any] = field(default_factory=dict)
    description: str = ""
    subtypes: dict[str, dict[str, Any]] = field(default_factory=dict)


# The registry: maps UnitType enum values to their BioSTEAM configuration.
# Default parameters are sourced from NREL design reports and BioSTEAM examples.
UNIT_REGISTRY: dict[UnitType, UnitRegistryEntry] = {
    UnitType.MIXER: UnitRegistryEntry(
        unit_type=UnitType.MIXER,
        biosteam_class="biosteam.units.Mixer",
        description="Stream mixer — combines multiple input streams",
    ),
    UnitType.SPLITTER: UnitRegistryEntry(
        unit_type=UnitType.SPLITTER,
        biosteam_class="biosteam.units.Splitter",
        default_params={"split": 0.5},
        description="Stream splitter — divides a stream by ratio",
    ),
    UnitType.HEAT_EXCHANGER: UnitRegistryEntry(
        unit_type=UnitType.HEAT_EXCHANGER,
        biosteam_class="biosteam.units.HXutility",
        default_params={"T": 350},
        description="Heat exchanger with utility heating/cooling",
    ),
    UnitType.PUMP: UnitRegistryEntry(
        unit_type=UnitType.PUMP,
        biosteam_class="biosteam.units.Pump",
        default_params={"P": 101325},
        description="Liquid pump",
    ),
    UnitType.FLASH: UnitRegistryEntry(
        unit_type=UnitType.FLASH,
        biosteam_class="biosteam.units.Flash",
        default_params={"T": 373.15, "P": 101325},
        description="Vapor-liquid flash separator",
    ),
    UnitType.DISTILLATION: UnitRegistryEntry(
        unit_type=UnitType.DISTILLATION,
        biosteam_class="biosteam.units.BinaryDistillation",
        default_params={"LHK": ("Ethanol", "Water"), "k": 1.25, "Rmin": 0.6},
        description="Distillation column for binary or multi-component separation",
        subtypes={
            "beer_column": {
                "LHK": ("Ethanol", "Water"),
                "y_top": 0.30,
                "x_bot": 0.0001,
            },
            "rectification": {
                "LHK": ("Ethanol", "Water"),
                "y_top": 0.90,
                "x_bot": 0.01,
            },
        },
    ),
    UnitType.REACTOR: UnitRegistryEntry(
        unit_type=UnitType.REACTOR,
        biosteam_class="biosteam.units.StirredTankReactor",
        default_params={"tau": 1.0, "T": 323.15},
        description="Continuous stirred-tank reactor",
        subtypes={
            "neutralization": {"tau": 0.5, "T": 323.15},
        },
    ),
    UnitType.FERMENTOR: UnitRegistryEntry(
        unit_type=UnitType.FERMENTOR,
        biosteam_class="biosteam.units.StirredTankReactor",
        default_params={"tau": 36.0, "T": 305.15},
        description="Fermentation vessel",
        subtypes={
            "co_fermentation": {"tau": 36.0, "T": 305.15},
            "anaerobic": {"tau": 48.0, "T": 310.15},
        },
    ),
    UnitType.ENZYMATIC_HYDROLYSIS: UnitRegistryEntry(
        unit_type=UnitType.ENZYMATIC_HYDROLYSIS,
        biosteam_class="biosteam.units.StirredTankReactor",
        default_params={"tau": 84.0, "T": 321.15},
        description="Enzymatic hydrolysis (saccharification) reactor",
    ),
    UnitType.PRETREATMENT: UnitRegistryEntry(
        unit_type=UnitType.PRETREATMENT,
        biosteam_class="biosteam.units.StirredTankReactor",
        default_params={"tau": 0.083, "T": 431.15, "P": 550000},
        description="Biomass pretreatment reactor",
        subtypes={
            "dilute_acid": {"tau": 0.083, "T": 431.15, "P": 550000},
            "steam_explosion": {"tau": 0.167, "T": 473.15, "P": 1500000},
            "alkaline": {"tau": 1.0, "T": 393.15},
        },
    ),
    UnitType.MOLECULAR_SIEVE: UnitRegistryEntry(
        unit_type=UnitType.MOLECULAR_SIEVE,
        biosteam_class="biosteam.units.MolecularSieve",
        default_params={},
        description="Molecular sieve for dehydration (e.g., ethanol to 99.5%)",
    ),
    UnitType.EVAPORATOR: UnitRegistryEntry(
        unit_type=UnitType.EVAPORATOR,
        biosteam_class="biosteam.units.MultiEffectEvaporator",
        default_params={"n_effects": 3},
        description="Multi-effect evaporator for concentration",
    ),
    UnitType.FILTER: UnitRegistryEntry(
        unit_type=UnitType.FILTER,
        biosteam_class="biosteam.units.SolidsCentrifuge",
        default_params={},
        description="Solid-liquid separation filter",
    ),
    UnitType.CENTRIFUGE: UnitRegistryEntry(
        unit_type=UnitType.CENTRIFUGE,
        biosteam_class="biosteam.units.SolidsCentrifuge",
        default_params={},
        description="Centrifuge for solid-liquid separation",
    ),
    UnitType.DRYER: UnitRegistryEntry(
        unit_type=UnitType.DRYER,
        biosteam_class="biosteam.units.DrumDryer",
        default_params={},
        description="Dryer for moisture removal",
    ),
    UnitType.STORAGE_TANK: UnitRegistryEntry(
        unit_type=UnitType.STORAGE_TANK,
        biosteam_class="biosteam.units.StorageTank",
        default_params={"tau": 24.0},
        description="Storage tank",
    ),
    UnitType.BOILER: UnitRegistryEntry(
        unit_type=UnitType.BOILER,
        biosteam_class="biosteam.units.BoilerTurbogenerator",
        default_params={},
        description="Boiler / combined heat and power system",
    ),
    UnitType.TURBINE: UnitRegistryEntry(
        unit_type=UnitType.TURBINE,
        biosteam_class="biosteam.units.Turbine",
        default_params={},
        description="Steam or gas turbine for power generation",
    ),
    UnitType.WASTEWATER_TREATMENT: UnitRegistryEntry(
        unit_type=UnitType.WASTEWATER_TREATMENT,
        biosteam_class="biosteam.units.AnaerobicDigestion",
        default_params={},
        description="Wastewater treatment system",
        subtypes={
            "anaerobic_aerobic": {},
            "aerobic": {},
        },
    ),
    UnitType.SIZE_REDUCTION: UnitRegistryEntry(
        unit_type=UnitType.SIZE_REDUCTION,
        biosteam_class="biosteam.units.HammerMill",
        default_params={},
        description="Size reduction equipment (mill, grinder)",
    ),
    UnitType.COMPRESSOR: UnitRegistryEntry(
        unit_type=UnitType.COMPRESSOR,
        biosteam_class="biosteam.units.IsentropicCompressor",
        default_params={"P": 1000000},
        description="Gas compressor",
    ),
}


def get_registry_entry(unit_type: UnitType) -> UnitRegistryEntry | None:
    """Look up a registry entry by unit type."""
    return UNIT_REGISTRY.get(unit_type)


def get_default_params(unit_type: UnitType, subtype: str | None = None) -> dict[str, Any]:
    """Get default parameters for a unit type, optionally with subtype overrides."""
    entry = UNIT_REGISTRY.get(unit_type)
    if entry is None:
        return {}
    params = dict(entry.default_params)
    if subtype and subtype in entry.subtypes:
        params.update(entry.subtypes[subtype])
    return params


def list_supported_types() -> list[UnitType]:
    """List all unit types with registry entries."""
    return list(UNIT_REGISTRY.keys())

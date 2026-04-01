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

    unit_type: str
    biosteam_class: str  # Dotted path, e.g., 'biosteam.units.Mixer'
    default_params: dict[str, Any] = field(default_factory=dict)
    description: str = ""
    subtypes: dict[str, dict[str, Any]] = field(default_factory=dict)


# The registry: maps unit type strings to their BioSTEAM configuration.
# Default parameters are sourced from NREL design reports and BioSTEAM examples.
# Keys use UnitType enum .value strings for known types; custom types use raw strings.
UNIT_REGISTRY: dict[str, UnitRegistryEntry] = {
    UnitType.MIXER.value: UnitRegistryEntry(
        unit_type=UnitType.MIXER.value,
        biosteam_class="biosteam.units.Mixer",
        description="Stream mixer — combines multiple input streams",
    ),
    UnitType.SPLITTER.value: UnitRegistryEntry(
        unit_type=UnitType.SPLITTER.value,
        biosteam_class="biosteam.units.Splitter",
        default_params={"split": 0.5},
        description="Stream splitter — divides a stream by ratio",
    ),
    UnitType.HEAT_EXCHANGER.value: UnitRegistryEntry(
        unit_type=UnitType.HEAT_EXCHANGER.value,
        biosteam_class="biosteam.units.HXutility",
        default_params={"T": 350},
        description="Heat exchanger with utility heating/cooling",
    ),
    UnitType.PUMP.value: UnitRegistryEntry(
        unit_type=UnitType.PUMP.value,
        biosteam_class="biosteam.units.Pump",
        default_params={"P": 101325},
        description="Liquid pump",
    ),
    UnitType.FLASH.value: UnitRegistryEntry(
        unit_type=UnitType.FLASH.value,
        biosteam_class="biosteam.units.Flash",
        default_params={"T": 373.15, "P": 101325},
        description="Vapor-liquid flash separator",
    ),
    UnitType.DISTILLATION.value: UnitRegistryEntry(
        unit_type=UnitType.DISTILLATION.value,
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
    UnitType.REACTOR.value: UnitRegistryEntry(
        unit_type=UnitType.REACTOR.value,
        biosteam_class="biosteam.units.StirredTankReactor",
        default_params={"tau": 1.0, "T": 323.15},
        description="Continuous stirred-tank reactor",
        subtypes={
            "neutralization": {"tau": 0.5, "T": 323.15},
        },
    ),
    UnitType.FERMENTOR.value: UnitRegistryEntry(
        unit_type=UnitType.FERMENTOR.value,
        biosteam_class="biosteam.units.StirredTankReactor",
        default_params={"tau": 36.0, "T": 305.15},
        description="Fermentation vessel",
        subtypes={
            "co_fermentation": {"tau": 36.0, "T": 305.15},
            "anaerobic": {"tau": 48.0, "T": 310.15},
        },
    ),
    UnitType.ENZYMATIC_HYDROLYSIS.value: UnitRegistryEntry(
        unit_type=UnitType.ENZYMATIC_HYDROLYSIS.value,
        biosteam_class="biosteam.units.StirredTankReactor",
        default_params={"tau": 84.0, "T": 321.15},
        description="Enzymatic hydrolysis (saccharification) reactor",
    ),
    UnitType.PRETREATMENT.value: UnitRegistryEntry(
        unit_type=UnitType.PRETREATMENT.value,
        biosteam_class="biosteam.units.StirredTankReactor",
        default_params={"tau": 0.083, "T": 431.15, "P": 550000},
        description="Biomass pretreatment reactor",
        subtypes={
            "dilute_acid": {"tau": 0.083, "T": 431.15, "P": 550000},
            "steam_explosion": {"tau": 0.167, "T": 473.15, "P": 1500000},
            "alkaline": {"tau": 1.0, "T": 393.15},
        },
    ),
    UnitType.MOLECULAR_SIEVE.value: UnitRegistryEntry(
        unit_type=UnitType.MOLECULAR_SIEVE.value,
        biosteam_class="biosteam.units.MolecularSieve",
        default_params={},
        description="Molecular sieve for dehydration (e.g., ethanol to 99.5%)",
    ),
    UnitType.EVAPORATOR.value: UnitRegistryEntry(
        unit_type=UnitType.EVAPORATOR.value,
        biosteam_class="biosteam.units.MultiEffectEvaporator",
        default_params={"n_effects": 3},
        description="Multi-effect evaporator for concentration",
    ),
    UnitType.FILTER.value: UnitRegistryEntry(
        unit_type=UnitType.FILTER.value,
        biosteam_class="biosteam.units.SolidsCentrifuge",
        default_params={},
        description="Solid-liquid separation filter",
    ),
    UnitType.CENTRIFUGE.value: UnitRegistryEntry(
        unit_type=UnitType.CENTRIFUGE.value,
        biosteam_class="biosteam.units.SolidsCentrifuge",
        default_params={},
        description="Centrifuge for solid-liquid separation",
    ),
    UnitType.DRYER.value: UnitRegistryEntry(
        unit_type=UnitType.DRYER.value,
        biosteam_class="biosteam.units.DrumDryer",
        default_params={},
        description="Dryer for moisture removal",
    ),
    UnitType.STORAGE_TANK.value: UnitRegistryEntry(
        unit_type=UnitType.STORAGE_TANK.value,
        biosteam_class="biosteam.units.StorageTank",
        default_params={"tau": 24.0},
        description="Storage tank",
    ),
    UnitType.BOILER.value: UnitRegistryEntry(
        unit_type=UnitType.BOILER.value,
        biosteam_class="biosteam.units.BoilerTurbogenerator",
        default_params={},
        description="Boiler / combined heat and power system",
    ),
    UnitType.TURBINE.value: UnitRegistryEntry(
        unit_type=UnitType.TURBINE.value,
        biosteam_class="biosteam.units.Turbine",
        default_params={},
        description="Steam or gas turbine for power generation",
    ),
    UnitType.WASTEWATER_TREATMENT.value: UnitRegistryEntry(
        unit_type=UnitType.WASTEWATER_TREATMENT.value,
        biosteam_class="biosteam.units.AnaerobicDigestion",
        default_params={},
        description="Wastewater treatment system",
        subtypes={
            "anaerobic_aerobic": {},
            "aerobic": {},
        },
    ),
    UnitType.SIZE_REDUCTION.value: UnitRegistryEntry(
        unit_type=UnitType.SIZE_REDUCTION.value,
        biosteam_class="biosteam.units.HammerMill",
        default_params={},
        description="Size reduction equipment (mill, grinder)",
    ),
    UnitType.COMPRESSOR.value: UnitRegistryEntry(
        unit_type=UnitType.COMPRESSOR.value,
        biosteam_class="biosteam.units.IsentropicCompressor",
        default_params={"P": 1000000},
        description="Gas compressor",
    ),
}


def get_registry_entry(unit_type: str) -> UnitRegistryEntry | None:
    """Look up a registry entry by unit type string."""
    return UNIT_REGISTRY.get(unit_type)


def get_default_params(unit_type: str, subtype: str | None = None) -> dict[str, Any]:
    """Get default parameters for a unit type, optionally with subtype overrides."""
    entry = UNIT_REGISTRY.get(unit_type)
    if entry is None:
        return {}
    params = dict(entry.default_params)
    if subtype and subtype in entry.subtypes:
        params.update(entry.subtypes[subtype])
    return params


def list_supported_types() -> list[str]:
    """List all unit types with registry entries."""
    return list(UNIT_REGISTRY.keys())

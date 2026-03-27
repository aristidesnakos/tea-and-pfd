"""Process Topology Engine — validates, enriches, and resolves ProcessSpec.

Responsibilities:
1. Validate the ProcessSpec graph structure (connectivity, valid types)
2. Enrich with default parameters from the unit registry
3. Track which parameters were auto-filled vs user-specified
"""

from __future__ import annotations

from collections import deque
from copy import deepcopy
from dataclasses import dataclass, field

from processflow.schema.process_spec import ProcessSpec, UnitOperation, UnitType
from processflow.topology.registry import UNIT_REGISTRY, get_default_params


@dataclass
class ValidationResult:
    """Result of ProcessSpec validation."""

    valid: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def add_error(self, msg: str) -> None:
        self.errors.append(msg)
        self.valid = False

    def add_warning(self, msg: str) -> None:
        self.warnings.append(msg)


class TopologyEngine:
    """Validates, enriches, and resolves ProcessSpec instances."""

    def validate(self, spec: ProcessSpec) -> ValidationResult:
        """Validate the ProcessSpec for structural correctness.

        Checks:
        - All unit IDs are unique
        - All stream references are valid
        - The process graph is connected (no orphan units)
        - All unit types are in the registry
        - At least one feed and one product stream exists
        """
        result = ValidationResult()

        # Check unique unit IDs
        ids = [u.id for u in spec.units]
        if len(ids) != len(set(ids)):
            dupes = [uid for uid in ids if ids.count(uid) > 1]
            result.add_error(f"Duplicate unit IDs: {set(dupes)}")

        # Check unit types are supported
        for unit in spec.units:
            if unit.type not in UNIT_REGISTRY:
                result.add_warning(
                    f"Unit {unit.id} type '{unit.type.value}' not in registry — "
                    "no default parameters available"
                )

        # Check stream connectivity
        unit_ids = set(ids)
        special = {"feed", "product", "waste", "utility"}
        valid_ids = unit_ids | special

        referenced_units = set()
        has_feed = False
        has_product = False

        for stream in spec.streams:
            if stream.from_id not in valid_ids:
                result.add_error(f"Stream references unknown source: '{stream.from_id}'")
            if stream.to_id not in valid_ids:
                result.add_error(f"Stream references unknown destination: '{stream.to_id}'")

            if stream.from_id in unit_ids:
                referenced_units.add(stream.from_id)
            if stream.to_id in unit_ids:
                referenced_units.add(stream.to_id)

            if stream.from_id == "feed":
                has_feed = True
            if stream.to_id == "product":
                has_product = True

        # Check for orphan units
        orphans = unit_ids - referenced_units
        if orphans:
            result.add_warning(f"Orphan units (not connected by any stream): {orphans}")

        if not has_feed:
            result.add_error("No feed stream found (stream with from_id='feed')")

        if not has_product:
            result.add_warning("No product stream found (stream with to_id='product')")

        # Check graph connectivity via BFS from feed
        graph = spec.get_connected_graph()
        visited = set()
        queue = deque(["feed"])
        while queue:
            node = queue.popleft()
            if node in visited:
                continue
            visited.add(node)
            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    queue.append(neighbor)

        unreachable = unit_ids - visited
        if unreachable:
            result.add_warning(
                f"Units not reachable from feed: {unreachable}. "
                "They may need additional input streams."
            )

        return result

    def enrich(self, spec: ProcessSpec) -> ProcessSpec:
        """Enrich ProcessSpec with default parameters from the registry.

        Returns a new ProcessSpec with:
        - Missing unit parameters filled from registry defaults
        - Auto-filled parameter paths tracked in metadata
        """
        spec = deepcopy(spec)
        auto_filled: list[str] = list(spec.metadata.auto_filled_params)

        for unit in spec.units:
            defaults = get_default_params(unit.type, unit.subtype)
            for key, value in defaults.items():
                if key not in unit.params:
                    unit.params[key] = value
                    auto_filled.append(f"units.{unit.id}.params.{key}")

            # Auto-assign section if missing
            if unit.section is None:
                unit.section = _infer_section(unit.type)
                auto_filled.append(f"units.{unit.id}.section")

            # Auto-assign name if missing
            if unit.name is None:
                entry = UNIT_REGISTRY.get(unit.type)
                if entry:
                    unit.name = entry.description.split(" — ")[0] if " — " in entry.description else entry.description
                    auto_filled.append(f"units.{unit.id}.name")

        spec.metadata.auto_filled_params = auto_filled
        return spec


def _infer_section(unit_type: UnitType) -> str:
    """Infer the process section from unit type."""
    section_map: dict[UnitType, str] = {
        UnitType.SIZE_REDUCTION: "feedstock_handling",
        UnitType.CONVEYOR: "feedstock_handling",
        UnitType.SCREW_FEEDER: "feedstock_handling",
        UnitType.PRETREATMENT: "pretreatment",
        UnitType.REACTOR: "reaction",
        UnitType.FERMENTOR: "fermentation",
        UnitType.ENZYMATIC_HYDROLYSIS: "saccharification",
        UnitType.DISTILLATION: "separation",
        UnitType.FLASH: "separation",
        UnitType.MOLECULAR_SIEVE: "purification",
        UnitType.EVAPORATOR: "separation",
        UnitType.FILTER: "separation",
        UnitType.CENTRIFUGE: "separation",
        UnitType.ADSORPTION: "purification",
        UnitType.CRYSTALLIZER: "purification",
        UnitType.DRYER: "separation",
        UnitType.MIXER: "other",
        UnitType.SPLITTER: "other",
        UnitType.HEAT_EXCHANGER: "heat_transfer",
        UnitType.PUMP: "other",
        UnitType.STORAGE_TANK: "storage",
        UnitType.BOILER: "utilities",
        UnitType.TURBINE: "utilities",
        UnitType.COOLING_TOWER: "utilities",
        UnitType.WASTEWATER_TREATMENT: "wastewater",
        UnitType.COMPRESSOR: "other",
    }
    return section_map.get(unit_type, "other")

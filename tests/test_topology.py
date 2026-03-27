"""Tests for the Process Topology Engine."""

import pytest

from processflow.schema.process_spec import (
    Feedstock,
    ProcessSpec,
    Stream,
    UnitOperation,
    UnitType,
)
from processflow.topology.engine import TopologyEngine
from processflow.topology.registry import (
    get_default_params,
    get_registry_entry,
    list_supported_types,
)


class TestTopologyEngine:
    @pytest.fixture
    def engine(self):
        return TopologyEngine()

    def test_valid_spec_passes(self, engine, corn_stover_spec):
        """Valid corn stover spec passes validation."""
        result = engine.validate(corn_stover_spec)
        assert result.valid
        assert len(result.errors) == 0

    def test_duplicate_unit_ids(self, engine):
        """Duplicate unit IDs are caught."""
        spec = ProcessSpec(
            process_name="Bad",
            feedstock=Feedstock(name="x", flow_rate_kg_hr=100),
            units=[
                UnitOperation(id="U-101", type=UnitType.MIXER),
                UnitOperation(id="U-101", type=UnitType.PUMP),
            ],
            streams=[Stream(from_id="feed", to_id="U-101")],
        )
        result = engine.validate(spec)
        assert not result.valid
        assert any("Duplicate" in e for e in result.errors)

    def test_missing_feed_stream(self, engine):
        """Missing feed stream is caught."""
        spec = ProcessSpec(
            process_name="Bad",
            feedstock=Feedstock(name="x", flow_rate_kg_hr=100),
            units=[UnitOperation(id="U-101", type=UnitType.MIXER)],
            streams=[Stream(from_id="U-101", to_id="product")],
        )
        result = engine.validate(spec)
        assert not result.valid
        assert any("feed" in e.lower() for e in result.errors)

    def test_orphan_units_warned(self, engine):
        """Orphan units (not connected) generate warnings."""
        spec = ProcessSpec(
            process_name="Orphan",
            feedstock=Feedstock(name="x", flow_rate_kg_hr=100),
            units=[
                UnitOperation(id="U-101", type=UnitType.MIXER),
                UnitOperation(id="U-201", type=UnitType.PUMP),
            ],
            streams=[Stream(from_id="feed", to_id="U-101")],
        )
        result = engine.validate(spec)
        assert any("Orphan" in w or "orphan" in w.lower() for w in result.warnings)

    def test_enrich_fills_defaults(self, engine, corn_stover_spec):
        """Enrichment fills in missing parameters from registry."""
        enriched = engine.enrich(corn_stover_spec)
        assert len(enriched.metadata.auto_filled_params) > 0

    def test_enrich_preserves_user_params(self, engine, corn_stover_spec):
        """Enrichment does not overwrite user-specified parameters."""
        original_temp = corn_stover_spec.units[1].params.get("temperature_C")
        enriched = engine.enrich(corn_stover_spec)
        enriched_temp = enriched.units[1].params.get("temperature_C")
        assert original_temp == enriched_temp


class TestRegistry:
    def test_all_common_types_registered(self):
        """Common unit types have registry entries."""
        for ut in [UnitType.MIXER, UnitType.REACTOR, UnitType.DISTILLATION,
                   UnitType.PUMP, UnitType.HEAT_EXCHANGER]:
            assert get_registry_entry(ut) is not None

    def test_default_params_with_subtype(self):
        """Subtype overrides are applied to default params."""
        params = get_default_params(UnitType.PRETREATMENT, "dilute_acid")
        assert "tau" in params
        assert "T" in params

    def test_list_supported_types(self):
        """At least 15 unit types are registered."""
        types = list_supported_types()
        assert len(types) >= 15

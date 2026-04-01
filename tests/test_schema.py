"""Tests for ProcessSpec schema validation and serialization."""

import json

import pytest
from pydantic import ValidationError

from processflow.schema.process_spec import (
    ChemicalRole,
    ChemicalSpec,
    EconomicParams,
    Feedstock,
    ProcessSpec,
    Product,
    Stream,
    UnitOperation,
    UnitType,
)


class TestProcessSpec:
    def test_minimal_spec(self):
        """A minimal valid ProcessSpec with one unit and one stream."""
        spec = ProcessSpec(
            process_name="Test Process",
            feedstock=Feedstock(name="water", flow_rate_kg_hr=1000),
            units=[UnitOperation(id="U-101", type=UnitType.MIXER)],
            streams=[Stream(from_id="feed", to_id="U-101")],
        )
        assert spec.process_name == "Test Process"
        assert len(spec.units) == 1

    def test_json_roundtrip(self, corn_stover_spec: ProcessSpec):
        """ProcessSpec survives JSON serialization and deserialization."""
        json_str = corn_stover_spec.to_json()
        restored = ProcessSpec.from_json(json_str)
        assert restored.process_name == corn_stover_spec.process_name
        assert len(restored.units) == len(corn_stover_spec.units)
        assert len(restored.streams) == len(corn_stover_spec.streams)

    def test_json_file_roundtrip(self, corn_stover_spec: ProcessSpec, tmp_output):
        """ProcessSpec saves to and loads from a JSON file."""
        path = tmp_output / "spec.json"
        corn_stover_spec.to_json(path)
        restored = ProcessSpec.from_json(path)
        assert restored.process_name == corn_stover_spec.process_name

    def test_json_schema_export(self):
        """JSON Schema export produces valid schema."""
        schema = ProcessSpec.json_schema()
        assert schema["type"] == "object"
        assert "properties" in schema
        assert "process_name" in schema["properties"]

    def test_boundary_node_stream_accepted(self):
        """Stream to a non-unit-ID boundary node is accepted (relaxed validation)."""
        spec = ProcessSpec(
            process_name="CCS",
            feedstock=Feedstock(name="exhaust", flow_rate_kg_hr=100),
            units=[UnitOperation(id="U-101", type="amine_absorber")],
            streams=[
                Stream(from_id="FEED", to_id="U-101"),
                Stream(from_id="U-101", to_id="VENT"),
            ],
        )
        assert len(spec.streams) == 2

    def test_invalid_reaction_reference(self):
        """Reaction referencing a non-existent unit raises ValidationError."""
        from processflow.schema.process_spec import Reaction

        with pytest.raises(ValidationError, match="not found"):
            ProcessSpec(
                process_name="Bad",
                feedstock=Feedstock(name="x", flow_rate_kg_hr=100),
                units=[UnitOperation(id="U-101", type=UnitType.REACTOR)],
                streams=[Stream(from_id="feed", to_id="U-101")],
                reactions=[Reaction(unit_id="NONEXISTENT", reactants=["A"], products=["B"])],
            )

    def test_get_unit_by_id(self, corn_stover_spec: ProcessSpec):
        """Look up unit by ID."""
        unit = corn_stover_spec.get_unit_by_id("U-201")
        assert unit is not None
        assert unit.type == "Pretreatment"
        assert corn_stover_spec.get_unit_by_id("NONEXISTENT") is None

    def test_connected_graph(self, corn_stover_spec: ProcessSpec):
        """Connected graph adjacency list is built correctly."""
        graph = corn_stover_spec.get_connected_graph()
        assert "feed" in graph
        assert "U-101" in graph["feed"]

    def test_corn_stover_template_completeness(self, corn_stover_spec: ProcessSpec):
        """Corn stover template has expected structure."""
        assert len(corn_stover_spec.units) == 10
        assert len(corn_stover_spec.streams) == 12
        assert len(corn_stover_spec.reactions) == 4
        assert len(corn_stover_spec.chemicals) == 8
        assert corn_stover_spec.feedstock.flow_rate_kg_hr == pytest.approx(83333.33, rel=0.01)


class TestUnitType:
    def test_all_types_have_values(self):
        """All UnitType enum members have string values."""
        for ut in UnitType:
            assert isinstance(ut.value, str)
            assert len(ut.value) > 0


class TestFeedstock:
    def test_negative_flow_rate_rejected(self):
        """Negative flow rate is rejected."""
        with pytest.raises(ValidationError):
            Feedstock(name="x", flow_rate_kg_hr=-100)

    def test_zero_flow_rate_rejected(self):
        """Zero flow rate is rejected."""
        with pytest.raises(ValidationError):
            Feedstock(name="x", flow_rate_kg_hr=0)

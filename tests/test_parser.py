"""Tests for the NL parser (template loading, no API calls in unit tests)."""

import pytest

from processflow.parser.nl_parser import list_templates, load_template
from processflow.schema.process_spec import ProcessSpec


class TestTemplateLoading:
    def test_list_templates(self):
        """At least one template is available."""
        templates = list_templates()
        assert len(templates) >= 1
        assert "corn_stover_ethanol" in templates

    def test_load_corn_stover_template(self):
        """Corn stover template loads as valid ProcessSpec."""
        spec = load_template("corn_stover_ethanol")
        assert isinstance(spec, ProcessSpec)
        assert "corn stover" in spec.process_name.lower()

    def test_load_nonexistent_template(self):
        """Loading a nonexistent template raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError, match="not found"):
            load_template("nonexistent_process")


class TestNLParser:
    def test_missing_api_key_raises(self):
        """parse_nl_to_spec raises RuntimeError without API key."""
        import os
        # Temporarily unset the env var
        old = os.environ.pop("ANTHROPIC_API_KEY", None)
        try:
            from processflow.parser.nl_parser import parse_nl_to_spec
            with pytest.raises(RuntimeError, match="API key"):
                parse_nl_to_spec("test", api_key=None)
        finally:
            if old:
                os.environ["ANTHROPIC_API_KEY"] = old

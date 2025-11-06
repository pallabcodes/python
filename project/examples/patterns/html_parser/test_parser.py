"""
Unit tests for HTML parser functionality.

This module provides comprehensive tests for HTML parsing,
data extraction, and pipeline integration.
"""

import pytest
from unittest.mock import patch, MagicMock

from .extractor import (
    ExtractionRule, ExtractionMethod, ExtractionResult,
    HTMLExtractor, create_extraction_rules, extract_data
)
from .parser_stage import HTMLParserStage, ConfigurableHTMLParserStage


class TestExtractionRule:
    """Tests for extraction rule configuration."""

    def test_valid_rule_creation(self):
        """Test creating a valid extraction rule."""
        rule = ExtractionRule(
            name="test_rule",
            method=ExtractionMethod.CSS_SELECTOR,
            selector=".test-class"
        )

        assert rule.name == "test_rule"
        assert rule.method == ExtractionMethod.CSS_SELECTOR
        assert rule.selector == ".test-class"
        assert not rule.multiple
        assert not rule.required

    def test_rule_validation(self):
        """Test rule validation requirements."""
        # Missing name
        with pytest.raises(ValueError):
            ExtractionRule(
                name="",
                method=ExtractionMethod.CSS_SELECTOR,
                selector=".test"
            )

        # Attribute extraction without attribute name
        with pytest.raises(ValueError):
            ExtractionRule(
                name="test",
                method=ExtractionMethod.ATTRIBUTE,
                selector=".test"
                # Missing attribute
            )


class TestHTMLExtractor:
    """Tests for HTML data extraction."""

    def test_extractor_creation(self):
        """Test HTML extractor initialization."""
        rules = [
            ExtractionRule(
                name="title",
                method=ExtractionMethod.CSS_SELECTOR,
                selector="title"
            )
        ]

        extractor = HTMLExtractor(rules)
        assert len(extractor.rules) == 1
        assert extractor.rules[0].name == "title"

    @patch('bs4.BeautifulSoup')
    def test_css_selector_extraction(self, mock_bs):
        """Test CSS selector-based extraction."""
        # Mock BeautifulSoup
        mock_soup = MagicMock()
        mock_element = MagicMock()
        mock_element.get_text.return_value = "Test Title"
        mock_soup.select.return_value = [mock_element]

        mock_bs.return_value = mock_soup

        rules = [
            ExtractionRule(
                name="title",
                method=ExtractionMethod.CSS_SELECTOR,
                selector="title"
            )
        ]

        extractor = HTMLExtractor(rules)
        html = "<html><head><title>Test Title</title></head></html>"
        result = extractor.extract(html)

        assert result["title"] == "Test Title"
        assert result["_extraction_success"] is True

    def test_regex_extraction(self):
        """Test regex-based data extraction."""
        rules = [
            ExtractionRule(
                name="email",
                method=ExtractionMethod.REGEX,
                selector=r'[\w\.-]+@[\w\.-]+\.\w+'
            )
        ]

        extractor = HTMLExtractor(rules)
        html = '<p>Contact: user@example.com for more info</p>'
        result = extractor.extract(html)

        assert result["email"] == "user@example.com"
        assert result["_extraction_success"] is True

    def test_multiple_extraction(self):
        """Test extracting multiple values."""
        rules = [
            ExtractionRule(
                name="items",
                method=ExtractionMethod.REGEX,
                selector=r'Item \d+',
                multiple=True
            )
        ]

        extractor = HTMLExtractor(rules)
        html = '<ul><li>Item 1</li><li>Item 2</li><li>Item 3</li></ul>'
        result = extractor.extract(html)

        assert result["items"] == ["Item 1", "Item 2", "Item 3"]
        assert result["_extraction_success"] is True

    def test_extraction_with_transform(self):
        """Test extraction with data transformation."""
        def uppercase_transform(value):
            return str(value).upper()

        rules = [
            ExtractionRule(
                name="title",
                method=ExtractionMethod.REGEX,
                selector=r'<title>(.*?)</title>',
                transform=uppercase_transform
            )
        ]

        extractor = HTMLExtractor(rules)
        html = '<html><head><title>test page</title></head></html>'
        result = extractor.extract(html)

        assert result["title"] == "TEST PAGE"

    def test_required_field_missing(self):
        """Test required field validation."""
        rules = [
            ExtractionRule(
                name="missing",
                method=ExtractionMethod.CSS_SELECTOR,
                selector=".nonexistent",
                required=True
            )
        ]

        extractor = HTMLExtractor(rules)
        html = "<html><body></body></html>"
        result = extractor.extract(html)

        assert result["_extraction_success"] is False
        assert len(result["_extraction_errors"]) > 0
        assert "Required field" in result["_extraction_errors"][0]

    def test_default_values(self):
        """Test default value handling."""
        rules = [
            ExtractionRule(
                name="missing",
                method=ExtractionMethod.CSS_SELECTOR,
                selector=".nonexistent",
                default_value="Not found"
            )
        ]

        extractor = HTMLExtractor(rules)
        html = "<html><body></body></html>"
        result = extractor.extract(html)

        assert result["missing"] == "Not found"
        assert result["_extraction_success"] is True


class TestHTMLParserStage:
    """Tests for HTML parser pipeline stage."""

    def test_parser_stage_creation(self):
        """Test parser stage initialization."""
        rules = [
            ExtractionRule(
                name="title",
                method=ExtractionMethod.CSS_SELECTOR,
                selector="title"
            )
        ]

        stage = HTMLParserStage(
            name="TestParser",
            extraction_rules=rules,
            input_field="html",
            output_field="parsed"
        )

        assert stage.name == "TestParser"
        assert stage.input_field == "html"
        assert stage.output_field == "parsed"
        assert len(stage.extraction_rules) == 1

    def test_html_content_extraction(self):
        """Test extracting HTML content from input data."""
        stage = HTMLParserStage(
            name="TestParser",
            extraction_rules=[],
            input_field="content"
        )

        # Test string input
        assert stage._get_html_content("test html") == "test html"

        # Test dict input with configured field
        data = {"content": "<html>test</html>", "other": "data"}
        assert stage._get_html_content(data) == "<html>test</html>"

        # Test dict input with fallback fields
        data = {"html": "<html>test</html>"}
        assert stage._get_html_content(data) == "<html>test</html>"

        # Test bytes input
        data = {"content": b"<html>test</html>"}
        assert stage._get_html_content(data) == "<html>test</html>"

    def test_error_result_creation(self):
        """Test error result creation."""
        stage = HTMLParserStage(name="TestParser", extraction_rules=[])

        original_data = {"test": "data"}
        error_result = stage._create_error_result(original_data, "Test error")

        assert error_result["test"] == "data"
        assert error_result[stage.output_field]["_extraction_success"] is False
        assert "Test error" in error_result[stage.output_field]["_extraction_errors"]

    def test_parser_statistics(self):
        """Test parser statistics reporting."""
        rules = [ExtractionRule(name="test", method=ExtractionMethod.TEXT, selector="")]
        stage = HTMLParserStage(name="TestParser", extraction_rules=rules)

        stats = stage.get_stats()
        assert stats["stage_name"] == "TestParser"
        assert stats["documents_processed"] == 0
        assert stats["num_rules"] == 1


class TestConfigurableHTMLParserStage:
    """Tests for configurable HTML parser stage."""

    def test_configurable_stage_creation(self):
        """Test configurable parser stage initialization."""
        stage = ConfigurableHTMLParserStage(
            name="ConfigParser",
            rules_field="custom_rules"
        )

        assert stage.name == "ConfigParser"
        assert stage.rules_field == "custom_rules"
        assert len(stage.default_rules) == 0

    def test_runtime_rule_creation(self):
        """Test creating rules from runtime configuration."""
        stage = ConfigurableHTMLParserStage(name="TestParser")

        config_data = {
            "html": "<html><title>Test</title></html>",
            "extraction_rules": [
                {
                    "name": "title",
                    "method": "css_selector",
                    "selector": "title"
                }
            ]
        }

        rules = stage._get_extraction_rules(config_data)
        assert len(rules) == 1
        assert rules[0].name == "title"
        assert rules[0].method == ExtractionMethod.CSS_SELECTOR

    def test_fallback_to_default_rules(self):
        """Test falling back to default rules when none provided."""
        default_rules = [
            ExtractionRule(
                name="default_title",
                method=ExtractionMethod.CSS_SELECTOR,
                selector="title"
            )
        ]

        stage = ConfigurableHTMLParserStage(
            name="TestParser",
            default_rules=default_rules
        )

        # No rules in input data
        config_data = {"html": "<html><title>Test</title></html>"}
        rules = stage._get_extraction_rules(config_data)

        assert len(rules) == 1
        assert rules[0].name == "default_title"


class TestIntegration:
    """Integration tests combining multiple components."""

    def test_full_pipeline_integration(self):
        """Test full pipeline with HTML parsing."""
        from ..pipeline_core.runner import PipelineRunner

        rules = [
            ExtractionRule(
                name="title",
                method=ExtractionMethod.REGEX,
                selector=r'<title>(.*?)</title>'
            )
        ]

        stage = HTMLParserStage(
            name="IntegrationParser",
            extraction_rules=rules,
            input_field="content"
        )

        pipeline = PipelineRunner([stage])

        input_data = {"content": "<html><head><title>Test Page</title></head></html>"}
        results = pipeline.run_pipeline([input_data])

        assert results["success"] is True
        assert len(results) == 1
        assert results[0][stage.output_field]["title"] == "Test Page"


def create_test_rules() -> List[ExtractionRule]:
    """Create test extraction rules."""
    return [
        ExtractionRule(
            name="title",
            method=ExtractionMethod.CSS_SELECTOR,
            selector="title"
        ),
        ExtractionRule(
            name="items",
            method=ExtractionMethod.CSS_SELECTOR,
            selector=".item",
            multiple=True
        )
    ]


if __name__ == "__main__":
    """Run tests when executed directly."""
    pytest.main([__file__, "-v"])


"""
Demonstrations of HTML Parser functionality.

This module provides practical examples of using HTML parsing
stages to extract structured data from web content.
"""

import logging
from typing import Any, List

from ..pipeline_core.message import create_data_message
from ..pipeline_core.runner import PipelineRunner
from .extractor import ExtractionRule, ExtractionMethod, create_extraction_rules
from .parser_stage import HTMLParserStage, ConfigurableHTMLParserStage


def demo_basic_html_parsing() -> None:
    """Demonstrate basic HTML parsing with predefined rules."""
    print("=== Basic HTML Parsing Demo ===")

    # Sample HTML content
    html_content = """
    <html>
    <head><title>Test Page</title></head>
    <body>
        <h1>Welcome to Test Page</h1>
        <div class="content">
            <p>This is a test paragraph.</p>
            <ul class="items">
                <li class="item" data-id="1">Item 1</li>
                <li class="item" data-id="2">Item 2</li>
                <li class="item" data-id="3">Item 3</li>
            </ul>
        </div>
        <div class="metadata">
            <span class="author">John Doe</span>
            <span class="date">2024-01-15</span>
        </div>
    </body>
    </html>
    """

    # Define extraction rules
    rules = [
        ExtractionRule(
            name="title",
            method=ExtractionMethod.CSS_SELECTOR,
            selector="title",
            required=True
        ),
        ExtractionRule(
            name="heading",
            method=ExtractionMethod.CSS_SELECTOR,
            selector="h1"
        ),
        ExtractionRule(
            name="items",
            method=ExtractionMethod.CSS_SELECTOR,
            selector=".item",
            multiple=True
        ),
        ExtractionRule(
            name="item_ids",
            method=ExtractionMethod.ATTRIBUTE,
            selector=".item",
            attribute="data-id",
            multiple=True
        ),
        ExtractionRule(
            name="author",
            method=ExtractionMethod.CSS_SELECTOR,
            selector=".author"
        ),
        ExtractionRule(
            name="date",
            method=ExtractionMethod.CSS_SELECTOR,
            selector=".date"
        )
    ]

    # Create parser stage
    parser = HTMLParserStage(
        name="BasicParser",
        extraction_rules=rules,
        input_field="html_content",
        output_field="parsed_data"
    )

    # Create pipeline
    pipeline = PipelineRunner([parser])

    # Input data
    input_data = {"html_content": html_content, "source_url": "https://example.com/test"}
    input_messages = [create_data_message(input_data)]

    print("HTML content to parse:")
    print(html_content[:200] + "..." if len(html_content) > 200 else html_content)
    print(f"\nExtraction rules: {len(rules)}")
    print("Pipeline: HTML Parser")
    print()

    try:
        results = pipeline.run_pipeline(input_messages, timeout=10.0)

        print(f"Pipeline completed in {results['execution_time']:.2f}s")
        print(f"Success: {results['success']}")

        if results['success']:
            # Show extracted data
            parsed_data = results[0][parser.output_field]
            print("
Extracted data:")
            for key, value in parsed_data.items():
                if not key.startswith('_'):
                    print(f"  {key}: {value}")

            errors = parsed_data.get('_extraction_errors', [])
            if errors:
                print(f"\nExtraction errors: {len(errors)}")
                for error in errors[:3]:  # Show first 3 errors
                    print(f"  - {error}")

    except Exception as e:
        print(f"Demo failed: {e}")


def demo_configurable_parsing() -> None:
    """Demonstrate runtime-configurable HTML parsing."""
    print("\n=== Configurable HTML Parsing Demo ===")

    # Create configurable parser
    parser = ConfigurableHTMLParserStage(
        name="ConfigurableParser",
        input_field="html",
        output_field="extracted",
        rules_field="rules"
    )

    pipeline = PipelineRunner([parser])

    # Input with HTML and custom extraction rules
    input_data = {
        "html": """
        <div class="product">
            <h2 class="name">Widget Pro</h2>
            <span class="price">$29.99</span>
            <div class="specs">
                <span class="category">Electronics</span>
                <span class="stock">In Stock</span>
            </div>
        </div>
        """,
        "rules": [
            {
                "name": "product_name",
                "method": "css_selector",
                "selector": ".name"
            },
            {
                "name": "price",
                "method": "css_selector",
                "selector": ".price"
            },
            {
                "name": "category",
                "method": "css_selector",
                "selector": ".category"
            },
            {
                "name": "availability",
                "method": "css_selector",
                "selector": ".stock"
            }
        ],
        "product_id": "widget-001"
    }

    input_messages = [create_data_message(input_data)]

    print("Configurable parsing with runtime rules:")
    print("HTML content + extraction rules provided at runtime")
    print()

    try:
        results = pipeline.run_pipeline(input_messages, timeout=10.0)

        print(f"Pipeline completed in {results['execution_time']:.2f}s")
        print(f"Success: {results['success']}")

        if results['success']:
            extracted = results[0][parser.output_field]
            print("
Extracted product data:")
            for key, value in extracted.items():
                if not key.startswith('_'):
                    print(f"  {key}: {value}")

    except Exception as e:
        print(f"Demo failed: {e}")


def demo_regex_extraction() -> None:
    """Demonstrate regex-based data extraction."""
    print("\n=== Regex Extraction Demo ===")

    # HTML with structured text patterns
    html_content = """
    <html>
    <body>
        <p>Contact: email@company.com</p>
        <p>Phone: (555) 123-4567</p>
        <p>Website: https://www.company.com</p>
        <p>Address: 123 Main St, City, ST 12345</p>
    </body>
    </html>
    """

    # Regex-based extraction rules
    rules = [
        ExtractionRule(
            name="email",
            method=ExtractionMethod.REGEX,
            selector=r'[\w\.-]+@[\w\.-]+\.\w+'
        ),
        ExtractionRule(
            name="phone",
            method=ExtractionMethod.REGEX,
            selector=r'\(\d{3}\) \d{3}-\d{4}'
        ),
        ExtractionRule(
            name="website",
            method=ExtractionMethod.REGEX,
            selector=r'https?://[^\s<>"\'{}|\\^`[\]]+'
        ),
        ExtractionRule(
            name="zip_code",
            method=ExtractionMethod.REGEX,
            selector=r'\b\d{5}\b'
        )
    ]

    parser = HTMLParserStage(
        name="RegexParser",
        extraction_rules=rules,
        input_field="content"
    )

    pipeline = PipelineRunner([parser])

    input_data = {"content": html_content, "source": "contact_page"}
    input_messages = [create_data_message(input_data)]

    print("Regex-based extraction from HTML text:")
    print("Extracting email, phone, website, zip code using regex patterns")
    print()

    try:
        results = pipeline.run_pipeline(input_messages, timeout=10.0)

        print(f"Pipeline completed in {results['execution_time']:.2f}s")
        print(f"Success: {results['success']}")

        if results['success']:
            extracted = results[0][parser.output_field]
            print("
Extracted contact information:")
            for key, value in extracted.items():
                if not key.startswith('_'):
                    print(f"  {key}: {value}")

    except Exception as e:
        print(f"Demo failed: {e}")


def demo_error_handling() -> None:
    """Demonstrate error handling in HTML parsing."""
    print("\n=== Error Handling Demo ===")

    # Rules with some invalid selectors
    rules = [
        ExtractionRule(
            name="title",
            method=ExtractionMethod.CSS_SELECTOR,
            selector="title",
            required=True
        ),
        ExtractionRule(
            name="missing_element",
            method=ExtractionMethod.CSS_SELECTOR,
            selector=".nonexistent",
            required=True,
            default_value="Not found"
        ),
        ExtractionRule(
            name="invalid_selector",
            method=ExtractionMethod.CSS_SELECTOR,
            selector="invalid[selector",
            default_value="Parse error"
        )
    ]

    parser = HTMLParserStage(
        name="ErrorHandlingParser",
        extraction_rules=rules
    )

    pipeline = PipelineRunner([parser])

    # Malformed HTML
    malformed_html = """
    <html>
    <head><title>Test Page</title>
    <body>
    <h1>Unclosed heading
    <p>Some content
    <div class="broken">Broken <span>nested
    </body>
    """

    input_data = {"data": malformed_html}
    input_messages = [create_data_message(input_data)]

    print("Error handling with malformed HTML and missing elements:")
    print("Some rules are required, some have invalid selectors")
    print()

    try:
        results = pipeline.run_pipeline(input_messages, timeout=10.0)

        print(f"Pipeline completed in {results['execution_time']:.2f}s")
        print(f"Success: {results['success']}")

        if results['success']:
            extracted = results[0][parser.output_field]
            print("
Extraction results:")
            for key, value in extracted.items():
                if not key.startswith('_'):
                    print(f"  {key}: {value}")

            errors = extracted.get('_extraction_errors', [])
            if errors:
                print(f"\nExtraction errors ({len(errors)}):")
                for error in errors:
                    print(f"  - {error}")

    except Exception as e:
        print(f"Demo failed: {e}")


def run_all_parser_demos() -> None:
    """Run all HTML parser demonstrations."""
    # Configure logging for demos
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("Running HTML Parser Demonstrations")
    print("=" * 45)

    try:
        demo_basic_html_parsing()
        demo_configurable_parsing()
        demo_regex_extraction()
        demo_error_handling()

        print("\n" + "=" * 45)
        print("All HTML parser demonstrations completed successfully!")

    except Exception as e:
        print(f"\nDemo failed with error: {e}")
        raise


if __name__ == "__main__":
    """Run demonstrations when executed directly."""
    run_all_parser_demos()


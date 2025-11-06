"""
Basic HTML parser demonstrations.

This module contains fundamental demonstrations of HTML parsing
with predefined rules and basic functionality.
"""

import logging
from typing import Any, List

from ..pipeline_core.message import create_data_message
from ..pipeline_core.runner import PipelineRunner
from .extractor import ExtractionRule, ExtractionMethod
from .parser_stage import HTMLParserStage


class ResponseProcessor:
    """Process HTML parser responses."""

    def __init__(self, name: str = "ResponseProcessor"):
        self.name = name
        self._processed = 0

    def transform(self, data: Any) -> Any:
        """Process HTML parser response data."""
        self._processed += 1

        if isinstance(data, dict) and data.get("error"):
            # Handle error responses
            return {
                "processed": False,
                "error": data["error_message"],
                "original": data.get("original_request")
            }

        # Process successful responses
        if isinstance(data, dict) and "status_code" in data:
            return {
                "processed": True,
                "url": data.get("url"),
                "status": data.get("status_code"),
                "content_type": data.get("content_type"),
                "data_length": len(str(data.get("data", ""))),
                "elapsed": data.get("elapsed", 0)
            }

        return data


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


def run_basic_demos() -> None:
    """Run all basic HTML parser demonstrations."""
    # Configure logging for demos
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("Running Basic HTML Parser Demonstrations")
    print("=" * 40)

    try:
        demo_basic_html_parsing()
        demo_regex_extraction()

        print("\n" + "=" * 40)
        print("Basic demonstrations completed successfully!")

    except Exception as e:
        print(f"\nDemo failed with error: {e}")
        raise


if __name__ == "__main__":
    """Run basic demonstrations when executed directly."""
    run_basic_demos()


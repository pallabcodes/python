"""
HTML extraction method implementations.

This module contains the specific implementations for different
HTML extraction methods used by the HTMLExtractor class.
"""

import re
from typing import Any, Optional

from .extractor_core import ExtractionResult, ExtractionRule, ExtractionMethod


def _apply_rule(self: 'HTMLExtractor', soup: Any, html_content: str, rule: ExtractionRule) -> ExtractionResult:
    """Apply a single extraction rule."""
    try:
        if rule.method == ExtractionMethod.CSS_SELECTOR:
            return self._extract_css_selector(soup, rule)
        elif rule.method == ExtractionMethod.XPATH:
            return self._extract_xpath(soup, html_content, rule)
        elif rule.method == ExtractionMethod.REGEX:
            return self._extract_regex(html_content, rule)
        elif rule.method == ExtractionMethod.ATTRIBUTE:
            return self._extract_attribute(soup, rule)
        elif rule.method == ExtractionMethod.TEXT:
            return self._extract_text(soup, rule)
        elif rule.method == ExtractionMethod.HTML:
            return self._extract_html(soup, rule)
        else:
            return ExtractionResult(
                rule_name=rule.name,
                value=rule.default_value,
                success=False,
                error=f"Unsupported extraction method: {rule.method}"
            )

    except Exception as e:
        return ExtractionResult(
            rule_name=rule.name,
            value=rule.default_value,
            success=False,
            error=str(e)
        )


def _extract_css_selector(self: 'HTMLExtractor', soup: Any, rule: ExtractionRule) -> ExtractionResult:
    """Extract data using CSS selector."""
    if soup is str:
        return ExtractionResult(
            rule_name=rule.name,
            value=rule.default_value,
            success=False,
            error="CSS selectors require BeautifulSoup"
        )

    try:
        elements = soup.select(rule.selector)

        if not elements:
            return ExtractionResult(
                rule_name=rule.name,
                value=rule.default_value if rule.multiple else None,
                success=True
            )

        if rule.multiple:
            values = []
            for element in elements:
                value = self._get_element_value(element, rule.attribute)
                if rule.transform:
                    value = rule.transform(value)
                values.append(value)
            return ExtractionResult(rule_name=rule.name, value=values, success=True)
        else:
            element = elements[0]
            value = self._get_element_value(element, rule.attribute)
            if rule.transform:
                value = rule.transform(value)
            return ExtractionResult(rule_name=rule.name, value=value, success=True)

    except Exception as e:
        return ExtractionResult(
            rule_name=rule.name,
            value=rule.default_value,
            success=False,
            error=f"CSS selector error: {e}"
        )


def _extract_xpath(self: 'HTMLExtractor', soup: Any, html_content: str, rule: ExtractionRule) -> ExtractionResult:
    """Extract data using XPath expression."""
    try:
        from lxml import html, etree
    except ImportError:
        return ExtractionResult(
            rule_name=rule.name,
            value=rule.default_value,
            success=False,
            error="XPath extraction requires lxml library"
        )

    try:
        tree = html.fromstring(html_content)
        elements = tree.xpath(rule.selector)

        if not elements:
            return ExtractionResult(
                rule_name=rule.name,
                value=rule.default_value if rule.multiple else None,
                success=True
            )

        if rule.multiple:
            values = []
            for element in elements:
                if hasattr(element, 'text') and element.text:
                    value = element.text.strip()
                elif hasattr(element, 'attrib') and rule.attribute:
                    value = element.attrib.get(rule.attribute, "")
                else:
                    value = etree.tostring(element, encoding='unicode', method='text').strip()

                if rule.transform:
                    value = rule.transform(value)
                values.append(value)
            return ExtractionResult(rule_name=rule.name, value=values, success=True)
        else:
            element = elements[0]
            if hasattr(element, 'text') and element.text:
                value = element.text.strip()
            elif hasattr(element, 'attrib') and rule.attribute:
                value = element.attrib.get(rule.attribute, "")
            else:
                value = etree.tostring(element, encoding='unicode', method='text').strip()

            if rule.transform:
                value = rule.transform(value)
            return ExtractionResult(rule_name=rule.name, value=value, success=True)

    except Exception as e:
        return ExtractionResult(
            rule_name=rule.name,
            value=rule.default_value,
            success=False,
            error=f"XPath error: {e}"
        )


def _extract_regex(self: 'HTMLExtractor', html_content: str, rule: ExtractionRule) -> ExtractionResult:
    """Extract data using regular expressions."""
    try:
        pattern = re.compile(rule.selector, re.MULTILINE | re.DOTALL)
        matches = pattern.findall(html_content)

        if not matches:
            return ExtractionResult(
                rule_name=rule.name,
                value=rule.default_value if rule.multiple else None,
                success=True
            )

        if rule.multiple:
            values = []
            for match in matches:
                value = match
                if rule.transform:
                    value = rule.transform(value)
                values.append(value)
            return ExtractionResult(rule_name=rule.name, value=values, success=True)
        else:
            value = matches[0]
            if rule.transform:
                value = rule.transform(value)
            return ExtractionResult(rule_name=rule.name, value=value, success=True)

    except Exception as e:
        return ExtractionResult(
            rule_name=rule.name,
            value=rule.default_value,
            success=False,
            error=f"Regex error: {e}"
        )


def _extract_attribute(self: 'HTMLExtractor', soup: Any, rule: ExtractionRule) -> ExtractionResult:
    """Extract element attribute value."""
    if soup is str:
        return ExtractionResult(
            rule_name=rule.name,
            value=rule.default_value,
            success=False,
            error="Attribute extraction requires BeautifulSoup"
        )

    try:
        elements = soup.select(rule.selector) if rule.selector else [soup]

        if not elements:
            return ExtractionResult(
                rule_name=rule.name,
                value=rule.default_value,
                success=True
            )

        if rule.multiple:
            values = []
            for element in elements:
                value = element.get(rule.attribute, rule.default_value)
                if rule.transform:
                    value = rule.transform(value)
                values.append(value)
            return ExtractionResult(rule_name=rule.name, value=values, success=True)
        else:
            element = elements[0]
            value = element.get(rule.attribute, rule.default_value)
            if rule.transform:
                value = rule.transform(value)
            return ExtractionResult(rule_name=rule.name, value=value, success=True)

    except Exception as e:
        return ExtractionResult(
            rule_name=rule.name,
            value=rule.default_value,
            success=False,
            error=f"Attribute extraction error: {e}"
        )


def _extract_text(self: 'HTMLExtractor', soup: Any, rule: ExtractionRule) -> ExtractionResult:
    """Extract text content from HTML."""
    if soup is str:
        return ExtractionResult(
            rule_name=rule.name,
            value=rule.default_value,
            success=False,
            error="Text extraction requires BeautifulSoup"
        )

    try:
        if rule.selector:
            elements = soup.select(rule.selector)
        else:
            elements = [soup]

        if not elements:
            return ExtractionResult(
                rule_name=rule.name,
                value=rule.default_value,
                success=True
            )

        if rule.multiple:
            values = []
            for element in elements:
                value = element.get_text(strip=True)
                if rule.transform:
                    value = rule.transform(value)
                values.append(value)
            return ExtractionResult(rule_name=rule.name, value=values, success=True)
        else:
            element = elements[0]
            value = element.get_text(strip=True)
            if rule.transform:
                value = rule.transform(value)
            return ExtractionResult(rule_name=rule.name, value=value, success=True)

    except Exception as e:
        return ExtractionResult(
            rule_name=rule.name,
            value=rule.default_value,
            success=False,
            error=f"Text extraction error: {e}"
        )


def _extract_html(self: 'HTMLExtractor', soup: Any, rule: ExtractionRule) -> ExtractionResult:
    """Extract HTML content."""
    if soup is str:
        return ExtractionResult(
            rule_name=rule.name,
            value=rule.default_value,
            success=False,
            error="HTML extraction requires BeautifulSoup"
        )

    try:
        if rule.selector:
            elements = soup.select(rule.selector)
        else:
            elements = [soup]

        if not elements:
            return ExtractionResult(
                rule_name=rule.name,
                value=rule.default_value,
                success=True
            )

        if rule.multiple:
            values = []
            for element in elements:
                value = str(element)
                if rule.transform:
                    value = rule.transform(value)
                values.append(value)
            return ExtractionResult(rule_name=rule.name, value=values, success=True)
        else:
            element = elements[0]
            value = str(element)
            if rule.transform:
                value = rule.transform(value)
            return ExtractionResult(rule_name=rule.name, value=value, success=True)

    except Exception as e:
        return ExtractionResult(
            rule_name=rule.name,
            value=rule.default_value,
            success=False,
            error=f"HTML extraction error: {e}"
        )


def _get_element_value(self: 'HTMLExtractor', element: Any, attribute: Optional[str]) -> Any:
    """Get value from HTML element."""
    if attribute:
        return element.get(attribute, "")
    else:
        return element.get_text(strip=True)


# Import utility functions
from .extractor_utils import create_extraction_rules, extract_data


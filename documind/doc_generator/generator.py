"""AI-powered documentation generator."""

import logging
from typing import Dict, List, Optional, Any

from app.core.exceptions import DocumentationError
from app.models.code_entity import CodeEntity
from app.models.documentation import Documentation

from .templates import DocTemplates


class DocGenerator:
    """AI-powered documentation generator."""

    def __init__(self):
        """Initialize the documentation generator."""
        self.logger = logging.getLogger(__name__)
        self.templates = DocTemplates()

        # AI models configuration
        self.models = {
            'openai': {
                'gpt-4': {'model': 'gpt-4', 'max_tokens': 2000, 'temperature': 0.3},
                'gpt-3.5-turbo': {'model': 'gpt-3.5-turbo', 'max_tokens': 1500, 'temperature': 0.3},
            },
            'anthropic': {
                'claude-3': {'model': 'claude-3-sonnet-20240229', 'max_tokens': 2000, 'temperature': 0.3},
            }
        }

        self.primary_model = 'gpt-4'

    async def generate_documentation(
        self,
        code_entity: CodeEntity,
        context: Optional[Dict[str, Any]] = None,
        model: Optional[str] = None
    ) -> Documentation:
        """
        Generate comprehensive documentation for a code entity.

        Args:
            code_entity: CodeEntity to document
            context: Additional context (repository, related entities, etc.)
            model: AI model to use

        Returns:
            Documentation object
        """
        try:
            model = model or self.primary_model
            context = context or {}

            self.logger.info(f"Generating documentation for {code_entity.qualified_name} using {model}")

            # Generate different documentation sections
            sections = await self._generate_doc_sections(code_entity, context)

            # Create the main documentation content
            content = await self._assemble_documentation(code_entity, sections)

            # Generate title and summary
            title = await self._generate_title(code_entity)
            summary = await self._generate_summary(code_entity, sections)

            # Calculate quality score
            quality_score = self._calculate_quality_score(sections)

            # Create documentation object
            documentation = Documentation(
                repository_id=code_entity.repository_id,
                code_entity_id=code_entity.id,
                title=title,
                content=content,
                summary=summary,
                sections=sections,
                doc_type='api',  # Could be determined based on entity type
                format='markdown',
                language=code_entity.language,
                generated_by='ai',
                generation_model=model,
                quality_score=quality_score,
                completeness_score=self._calculate_completeness_score(sections),
                accuracy_score=0.9,  # Assumed high for AI-generated
                readability_score=self._calculate_readability_score(content),
            )

            return documentation

        except Exception as e:
            self.logger.error(f"Documentation generation failed for {code_entity.qualified_name}: {e}")
            raise DocumentationError(f"Documentation generation failed: {e}")

    async def _generate_doc_sections(
        self,
        code_entity: CodeEntity,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate different sections of documentation."""
        sections = {}

        # Generate based on entity type
        if code_entity.entity_type == 'function':
            sections = await self._generate_function_docs(code_entity, context)
        elif code_entity.entity_type == 'class':
            sections = await self._generate_class_docs(code_entity, context)
        elif code_entity.entity_type == 'method':
            sections = await self._generate_method_docs(code_entity, context)
        else:
            sections = await self._generate_generic_docs(code_entity, context)

        return sections

    async def _generate_function_docs(
        self,
        code_entity: CodeEntity,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate documentation for a function."""
        sections = {}

        # Parameters section
        if code_entity.parameter_count and code_entity.parameter_count > 0:
            sections['parameters'] = await self._generate_parameters_section(code_entity)

        # Returns section
        if code_entity.return_type:
            sections['returns'] = await self._generate_returns_section(code_entity)

        # Examples section
        sections['examples'] = await self._generate_examples_section(code_entity)

        # Notes section
        sections['notes'] = await self._generate_notes_section(code_entity, context)

        return sections

    async def _generate_class_docs(
        self,
        code_entity: CodeEntity,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate documentation for a class."""
        sections = {}

        # Overview section
        sections['overview'] = await self._generate_class_overview(code_entity)

        # Methods section
        if hasattr(code_entity, 'methods') and code_entity.methods:
            sections['methods'] = await self._generate_methods_section(code_entity)

        # Inheritance section
        if hasattr(code_entity, 'inheritance') and code_entity.inheritance:
            sections['inheritance'] = await self._generate_inheritance_section(code_entity)

        # Examples section
        sections['examples'] = await self._generate_class_examples_section(code_entity)

        return sections

    async def _generate_method_docs(
        self,
        code_entity: CodeEntity,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate documentation for a method."""
        # Methods are similar to functions but with class context
        return await self._generate_function_docs(code_entity, context)

    async def _generate_generic_docs(
        self,
        code_entity: CodeEntity,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate documentation for generic entities."""
        sections = {}

        # Basic description
        sections['description'] = await self._generate_generic_description(code_entity)

        # Examples if applicable
        sections['examples'] = await self._generate_generic_examples(code_entity)

        return sections

    async def _generate_parameters_section(self, code_entity: CodeEntity) -> List[Dict[str, str]]:
        """Generate parameters documentation."""
        # This would use AI to analyze the function signature and generate parameter docs
        # For now, return a template structure
        return [
            {
                "name": "param1",
                "type": "str",
                "description": "Description of parameter 1"
            }
        ]

    async def _generate_returns_section(self, code_entity: CodeEntity) -> Dict[str, str]:
        """Generate returns documentation."""
        return {
            "type": code_entity.return_type or "Any",
            "description": f"Returns a {code_entity.return_type or 'value'}"
        }

    async def _generate_examples_section(self, code_entity: CodeEntity) -> List[Dict[str, str]]:
        """Generate usage examples."""
        return [
            {
                "language": code_entity.language,
                "code": f"# Example usage of {code_entity.name}\n{code_entity.name}()",
                "description": "Basic usage example"
            }
        ]

    async def _generate_notes_section(
        self,
        code_entity: CodeEntity,
        context: Dict[str, Any]
    ) -> List[str]:
        """Generate additional notes."""
        notes = []

        if code_entity.complexity_score and code_entity.complexity_score > 10:
            notes.append("This function has high complexity. Consider breaking it down into smaller functions.")

        if code_entity.is_async == "True":
            notes.append("This is an asynchronous function. Use 'await' when calling it.")

        return notes

    async def _generate_class_overview(self, code_entity: CodeEntity) -> str:
        """Generate class overview."""
        return f"The {code_entity.name} class provides functionality for..."

    async def _generate_methods_section(self, code_entity: CodeEntity) -> List[str]:
        """Generate methods list."""
        if hasattr(code_entity, 'methods'):
            return code_entity.methods
        return []

    async def _generate_inheritance_section(self, code_entity: CodeEntity) -> List[str]:
        """Generate inheritance information."""
        if hasattr(code_entity, 'inheritance'):
            return code_entity.inheritance
        return []

    async def _generate_class_examples_section(self, code_entity: CodeEntity) -> List[Dict[str, str]]:
        """Generate class usage examples."""
        return [
            {
                "language": code_entity.language,
                "code": f"# Example usage of {code_entity.name}\ninstance = {code_entity.name}()",
                "description": "Basic instantiation example"
            }
        ]

    async def _generate_generic_description(self, code_entity: CodeEntity) -> str:
        """Generate generic description."""
        return f"The {code_entity.name} {code_entity.entity_type} provides functionality for..."

    async def _generate_generic_examples(self, code_entity: CodeEntity) -> List[Dict[str, str]]:
        """Generate generic examples."""
        return [
            {
                "language": code_entity.language,
                "code": f"# Usage example\n{code_entity.name}",
                "description": "Basic usage"
            }
        ]

    async def _assemble_documentation(
        self,
        code_entity: CodeEntity,
        sections: Dict[str, Any]
    ) -> str:
        """Assemble all sections into final documentation."""
        content_parts = []

        # Title
        content_parts.append(f"# {code_entity.name}\n")

        # Description
        if 'description' in sections:
            content_parts.append(f"{sections['description']}\n")

        # Parameters
        if 'parameters' in sections:
            content_parts.append("## Parameters\n")
            for param in sections['parameters']:
                content_parts.append(f"- `{param['name']}` ({param['type']}): {param['description']}")
            content_parts.append("")

        # Returns
        if 'returns' in sections:
            content_parts.append("## Returns\n")
            returns = sections['returns']
            content_parts.append(f"- `{returns['type']}`: {returns['description']}\n")

        # Examples
        if 'examples' in sections:
            content_parts.append("## Examples\n")
            for example in sections['examples']:
                content_parts.append(f"```python\n{example['code']}\n```")
                content_parts.append(f"{example['description']}\n")

        # Notes
        if 'notes' in sections and sections['notes']:
            content_parts.append("## Notes\n")
            for note in sections['notes']:
                content_parts.append(f"- {note}")
            content_parts.append("")

        return "\n".join(content_parts)

    async def _generate_title(self, code_entity: CodeEntity) -> str:
        """Generate documentation title."""
        return f"{code_entity.name} - {code_entity.entity_type.title()}"

    async def _generate_summary(self, code_entity: CodeEntity, sections: Dict[str, Any]) -> str:
        """Generate documentation summary."""
        return f"Documentation for {code_entity.entity_type} {code_entity.name}"

    def _calculate_quality_score(self, sections: Dict[str, Any]) -> float:
        """Calculate documentation quality score."""
        score = 0.5  # Base score

        # Bonus for having parameters documented
        if 'parameters' in sections:
            score += 0.2

        # Bonus for having examples
        if 'examples' in sections and sections['examples']:
            score += 0.2

        # Bonus for having notes
        if 'notes' in sections and sections['notes']:
            score += 0.1

        return min(score, 1.0)

    def _calculate_completeness_score(self, sections: Dict[str, Any]) -> float:
        """Calculate documentation completeness score."""
        required_sections = ['description', 'examples']
        optional_sections = ['parameters', 'returns', 'notes']

        completed_required = sum(1 for section in required_sections if section in sections)
        completed_optional = sum(1 for section in optional_sections if section in sections)

        required_score = completed_required / len(required_sections)
        optional_score = completed_optional / len(optional_sections)

        return (required_score * 0.7) + (optional_score * 0.3)

    def _calculate_readability_score(self, content: str) -> float:
        """Calculate documentation readability score."""
        # Simple heuristic based on length and structure
        score = 0.7  # Base score

        # Bonus for having sections (headers)
        if '##' in content:
            score += 0.1

        # Bonus for having code examples
        if '```' in content:
            score += 0.1

        # Penalty for being too short
        if len(content) < 200:
            score -= 0.2

        return max(0.0, min(score, 1.0))

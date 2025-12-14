"""Documentation templates for different languages and entity types."""

from typing import Dict, List, Any


class DocTemplates:
    """Documentation templates for different programming constructs."""

    def __init__(self):
        """Initialize documentation templates."""
        self.templates = {
            'python': {
                'function': self._python_function_template,
                'class': self._python_class_template,
                'method': self._python_method_template,
                'module': self._python_module_template,
            },
            'javascript': {
                'function': self._js_function_template,
                'class': self._js_class_template,
                'method': self._js_method_template,
                'arrow_function': self._js_arrow_function_template,
            },
            'typescript': {
                'function': self._ts_function_template,
                'class': self._ts_class_template,
                'interface': self._ts_interface_template,
                'type': self._ts_type_template,
            },
            'java': {
                'class': self._java_class_template,
                'interface': self._java_interface_template,
                'method': self._java_method_template,
            },
            'go': {
                'function': self._go_function_template,
                'struct': self._go_struct_template,
                'interface': self._go_interface_template,
            },
            'rust': {
                'function': self._rust_function_template,
                'struct': self._rust_struct_template,
                'enum': self._rust_enum_template,
                'trait': self._rust_trait_template,
            }
        }

    def get_template(self, language: str, entity_type: str) -> callable:
        """Get documentation template for language and entity type."""
        if language in self.templates and entity_type in self.templates[language]:
            return self.templates[language][entity_type]
        return self._generic_template

    def _generic_template(self, entity: Dict[str, Any]) -> str:
        """Generic documentation template."""
        return f"""# {entity.get('name', 'Unknown')}

{entity.get('description', 'No description available.')}

## Usage

```python
{entity.get('name', 'entity')}()
```
"""

    def _python_function_template(self, entity: Dict[str, Any]) -> str:
        """Python function documentation template."""
        name = entity.get('name', 'function')
        signature = entity.get('signature', f'def {name}()')
        params = entity.get('parameters', [])
        returns = entity.get('returns', {})

        template = f"""# {name}

{entity.get('description', f'A Python function that performs {name} operation.')}

## Signature

```python
{signature}
```

"""

        if params:
            template += "## Parameters\n\n"
            for param in params:
                template += f"- `{param['name']}` ({param.get('type', 'Any')}): {param.get('description', 'Parameter description')}\n"
            template += "\n"

        if returns:
            template += f"## Returns\n\n- `{returns.get('type', 'Any')}`: {returns.get('description', 'Return value description')}\n\n"

        template += f"""## Example

```python
# Basic usage
result = {name}()
```

## Notes

- This function is {'async' if entity.get('is_async') else 'synchronous'}
- Complexity score: {entity.get('complexity', 'N/A')}
"""

        return template

    def _python_class_template(self, entity: Dict[str, Any]) -> str:
        """Python class documentation template."""
        name = entity.get('name', 'Class')
        inheritance = entity.get('inheritance', [])
        methods = entity.get('methods', [])

        template = f"""# {name} Class

{entity.get('description', f'A Python class that implements {name} functionality.')}

## Inheritance

"""

        if inheritance:
            for base in inheritance:
                template += f"- Inherits from `{base}`\n"
        else:
            template += "- No inheritance\n"

        template += f"""

## Methods

"""

        if methods:
            for method in methods[:10]:  # Limit to first 10 methods
                template += f"- `{method}`()\n"
        else:
            template += "No methods documented\n"

        template += f"""

## Example

```python
# Create instance
instance = {name}()

# Use methods
instance.some_method()
```

## Notes

- Class complexity: {len(methods) if methods else 0} methods
- Located in: {entity.get('file_path', 'Unknown file')}
"""

        return template

    def _python_method_template(self, entity: Dict[str, Any]) -> str:
        """Python method documentation template."""
        # Methods are similar to functions but within class context
        return self._python_function_template(entity)

    def _python_module_template(self, entity: Dict[str, Any]) -> str:
        """Python module documentation template."""
        name = entity.get('name', 'module')

        return f"""# {name} Module

{entity.get('description', f'A Python module containing {name} functionality.')}

## Overview

This module provides functionality for {name} operations.

## Usage

```python
import {name}
# or
from {name} import specific_function
```

## Contents

- Functions: {entity.get('function_count', 'Unknown')}
- Classes: {entity.get('class_count', 'Unknown')}
- Constants: {entity.get('constant_count', 'Unknown')}
"""

    def _js_function_template(self, entity: Dict[str, Any]) -> str:
        """JavaScript function documentation template."""
        name = entity.get('name', 'function')

        return f"""# {name} Function

{entity.get('description', f'A JavaScript function that performs {name} operation.')}

## Syntax

```javascript
{name}()
```

## Example

```javascript
// Basic usage
const result = {name}();
```

## Notes

- Language: JavaScript
- Located in: {entity.get('file_path', 'Unknown file')}
"""

    def _js_class_template(self, entity: Dict[str, Any]) -> str:
        """JavaScript class documentation template."""
        name = entity.get('name', 'Class')

        return f"""# {name} Class

{entity.get('description', f'A JavaScript class that implements {name} functionality.')}

## Constructor

```javascript
const instance = new {name}();
```

## Methods

- Constructor and methods are dynamically analyzed

## Example

```javascript
// Create instance
const instance = new {name}();

// Use methods
instance.someMethod();
```

## Notes

- ES6 class syntax
- Located in: {entity.get('file_path', 'Unknown file')}
"""

    def _js_method_template(self, entity: Dict[str, Any]) -> str:
        """JavaScript method documentation template."""
        return self._js_function_template(entity)

    def _js_arrow_function_template(self, entity: Dict[str, Any]) -> str:
        """JavaScript arrow function documentation template."""
        name = entity.get('name', 'arrowFunction')

        return f"""# {name} Arrow Function

{entity.get('description', f'An arrow function that performs {name} operation.')}

## Syntax

```javascript
const {name} = () => {{
  // implementation
}};
```

## Example

```javascript
// Usage
const result = {name}();
```

## Notes

- Arrow function syntax
- Located in: {entity.get('file_path', 'Unknown file')}
"""

    def _ts_function_template(self, entity: Dict[str, Any]) -> str:
        """TypeScript function documentation template."""
        name = entity.get('name', 'function')

        return f"""# {name} Function

{entity.get('description', f'A TypeScript function that performs {name} operation.')}

## Type Signature

```typescript
function {name}(): any;
```

## Example

```typescript
// Basic usage
const result = {name}();
```

## Notes

- Language: TypeScript
- Type-safe implementation
- Located in: {entity.get('file_path', 'Unknown file')}
"""

    def _ts_class_template(self, entity: Dict[str, Any]) -> str:
        """TypeScript class documentation template."""
        return self._js_class_template(entity)

    def _ts_interface_template(self, entity: Dict[str, Any]) -> str:
        """TypeScript interface documentation template."""
        name = entity.get('name', 'Interface')

        return f"""# {name} Interface

{entity.get('description', f'A TypeScript interface that defines {name} contract.')}

## Definition

```typescript
interface {name} {{
  // Properties and methods
}}
```

## Implementation

```typescript
class MyClass implements {name} {{
  // Implementation
}}
```

## Notes

- TypeScript interface
- Defines contract for implementations
- Located in: {entity.get('file_path', 'Unknown file')}
"""

    def _ts_type_template(self, entity: Dict[str, Any]) -> str:
        """TypeScript type documentation template."""
        name = entity.get('name', 'Type')

        return f"""# {name} Type

{entity.get('description', f'A TypeScript type definition for {name}.')}

## Definition

```typescript
type {name} = // type definition
```

## Usage

```typescript
const myVar: {name} = // value
```

## Notes

- TypeScript type alias
- Provides type safety
- Located in: {entity.get('file_path', 'Unknown file')}
"""

    # Java, Go, and Rust templates would follow similar patterns
    # For brevity, I'll define them as generic fallbacks

    def _java_class_template(self, entity: Dict[str, Any]) -> str:
        """Java class documentation template."""
        return self._generic_template(entity)

    def _java_interface_template(self, entity: Dict[str, Any]) -> str:
        """Java interface documentation template."""
        return self._generic_template(entity)

    def _java_method_template(self, entity: Dict[str, Any]) -> str:
        """Java method documentation template."""
        return self._generic_template(entity)

    def _go_function_template(self, entity: Dict[str, Any]) -> str:
        """Go function documentation template."""
        return self._generic_template(entity)

    def _go_struct_template(self, entity: Dict[str, Any]) -> str:
        """Go struct documentation template."""
        return self._generic_template(entity)

    def _go_interface_template(self, entity: Dict[str, Any]) -> str:
        """Go interface documentation template."""
        return self._generic_template(entity)

    def _rust_function_template(self, entity: Dict[str, Any]) -> str:
        """Rust function documentation template."""
        return self._generic_template(entity)

    def _rust_struct_template(self, entity: Dict[str, Any]) -> str:
        """Rust struct documentation template."""
        return self._generic_template(entity)

    def _rust_enum_template(self, entity: Dict[str, Any]) -> str:
        """Rust enum documentation template."""
        return self._generic_template(entity)

    def _rust_trait_template(self, entity: Dict[str, Any]) -> str:
        """Rust trait documentation template."""
        return self._generic_template(entity)

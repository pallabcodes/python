# Python3 Mastery for Systems Engineers

An authoritative, zero-config knowledgebase for senior full-stack and systems engineers (L5+) transitioning from C/C++ or JVM languages. This repository prioritizes mechanical sympathy, the Python Data Model, and production-scale patterns over basic syntax.

## 🗺️ Roadmap

1.  **[m01_fundamentals/](file:///home/vadmin/Projects/python/m01_fundamentals/)**: Beyond basic syntax. Scoping, closures, and modern control flow (match/case).
2.  **[m02_data_model/](file:///home/vadmin/Projects/python/m02_data_model/)**: The core of Python. Memory layout, reference semantics, and the descriptor protocol.
3.  **[m03_oop/](file:///home/vadmin/Projects/python/m03_oop/)**: MRO deep-dives, Abstract Base Classes, and Structural Typing (Protocols).
4.  **[m04_functions_advanced/](file:///home/vadmin/Projects/python/m04_functions_advanced/)**: Decorators, Context Managers (RAII), and Generators.
5.  **[m05_type_system/](file:///home/vadmin/Projects/python/m05_type_system/)**: Static analysis with mypy, Generics, and TypeGuards.
6.  **[m06_error_handling/](file:///home/vadmin/Projects/python/m06_error_handling/)**: Exception groups and modern error patterns.
7.  **[m07_concurrency/](file:///home/vadmin/Projects/python/m07_concurrency/)**: GIL mechanics, threading, multiprocessing, and modern `asyncio`.
8.  **[m08_c_interop/](file:///home/vadmin/Projects/python/m08_c_interop/)**: Calling C/C++ from Python (ctypes, cffi, extensions).
9.  **[m09_stdlib_essentials/](file:///home/vadmin/Projects/python/m09_stdlib_essentials/)**: High-performance collections and itertools.
10. **[m10_testing/](file:///home/vadmin/Projects/python/m10_testing/)**: Production-grade testing with pytest.
11. **[m11_packaging/](file:///home/vadmin/Projects/python/m11_packaging/)**: Modern dependency management and distribution.
12. **[m12_scaling_python/](file:///home/vadmin/Projects/python/m12_scaling_python/)**: Elite scaling (Metaclasses, Advanced Asyncio, Pydantic, Profiling, Native extensions).

## 🚀 Quick Start

Ensure you have Python 3.12+ installed.

```bash
# Initialize environment
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Run a module
python -m m01_fundamentals.s01_variables_and_types
```

## 🛠️ Tooling

- **Linter/Formatter**: [Ruff](https://github.com/astral-sh/ruff)
- **Type Checker**: [Mypy](https://github.com/python/mypy)
- **Test Runner**: [Pytest](https://github.com/pytest-dev/pytest)

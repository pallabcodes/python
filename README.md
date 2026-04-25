# Python Mastery

A structured, zero-config knowledgebase for mastering Python 3.12+ with a focus on systems engineering and performance.

## 🗺️ Roadmap

1.  **[m01_fundamentals/](m01_fundamentals/)**: Scoping, closures, and modern control flow (match/case).
2.  **[m02_data_model/](m02_data_model/)**: Memory layout, reference semantics, and descriptors.
3.  **[m03_oop/](m03_oop/)**: MRO deep-dives, ABCs, and Protocols.
4.  **[m04_functions_advanced/](m04_functions_advanced/)**: Decorators, Context Managers, and Generators.
5.  **[m05_type_system/](m05_type_system/)**: Static analysis with Mypy, Generics, and TypeGuards.
6.  **[m06_error_handling/](m06_error_handling/)**: Exception groups and modern error patterns.
7.  **[m07_concurrency/](m07_concurrency/)**: GIL mechanics, threading, multiprocessing, and asyncio.
8.  **[m08_c_interop/](m08_c_interop/)**: Native interop (ctypes, buffer protocol).
9.  **[m09_stdlib_essentials/](m09_stdlib_essentials/)**: High-performance collections and itertools.
10. **[m10_testing/](m10_testing/)**: Production-grade testing with Pytest.
11. **[m11_packaging/](m11_packaging/)**: Dependency management and distribution.
12. **[m12_scaling_python/](m12_scaling_python/)**: Elite scaling (Metaclasses, Profiling, Native extensions).

## 🚀 Getting Started

This project uses [uv](https://github.com/astral-sh/uv) for high-performance dependency management.

```bash
# Install dependencies and setup environment
uv sync

# Run a specific module
uv run python -m m01_fundamentals.s01_variables_and_types

# Run tests
uv run pytest
```

## 🛠️ Tooling

- **Linter/Formatter**: [Ruff](https://github.com/astral-sh/ruff)
- **Type Checker**: [Mypy](https://github.com/python/mypy)
- **Test Runner**: [Pytest](https://github.com/pytest-dev/pytest)

---
*For internal engineering standards and philosophy, see [docs/philosophy.md](docs/philosophy.md).*

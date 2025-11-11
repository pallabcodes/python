"""
Asyncio examples demonstrating async/await programming.

This module provides comprehensive examples of asyncio concepts including:
- Basic coroutines and event loops
- Concurrent execution patterns
- Async I/O operations
- Synchronization primitives
- Task management and cancellation
- Async context managers and generators
- Real-world async applications
"""

from .basic_asyncio import BasicAsyncioExample
from .async_context_managers import AsyncContextManagerExample
from .async_generators import AsyncGeneratorExample
from .concurrency_patterns import ConcurrencyPatternsExample
from .async_io import AsyncIOExample
from .async_primitives import AsyncPrimitivesExample
from .task_management import TaskManagementExample
from .async_patterns import AsyncPatternsExample
from .web_asyncio import WebAsyncioExample
from .asyncio_demo import AsyncioDemo

"""
-- __all__ is a special variable (not a keyword, but a convention) that Python recognizes
-- as a way to export symbols from a module. When you do:
-- __all__ = ["symbol1", "symbol2", ...]
-- it tells Python that only these symbols should be exported when the module is imported with:
-- Controlled imports: When someone does from asyncio_examples import *, they'll only get these 10 classes, not all the internal functions, variables, or other modulesfrom module_name import *
-- Clean API: It defines the module's public interface - these are the classes users should use
-- Documentation: It serves as documentation showing what's available to users

# This will import only the classes listed in __all__
from asyncio_examples import *

# Now you can use:
example = BasicAsyncioExample()
# etc.

Without __all__:
If __all__ wasn't defined, from asyncio_examples import * would import everything that's not private (doesn't start with _), which could include internal functions, imported modules, etc. - leading to namespace pollution.
So __all__ here acts as an explicit whitelist of what the module exposes as its public API. It's a best practice for packages and modules that want to control their public interface.

"""

__all__ = [
    "BasicAsyncioExample",
    "AsyncContextManagerExample",
    "AsyncGeneratorExample",
    "ConcurrencyPatternsExample",
    "AsyncIOExample",
    "AsyncPrimitivesExample",
    "TaskManagementExample",
    "AsyncPatternsExample",
    "WebAsyncioExample",
    "AsyncioDemo"
]


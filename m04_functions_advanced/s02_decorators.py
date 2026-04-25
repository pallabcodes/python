"""
Module: Decorators — Metaprogramming with Functions

Key Insights:
1. Decorators are Higher-Order Functions that wrap other functions.
2. Syntax: '@decorator' is syntactic sugar for 'func = decorator(func)'.
3. Always use 'functools.wraps' to preserve metadata (__name__, __doc__).
"""

import functools
import time

# 1. Simple Decorator
def log_execution(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        print(f"Executing {func.__name__}...")
        result = func(*args, **kwargs)
        print(f"{func.__name__} finished.")
        return result
    return wrapper

@log_execution
def add(x, y):
    """Adds two numbers."""
    return x + y

print(add(5, 7))
print(f"Metadata preserved? Name: {add.__name__}, Doc: {add.__doc__}")

# 2. Decorator with Arguments
def repeat(times):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for _ in range(times):
                result = func(*args, **kwargs)
            return result
        return wrapper
    return decorator

@repeat(times=3)
def greet(name):
    print(f"Hello {name}")

greet("Alice")

# 3. Class-based Decorator
class Timer:
    def __init__(self, func):
        functools.update_wrapper(self, func)
        self.func = func

    def __call__(self, *args, **kwargs):
        start = time.perf_counter()
        result = self.func(*args, **kwargs)
        end = time.perf_counter()
        print(f"Execution time: {end - start:.6f}s")
        return result

@Timer
def heavy_calc():
    return sum(range(10**6))

heavy_calc()

if __name__ == "__main__":
    pass

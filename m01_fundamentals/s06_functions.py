"""
Module: Functions, Scoping, and First-Class Citizens
Target: L5+ Systems Engineers

Key Insights:
1. Functions are objects (First-Class Citizens).
2. LEGB Scoping: Local -> Enclosing -> Global -> Built-in.
3. Param passing: Everything is passed by "object reference".
"""

from typing import List, Optional

# 1. Basic Function with Type Hints (3.5+)
def calculate_mpg(mileage: float, fuel: float) -> float:
    """Calculates miles per gallon."""
    if fuel <= 0:
        raise ValueError("Fuel must be positive")
    return mileage / fuel

# 2. Argument Flexibility (*args, **kwargs)
def log_event(message: str, *tags: str, **metadata: str) -> None:
    print(f"MSG: {message}")
    if tags:
        print(f"TAGS: {tags}")
    if metadata:
        print(f"META: {metadata}")

log_event("Connection lost", "network", "critical", host="10.0.0.1", retry=True)

# 3. Default Arguments (The Pitfall)
# WARNING: Never use a mutable object (list, dict) as a default!
def add_item(item: str, items: Optional[List[str]] = None) -> List[str]:
    if items is None:
        items = []
    items.append(item)
    return items

# 4. Closures and Enclosing Scope
# Equivalent to a C++ lambda with capture by reference.
def make_counter():
    count = 0
    def increment():
        nonlocal count  # 'nonlocal' allows modifying variable in the enclosing scope
        count += 1
        return count
    return increment

counter = make_counter()
print(f"Count: {counter()}")
print(f"Count: {counter()}")

# 5. First-Class Functions
# Passing functions as arguments (Higher Order Functions)
def transform(data: List[int], func) -> List[int]:
    return [func(x) for x in data]

nums = [1, 2, 3]
print(transform(nums, lambda x: x**2))

if __name__ == "__main__":
    pass

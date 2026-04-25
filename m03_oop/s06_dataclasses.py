"""
Module: Dataclasses — Boilerplate-free Data Objects

Key Insights for C++ Engineers:
1. '@dataclass' (3.7+) generates __init__, __repr__, __eq__, etc. automatically.
2. Similar to C++20 'default' operations or Java Records.
3. Supports immutability via 'frozen=True'.
"""

from dataclasses import dataclass, field
from typing import List

@dataclass(frozen=True)  # Immutable dataclass
class User:
    id: int
    username: str
    # Default value
    active: bool = True
    # Default factory for mutable objects
    tags: List[str] = field(default_factory=list)

# 1. Automatic Methods
u1 = User(1, "jose")
u2 = User(1, "jose")
print(u1)  # Nice __repr__
print(f"u1 == u2? {u1 == u2}")  # Value-based equality

# 2. Immutability
try:
    u1.username = "new_name"
except Exception as e:
    print(f"Caught error on frozen dataclass: {e}")

# 3. Inheritance with dataclasses
@dataclass
class Admin(User):
    admin_level: int = 1

a = Admin(2, "root", admin_level=10)
print(a)

# 4. Conversion
from dataclasses import asdict, astuple
print(f"As Dict: {asdict(u1)}")
print(f"As Tuple: {astuple(u1)}")

if __name__ == "__main__":
    pass

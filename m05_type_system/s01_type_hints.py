"""
Module: Modern Type Hinting and Static Analysis
Target: L5+ Systems Engineers

Key Insights:
1. Type hints are for STATIC ANALYSIS (mypy, pyright). They are NOT enforced at runtime.
2. 'Any' is the "escape hatch" (avoid if possible).
3. 'Protocol' vs 'Generic': Structural vs Parametric polymorphism.
"""

from typing import List, Dict, Optional, Union, Any, Callable, TypeVar, Generic

# 1. Basic Containers
def process_users(users: List[str]) -> Dict[str, int]:
    return {user: len(user) for user in users}

# 2. Optional and Union
# In 3.10+, Union[str, int] can be written as str | int
# Optional[str] is str | None
def get_user_id(name: str) -> str | int | None:
    if name == "admin": return 0
    if name == "guest": return "G-1"
    return None

# 3. Type Aliases (3.10 Style)
from typing import TypeAlias
UserID: TypeAlias = Union[str, int]
# In 3.12+, you can use: type UserID = str | int
def find_by_id(id: UserID):
    pass

# 4. Generics (Parametric Polymorphism)
T = TypeVar('T')

class Box(Generic[T]):
    def __init__(self, content: T):
        self.content = content
    
    def get(self) -> T:
        return self.content

int_box = Box(42)
str_box = Box("Hello")

# 5. Callables (Function pointers)
def execute(action: Callable[[int, int], int], a: int, b: int) -> int:
    return action(a, b)

print(execute(lambda x, y: x + y, 10, 20))

if __name__ == "__main__":
    pass

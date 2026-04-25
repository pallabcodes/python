"""
Module: Protocols — Structural Subtyping (Static Duck Typing)
Target: L5+ Systems Engineers

Key Insights:
1. 'Protocol' (PEP 544) allows for structural typing (like Go interfaces).
2. Unlike ABCs, a class doesn't need to inherit from the Protocol.
3. If it has the right methods, it matches the Protocol (Duck Typing).
"""

from typing import Protocol, runtime_checkable

@runtime_checkable
class Drawable(Protocol):
    def draw(self) -> None:
        ...

class Button:
    def draw(self) -> None:
        print("Drawing a button")

class Icon:
    def draw(self) -> None:
        print("Drawing an icon")

class NonDrawable:
    pass

def render(obj: Drawable) -> None:
    # Static type checkers (mypy) will verify 'obj' has a 'draw' method.
    obj.draw()

# 1. Usage
render(Button())
render(Icon())

# 2. Runtime check (requires @runtime_checkable)
print(f"Is Button drawable? {isinstance(Button(), Drawable)}")
print(f"Is NonDrawable drawable? {isinstance(NonDrawable(), Drawable)}")

# Why use Protocols over ABCs?
# 1. Decoupling: You can define an interface for 3rd party classes you don't control.
# 2. Flexibility: Better matches Python's dynamic "duck typing" nature while keeping static safety.

if __name__ == "__main__":
    pass

"""
Module: Abstract Base Classes (ABCs) — Nominal Typing

Key Insights for C++/Java Engineers:
1. ABCs are the equivalent of "Pure Virtual Classes" or "Interfaces".
2. You cannot instantiate an ABC that has unimplemented @abstractmethods.
3. Subclasses MUST override all abstract methods to be instantiable.
"""

from abc import ABC, abstractmethod

class Shape(ABC):
    @abstractmethod
    def area(self) -> float:
        """Calculate the area of the shape."""
        pass

    @abstractmethod
    def perimeter(self) -> float:
        pass

    def describe(self):
        # Concrete method in an ABC
        print(f"I am a {type(self).__name__} with area {self.area()}")

class Circle(Shape):
    def __init__(self, radius: float):
        self.radius = radius

    def area(self) -> float:
        return 3.14159 * self.radius ** 2

    def perimeter(self) -> float:
        return 2 * 3.14159 * self.radius

# 1. Attempting to instantiate an ABC
try:
    s = Shape()
except TypeError as e:
    print(f"Error instantiating ABC: {e}")

# 2. Valid instantiation
c = Circle(5.0)
c.describe()

# 3. Virtual Subclassing (The 'register' magic)
# You can make a class "look like" a subclass of an ABC without inheriting from it.
class ExternalShape:
    def area(self): return 10.0
    def perimeter(self): return 20.0

Shape.register(ExternalShape)
ext = ExternalShape()
print(f"Is ExternalShape a Shape? {isinstance(ext, Shape)}")  # True!

if __name__ == "__main__":
    pass

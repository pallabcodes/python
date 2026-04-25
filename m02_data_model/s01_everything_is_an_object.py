"""
Module: Python Data Model — Everything is an Object

Key Insights for C/C++ Engineers:
1. In Python, types are objects, functions are objects, and even classes are objects.
2. The 'type' of a class is 'type' (the metaclass).
3. Inheritance hierarchy ends at 'object'.
"""

# 1. Inspecting objects
x = 42
print(f"Value: {x}")
print(f"Type: {type(x)}")
print(f"ID (Memory Address): {hex(id(x))}")

# 2. Functions are objects
def greet():
    return "Hello"

print(f"Function Type: {type(greet)}")
print(f"Function Docstring: {greet.__doc__}")

# 3. Classes are objects (Metaclasses)
class MyClass:
    pass

print(f"Class Type: {type(MyClass)}")  # <class 'type'>
# type is the constructor for classes.

# 4. The 'object' root
print(f"Is MyClass an instance of object? {isinstance(MyClass, object)}")
print(f"Is int an instance of object? {isinstance(int, object)}")

# 5. Dunder attributes
# Every object has a __dict__ (if not using __slots__) that stores its attributes.
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

p = Point(1, 2)
print(f"Point Attributes: {p.__dict__}")

# You can even inject attributes at runtime (unlike C++)
p.z = 3
print(f"Updated Attributes: {p.__dict__}")

if __name__ == "__main__":
    pass

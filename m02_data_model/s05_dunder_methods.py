"""
Module: Dunder (Double Underscore) Methods — The Python Protocols
Target: L5+ Systems Engineers

Key Insights:
1. Dunder methods are hooks into Python's syntax (operator overloading, iteration).
2. '__new__' is the allocator; '__init__' is the initializer.
3. To be used as a dict key, an object must be Hashable (__hash__ + __eq__).
"""

class Vector:
    def __new__(cls, *args, **kwargs):
        # Called BEFORE __init__ to create the instance.
        # Rarely overridden except in singleton patterns or immutable types.
        print("Allocating memory for Vector...")
        return super().__new__(cls)

    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

    # 1. String Representation
    def __repr__(self):
        # Developer-friendly (should look like the constructor call)
        return f"Vector({self.x}, {self.y})"

    def __str__(self):
        # User-friendly
        return f"({self.x}i + {self.y}j)"

    # 2. Arithmetic (Operator Overloading)
    def __add__(self, other):
        if not isinstance(other, Vector):
            return NotImplemented
        return Vector(self.x + other.x, self.y + other.y)

    # 3. Equality and Hashing
    def __eq__(self, other):
        if not isinstance(other, Vector):
            return False
        return self.x == other.x and self.y == other.y

    def __hash__(self):
        # Objects must be immutable to be hashable!
        return hash((self.x, self.y))

    # 4. Length and Container Protocol
    def __len__(self):
        return 2

    def __getitem__(self, index):
        if index == 0: return self.x
        if index == 1: return self.y
        raise IndexError("Vector index out of range")

# Usage
v1 = Vector(3, 4)
v2 = Vector(1, 2)
v3 = v1 + v2

print(f"v3 repr: {repr(v3)}")
print(f"v3 str: {v3}")
print(f"v3 length: {len(v3)}")
print(f"v3[0]: {v3[0]}")

# Testing hashing (can it be in a set?)
vectors = {v1, v2, v3}
print(f"Set of vectors: {vectors}")

if __name__ == "__main__":
    pass

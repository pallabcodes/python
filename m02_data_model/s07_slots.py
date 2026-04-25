"""
Module: Memory Optimization with __slots__
Target: L5+ Systems Engineers

Key Insights for C/C++ Engineers:
1. By default, every Python object stores attributes in a hash map (__dict__).
2. '__slots__' fixes the attribute names and stores them in an array-like structure.
3. This significantly reduces memory footprint and slightly increases attribute access speed.
"""

import sys

# 1. Standard Class (uses __dict__)
class PointStandard:
    def __init__(self, x, y):
        self.x = x
        self.y = y

# 2. Slotted Class
class PointSlotted:
    __slots__ = ("x", "y")  # Pre-declares allowed attributes
    def __init__(self, x, y):
        self.x = x
        self.y = y

p1 = PointStandard(1, 2)
p2 = PointSlotted(1, 2)

# Memory comparison
# Note: sys.getsizeof doesn't fully capture the __dict__ size.
print(f"Standard instance size: {sys.getsizeof(p1)}")
print(f"Slotted instance size: {sys.getsizeof(p2)}")

# Slotted objects don't have a __dict__
try:
    print(p1.__dict__)
    print(p2.__dict__)
except AttributeError:
    print("Slotted object has no __dict__")

# Slotted objects prevent dynamic attribute injection (Safety/Optimization)
try:
    p2.z = 10
except AttributeError as e:
    print(f"Caught expected error: {e}")

# Performance Insight:
# In C++ terms, __slots__ is like defining a struct with fixed fields, 
# whereas a regular Python class is like a std::unordered_map<string, PyObject*>.

if __name__ == "__main__":
    pass

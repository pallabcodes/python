"""
Module: Python Memory Model and Garbage Collection

Key Insights:
1. CPython primarily uses REFERENCE COUNTING.
2. A Cyclic Garbage Collector handles reference cycles.
3. 'sys.getsizeof' only returns the size of the object itself, not the objects it points to.
"""

import sys
import gc

# 1. Reference Counting
a = [1, 2, 3]
print(f"Ref count for a: {sys.getrefcount(a)}")  # Usually 2 (a + argument to getrefcount)

b = a
print(f"Ref count after b=a: {sys.getrefcount(a)}") # 3

# 2. Reference Cycles (Why we need GC)
class Node:
    def __init__(self):
        self.next = None

n1 = Node()
n2 = Node()
n1.next = n2
n2.next = n1  # Cycle created!

del n1
del n2
# Even though names are deleted, ref count is still 1 due to the cycle.
# The Cyclic GC will eventually find and reap these.

# 3. Object Overhead
# Python objects are "heavy" compared to C structs.
x = 0
print(f"Size of integer 0: {sys.getsizeof(x)} bytes")
y = "Hello"
print(f"Size of string 'Hello': {sys.getsizeof(y)} bytes")

# Empty list overhead
empty_list = []
print(f"Size of empty list: {sys.getsizeof(empty_list)} bytes")

# 4. Manual GC Control
gc.collect()  # Trigger manual collection
print(f"GC Thresholds: {gc.get_threshold()}")

if __name__ == "__main__":
    pass

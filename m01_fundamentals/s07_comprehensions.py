"""
Module: Comprehensions and Generator Expressions
Target: L5+ Systems Engineers

Key Insights:
1. Comprehensions are more efficient than manual .append() loops.
2. Generator expressions are memory-efficient (lazy evaluation).
"""

# 1. List Comprehensions
nums = [1, 2, 3, 4, 5]
squares = [x**2 for x in nums if x % 2 == 1]
print(f"Odd squares: {squares}")

# 2. Dictionary Comprehensions
users = [("rolf", 24), ("bob", 30), ("anne", 27)]
user_map = {name: age for name, age in users if age > 25}
print(f"Users > 25: {user_map}")

# 3. Set Comprehensions
names = ["Rolf", "Bob", "Jen", "Rolf"]
unique_lowered = {name.lower() for name in names}
print(f"Unique lowercase: {unique_lowered}")

# 4. Generator Expressions (Memory Efficient)
# Similar to a comprehension but returns an iterator, not a collection.
# Use this for massive datasets where you don't need everything in RAM at once.
huge_range = (x**2 for x in range(10**12))
print(f"First square: {next(huge_range)}")
print(f"Second square: {next(huge_range)}")
# Memory footprint is constant regardless of the range size.

# 5. Nested Comprehensions
# Matrix flattening
matrix = [[1, 2], [3, 4], [5, 6]]
flat = [x for row in matrix for x in row]
print(f"Flattened: {flat}")

if __name__ == "__main__":
    pass

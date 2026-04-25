"""
Module: Mutability and Identity
Target: L5+ Systems Engineers

Key Insights:
1. 'is' vs '==': Identity vs Equality.
2. Mutable types: list, dict, set, bytearray.
3. Immutable types: int, float, str, tuple, bytes, frozenset.
4. The 'interning' optimization for small integers and strings.
"""

import copy

# 1. Identity vs Equality
a = [1, 2, 3]
b = [1, 2, 3]
print(f"a == b: {a == b}")  # True (Values match)
print(f"a is b: {a is b}")  # False (Different memory addresses)

# 2. Integer Interning (Optimization)
# Python pre-allocates small integers (-5 to 256) for performance.
x = 256
y = 256
print(f"256 is 256: {x is y}")  # True

x = 257
y = 257
print(f"257 is 257: {x is y}")  # False (Might be True in REPL/certain versions due to peephole optimization)

# 3. Mutability Pitfalls
# Tuples are immutable, but their elements can be mutable!
t = ([1, 2], 3)
# t[0] = [1, 2, 3]  # TypeError
t[0].append(3)      # Works! The tuple still points to the SAME list object.
print(f"Modified tuple: {t}")

# 4. Shallow vs Deep Copy
original = [[1, 2], [3, 4]]

# Shallow copy: New container, same inner objects.
shallow = copy.copy(original)
shallow[0].append(99)
print(f"Original after shallow mod: {original}")  # [[1, 2, 99], [3, 4]]

# Deep copy: Recursive copy of all objects.
original = [[1, 2], [3, 4]]
deep = copy.deepcopy(original)
deep[0].append(99)
print(f"Original after deep mod: {original}")    # [[1, 2], [3, 4]]

if __name__ == "__main__":
    pass

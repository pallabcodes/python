"""
Module: Reference Semantics and Argument Passing
Target: L5+ Systems Engineers

Key Insights for C/C++ Engineers:
1. Python uses "Pass by Object Reference" (or "Pass by Assignment").
2. Re-assigning a name inside a function does NOT affect the caller.
3. Mutating a passed mutable object DOES affect the caller.
"""

def modify_list(items):
    # This MUTATES the object pointed to by 'items'.
    items.append(4)

def reassign_list(items):
    # This RE-BINDS the name 'items' to a NEW list object.
    # The original object in the caller's scope is untouched.
    items = [1, 2, 3, 4]

my_list = [1, 2, 3]

modify_list(my_list)
print(f"After modify: {my_list}")  # [1, 2, 3, 4]

reassign_list(my_list)
print(f"After reassign: {my_list}") # [1, 2, 3, 4] (Still the same object)

# The "Shared Reference" Trap
a = [1, 2, 3]
b = a
b.append(4)
print(f"a: {a}")  # [1, 2, 3, 4]

# How to avoid it?
b = a[:]  # Slicing creates a shallow copy
# or b = a.copy()
# or b = list(a)

if __name__ == "__main__":
    pass

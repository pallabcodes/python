"""
Module: Variables, Identity, and Built-in Types
Target: L5+ Systems Engineers (C/C++ Background)

Key Insights for C/C++ Engineers:
1. Python variables are NOT memory locations; they are NAMES bound to OBJECTS.
2. Every object has an identity (address), a type, and a value.
3. Integers in Python 3 are arbitrary precision (no overflow).
"""

import sys

# 1. Names and Binding (The "Variable" Myth)
# In C: int x = 10; (x is a memory location)
# In Python: x = 10 (x is a name pointing to an integer object 10)
age = 29
print(f"Value: {age}, ID: {id(age)}, Type: {type(age)}")

# Python names follow snake_case by convention.
# All-caps indicates a "constant" (though Python doesn't enforce this at runtime).
PI = 3.14159
RADIANS_TO_DEGREES = 180 / PI

# 2. Integers (Arbitrary Precision)
# Python ints are not limited by 32/64-bit boundaries.
large_num = 10**100  # A "googol"
print(f"Googol size in bytes: {sys.getsizeof(large_num)}")

# 3. Floating Point (IEEE 754)
# Equivalent to 'double' in C.
f_val = 0.1 + 0.2
print(f"0.1 + 0.2 == 0.3? {f_val == 0.3} (Result: {f_val})")  # Floating point precision issue

# 4. Booleans (Subtype of int)
# True is 1, False is 0.
truthy = True
falsy = False
print(f"True + 5 = {True + 5}")

# 5. Type Casting
age_str = "30"
age_int = int(age_str)
print(f"Converted {type(age_str)} to {type(age_int)}")

if __name__ == "__main__":
    # This block allows the script to be run as a standalone or as a module
    pass

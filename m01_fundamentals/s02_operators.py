"""
Module: Operators and Boolean Logic

Key Insights:
1. Short-circuiting logic: `and` and `or` return the actual objects, not necessarily a boolean.
2. Division: `/` always returns a float; `//` is floor division (integer division).
3. Walrus operator (`:=`): Assignment expression (Python 3.8+).
"""

# 1. Arithmetic Operators
a, b = 13, 5
print(f"Division (float): {a / b}")    # 2.6
print(f"Floor Division: {a // b}")    # 2
print(f"Modulo: {a % b}")            # 3
print(f"Power: {2 ** 10}")           # 1024

# 2. Logical Operators (Short-circuiting)
# 'or' returns the first TRUTHY value.
# 'and' returns the first FALSY value.
name = ""
fallback = "Default Name"
active_name = name or fallback
print(f"Active Name: {active_name}")  # "Default Name"

# 3. Bitwise Operators (Familiar territory for C engineers)
x = 0b1010  # 10
y = 0b1100  # 12
print(f"Bitwise AND: {bin(x & y)}")
print(f"Bitwise OR:  {bin(x | y)}")
print(f"Bitwise XOR: {bin(x ^ y)}")
print(f"Bitwise NOT: {bin(~x)}")
print(f"Bitwise Shift: {x << 2}")

# 4. Assignment Expressions (The Walrus Operator)
# Useful in loops and conditionals to avoid double calculation.
if (n := len(active_name)) > 10:
    print(f"Name is too long ({n} characters)")

# 5. Identity vs Equality
# is: Checks if two names point to the same OBJECT (id)
# ==: Checks if two objects have the same VALUE
list_a = [1, 2, 3]
list_b = [1, 2, 3]
print(f"list_a == list_b: {list_a == list_b}")  # True
print(f"list_a is list_b: {list_a is list_b}")  # False (different memory addresses)

if __name__ == "__main__":
    pass

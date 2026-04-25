"""
Module: Strings and Text Processing
Target: L5+ Systems Engineers

Key Insights:
1. Strings are IMMUTABLE sequences of Unicode code points.
2. UTF-8 is the default source encoding in Python 3.
3. f-strings are the modern, performant standard for formatting.
"""

# 1. Initialization and Multiline
raw_string = r"C:\Users\Name"  # Raw string (ignores escape chars)
multiline = """
This is a block string.
Useful for docstrings and SQL queries.
"""

# 2. Immutability and Slicing
s = "Python Programming"
# s[0] = 'p'  # TypeError: 'str' object does not support item assignment
print(f"First 6 chars: {s[:6]}")
print(f"Last 11 chars: {s[-11:]}")
print(f"Reversed: {s[::-1]}")

# 3. Modern Formatting (f-strings, 3.6+)
name = "Antigravity"
version = 3.12
print(f"Language: {name.upper()}, Version: {version:.2f}")

# Nested f-strings (3.12+)
precision = 3
print(f"Value: {22/7:.{precision}f}")

# 4. Encoding and Decoding
# Important for C engineers dealing with sockets or binary data.
data = "Hello 🚀"
encoded = data.encode("utf-8")  # str -> bytes
print(f"Encoded bytes: {encoded} (Length: {len(encoded)})")
decoded = encoded.decode("utf-8")  # bytes -> str
print(f"Decoded: {decoded}")

# 5. Methods
print("  strip me  ".strip())
print("csv,data,here".split(","))
print(" - ".join(["a", "b", "c"]))

if __name__ == "__main__":
    pass

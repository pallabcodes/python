"""
Module: Context Managers — The RAII Equivalent
Target: L5+ Systems Engineers

Key Insights for C++ Engineers:
1. 'with' statement provides a deterministic way to manage resources.
2. Equivalent to C++ RAII (Resource Acquisition Is Initialization).
3. Protocol: '__enter__' and '__exit__'.
"""

# 1. Class-based Context Manager
class DatabaseConnection:
    def __init__(self, name: str):
        self.name = name

    def __enter__(self):
        print(f"Opening connection to {self.name}")
        return self  # This is what 'as db' receives

    def __exit__(self, exc_type, exc_val, exc_tb):
        # exc_type, exc_val, exc_tb are non-None if an exception occurred.
        print(f"Closing connection to {self.name}")
        if exc_type:
            print(f"Caught exception: {exc_val}")
        # Return True to suppress the exception, False to propagate.
        return False

# Usage
with DatabaseConnection("prod") as db:
    print(f"Working with {db.name}")
    # raise ValueError("Something went wrong")

# 2. Function-based Context Manager (contextlib)
from contextlib import contextmanager

@contextmanager
def temp_file(filename: str):
    print(f"Creating {filename}")
    f = open(filename, "w")
    try:
        yield f
    finally:
        print(f"Deleting {filename}")
        f.close()
        # In a real scenario, you'd use os.remove(filename) here

with temp_file("test.txt") as f:
    f.write("Hello world")

# 3. Suppressing Exceptions (Utility)
from contextlib import suppress

with suppress(FileNotFoundError):
    import os
    os.remove("non_existent_file.txt")

if __name__ == "__main__":
    pass

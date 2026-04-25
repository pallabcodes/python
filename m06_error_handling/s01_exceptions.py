"""
Module: Exception Handling and Error Patterns
Target: L5+ Systems Engineers

Key Insights:
1. Python uses "EAFP" (Easier to Ask for Forgiveness than Permission).
2. Exception hierarchy: Always catch specific exceptions, never base 'Exception' if possible.
3. Exception Groups (3.11+): Handling multiple concurrent errors.
"""

# 1. Standard Try/Except/Else/Finally
def divide(a, b):
    try:
        result = a / b
    except ZeroDivisionError as e:
        print(f"Error: {e}")
        return None
    except TypeError as e:
        print(f"Error: {e}")
        raise  # Re-raising
    else:
        # Runs ONLY if no exception occurred
        print("Success!")
        return result
    finally:
        # ALWAYS runs (useful for cleanup)
        print("Cleanup complete")

# 2. Custom Exceptions
class DatabaseError(Exception):
    """Base class for database errors."""
    pass

class ConnectionTimeout(DatabaseError):
    def __init__(self, host, timeout):
        super().__init__(f"Timeout connecting to {host} after {timeout}s")
        self.host = host
        self.timeout = timeout

# 3. Exception Groups (Python 3.11+)
# Useful for asyncio TaskGroups or parallel processing.
# NOTE: Requires Python 3.11. Commented out for 3.10 compatibility.
"""
def aggregate_errors():
    raise ExceptionGroup(
        "Multiple failures",
        [
            ValueError("Invalid input"),
            TypeError("Wrong type"),
            DatabaseError("DB Down")
        ]
    )

try:
    aggregate_errors()
except* ValueError as eg:
    print(f"Handled ValueErrors: {eg.exceptions}")
"""

# 4. Assertions
# Used for internal sanity checks. Can be optimized away with -O.
def calculate_area(width, height):
    assert width > 0 and height > 0, "Dimensions must be positive"
    return width * height

if __name__ == "__main__":
    pass

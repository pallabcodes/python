"""
Module: Classes, Instances, and Scope

Key Insights:
1. 'self' is not a keyword (just a convention); it's the first argument passed by Python.
2. Class attributes vs Instance attributes.
3. Access modifiers: Python uses naming conventions (_protected, __private) rather than strict enforcement.
"""

class Database:
    # 1. Class Attribute (shared across all instances)
    # Similar to 'static' in C++ or Java.
    connection_count = 0

    def __init__(self, db_name: str):
        # 2. Instance Attributes
        self.name = db_name
        self._is_connected = False  # Convention: Protected (don't touch outside)
        self.__secret_key = "12345" # Convention: Private (Name mangling)
        
        Database.connection_count += 1

    def connect(self):
        self._is_connected = True
        print(f"Connected to {self.name}")

    def get_secret(self):
        # Accessing name-mangled attribute within the class
        return self.__secret_key

# Usage
db1 = Database("prod_db")
db2 = Database("test_db")

print(f"Total connections: {Database.connection_count}")
print(f"Total connections (via instance): {db1.connection_count}")

# 3. Accessing "Private" attributes
# Python mangles __secret_key to _Database__secret_key
try:
    print(db1.__secret_key)
except AttributeError:
    print("Direct access to __secret_key failed as expected.")

print(f"Mangled access: {db1._Database__secret_key}")

# 4. Modifying class attributes via instance (Pitfall!)
db1.connection_count = 10  # This creates an INSTANCE attribute 'connection_count' masking the class one!
print(f"db1.connection_count: {db1.connection_count}")
print(f"db2.connection_count: {db2.connection_count}")
print(f"Database.connection_count: {Database.connection_count}")

if __name__ == "__main__":
    pass

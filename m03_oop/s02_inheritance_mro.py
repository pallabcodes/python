"""
Module: Multiple Inheritance and Method Resolution Order (MRO)
Target: L5+ Systems Engineers

Key Insights for C++ Engineers:
1. Python supports Multiple Inheritance.
2. The 'diamond problem' is solved using C3 Linearization (MRO).
3. 'super()' doesn't just call the "parent"; it calls the NEXT class in the MRO.
"""

class Base:
    def greet(self):
        print("Hello from Base")

class A(Base):
    def greet(self):
        print("Hello from A")
        super().greet()

class B(Base):
    def greet(self):
        print("Hello from B")
        super().greet()

class C(A, B):
    def greet(self):
        print("Hello from C")
        super().greet()

# 1. Inspecting the MRO
# This is the order in which Python searches for attributes/methods.
print(f"MRO for C: {[cls.__name__ for cls in C.mro()]}")
# Expected: C -> A -> B -> Base -> object

# 2. Execution flow
print("\nInvoking C().greet():")
C().greet()
# Notice that C calls A, A calls B, and B calls Base.
# This happens because super() in A finds B in C's MRO.

# 3. Dynamic nature of super()
# super() is runtime-dependent. It depends on the MRO of the instance being used.

# 4. Mixing types (Mixins)
class LoggingMixin:
    def log(self, msg):
        print(f"[LOG] {msg}")

class SecureDatabase(Database, LoggingMixin):
    def connect(self):
        self.log(f"Attempting secure connection to {self.name}")
        super().connect()

if __name__ == "__main__":
    from m03_oop.s01_classes_and_instances import Database
    sdb = SecureDatabase("vault")
    sdb.connect()

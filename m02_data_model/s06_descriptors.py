"""
Module: The Descriptor Protocol

Key Insights:
1. Descriptors are objects that define __get__, __set__, or __delete__.
2. They are the engine behind @property, @classmethod, and @staticmethod.
3. Descriptors MUST be class attributes, not instance attributes.
"""

class VerboseAttribute:
    """A descriptor that logs every access."""
    def __init__(self, name: str):
        self.name = name

    def __get__(self, instance, owner):
        print(f"Reading '{self.name}' from {instance}")
        return instance.__dict__.get(self.name)

    def __set__(self, instance, value):
        print(f"Writing '{self.name}' to {instance}")
        instance.__dict__[self.name] = value

class User:
    # Descriptors are defined at the class level
    name = VerboseAttribute("name")
    age = VerboseAttribute("age")

    def __init__(self, name: str, age: int):
        self.name = name  # Triggers __set__
        self.age = age

u = User("Alice", 30)
print(f"User Name: {u.name}")  # Triggers __get__

# Why use this instead of @property?
# Descriptors allow you to REUSE logic across different attributes or classes.
# @property is just a convenient syntax for a one-off descriptor.

# Comparison with @property
class Product:
    def __init__(self, price):
        self._price = price

    @property
    def price(self):
        print("Reading price...")
        return self._price

    @price.setter
    def price(self, value):
        if value < 0: raise ValueError("Price cannot be negative")
        self._price = value

p = Product(100)
print(p.price)
p.price = 150

if __name__ == "__main__":
    pass

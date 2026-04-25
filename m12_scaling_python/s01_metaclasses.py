"""
Module: Metaclasses — The "Class of a Class"

Key Insights for Systems Engineers:
1. In Python, classes ARE objects. Their type is 'type' (the default metaclass).
2. Metaclasses allow you to intercept class creation (e.g., for validation, registration).
3. '__new__' on a metaclass is where the class is allocated; '__init__' is where it's initialized.
"""

# 1. Manual Class Creation (The 'type' constructor)
# type(name, bases, dict)
def greet(self):
    return f"Hello from {self.name}"

DynamicClass = type("DynamicClass", (object,), {"name": "Dynamic", "greet": greet})
obj = DynamicClass()
print(f"Dynamic instance: {obj.greet()}")

# 2. Custom Metaclass
# Use case: Automatically register all subclasses in a central registry.
class RegistryMeta(type):
    registry = {}

    def __new__(mcs, name, bases, attrs):
        # mcs: The metaclass itself
        # name: The name of the class being created
        # bases: Tuple of parent classes
        # attrs: Dict of class attributes
        
        cls = super().__new__(mcs, name, bases, attrs)
        if name != "BaseModel":  # Don't register the base itself
            mcs.registry[name] = cls
            print(f"Registered class: {name}")
        return cls

class BaseModel(metaclass=RegistryMeta):
    pass

class User(BaseModel):
    pass

class Product(BaseModel):
    pass

print(f"Current Registry: {list(RegistryMeta.registry.keys())}")

# 3. Practical Example: Validation
class Field:
    def __init__(self, type_):
        self.type_ = type_

class ValidatingMeta(type):
    def __new__(mcs, name, bases, attrs):
        # Ensure all fields match their declared type
        for key, value in attrs.items():
            if isinstance(value, Field):
                print(f"Found field '{key}' with type {value.type_}")
        return super().__new__(mcs, name, bases, attrs)

class Profile(metaclass=ValidatingMeta):
    username = Field(str)
    age = Field(int)

# Why use this?
# This is how SQLAlchemy, Pydantic, and Django models work. 
# They inspect the class attributes at creation time to build database schemas or validators.

if __name__ == "__main__":
    pass

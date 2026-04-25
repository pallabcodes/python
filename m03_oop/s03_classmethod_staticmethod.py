"""
Module: Method Types (Instance, Class, Static)

Key Insights:
1. Instance Method: Receives 'self' (the object).
2. Class Method: Receives 'cls' (the class). Used for factory methods.
3. Static Method: Receives nothing. Just a function namespaced within the class.
"""

class User:
    def __init__(self, name: str, access_level: str):
        self.name = name
        self.access_level = access_level

    # 1. Instance Method
    def get_details(self):
        return f"User {self.name} ({self.access_level})"

    # 2. Class Method (Common Factory Pattern)
    @classmethod
    def admin(cls, name: str):
        # cls is the class object (User)
        return cls(name, "admin")

    @classmethod
    def guest(cls, name: str):
        return cls(name, "guest")

    # 3. Static Method (Utility helper)
    @staticmethod
    def validate_name(name: str) -> bool:
        return len(name) > 2

# Usage
u1 = User.admin("Rolf")
u2 = User.guest("Bob")

print(u1.get_details())
print(f"Is 'R' valid? {User.validate_name('R')}")

# Why use @classmethod instead of just the class name in the factory?
# INHERITANCE. If we subclass User, the @classmethod will receive the SUBCLASS as 'cls'.
class PowerUser(User):
    pass

pu = PowerUser.admin("Anne")
print(f"Type of pu: {type(pu)}")  # <class '__main__.PowerUser'>

if __name__ == "__main__":
    pass

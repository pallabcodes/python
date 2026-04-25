"""
Module: Advanced Descriptors — Reusable Property Logic
Target: L7 Architects

Key Insights:
1. Descriptors allow you to encapsulate the "how" of attribute access.
2. LazyProperty: Compute a value once and cache it.
3. ValidatedField: Enforce rules across multiple classes without boilerplate.
"""

# 1. The LazyProperty (Cache-on-access)
# Very common in high-performance frameworks like Django or Flask.
class LazyProperty:
    def __init__(self, func):
        self.func = func
        self.__name__ = func.__name__
        self.__doc__ = func.__doc__

    def __get__(self, instance, owner):
        if instance is None:
            return self
        
        # Compute the value
        value = self.func(instance)
        
        # CACHE IT: Inject the value into the instance's __dict__
        # This masks the descriptor for subsequent accesses!
        instance.__dict__[self.__name__] = value
        return value

class HeavyResource:
    @LazyProperty
    def data(self):
        print("Computing heavy data (should only happen once)...")
        import time
        time.sleep(1)
        return [1, 2, 3, 4, 5]

resource = HeavyResource()
print(f"Access 1: {resource.data}")
print(f"Access 2: {resource.data}")  # Instant, no print statement

# 2. The Validated Field
class IntegerField:
    def __init__(self, min_value=None, max_value=None):
        self.min_value = min_value
        self.max_value = max_value
        self._name = None

    def __set_name__(self, owner, name):
        # Python 3.6+ hook to get the name of the attribute automatically
        self._name = name

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return instance.__dict__.get(self._name)

    def __set__(self, instance, value):
        if not isinstance(value, int):
            raise TypeError(f"'{self._name}' must be an integer")
        if self.min_value is not None and value < self.min_value:
            raise ValueError(f"'{self._name}' must be >= {self.min_value}")
        instance.__dict__[self._name] = value

class User:
    age = IntegerField(min_value=0, max_value=150)
    score = IntegerField(min_value=0)

u = User()
u.age = 30
# u.age = "thirty"  # Raises TypeError
# u.age = -1       # Raises ValueError

if __name__ == "__main__":
    pass

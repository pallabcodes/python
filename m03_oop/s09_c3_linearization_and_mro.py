"""
Module: MRO (C3 Linearization) and Metaprogramming Details
Target: L5/L7 Engineers

Understanding Python's method resolution order mathematically, and implementing
a native-level Descriptor to demonstrate how @property actually works at the CPython level.
"""

print("=== MRO and C3 Linearization ===")
# C3 Linearization Example
class O: pass
class A(O): pass
class B(O): pass
class C(O): pass
class D(O): pass
class E(O): pass
class K1(A, B, C): pass
class K2(D, B, E): pass
class K3(D, A): pass
class Z(K1, K2, K3): pass

print(f"Z MRO using C3 Linearization: {[cls.__name__ for cls in Z.__mro__]}")


print("\n=== Descriptor Protocol Internals ===")
class AdvancedProperty:
    """A pure Python implementation of the property() builtin."""
    def __init__(self, fget=None, fset=None):
        self.fget = fget
        self.fset = fset

    def __get__(self, obj, objtype=None):
        if obj is None: 
            return self
        if self.fget is None: 
            raise AttributeError("unreadable attribute")
        return self.fget(obj)

    def __set__(self, obj, value):
        if self.fset is None: 
            raise AttributeError("can't set attribute")
        self.fset(obj, value)
        
    def setter(self, fset):
        return type(self)(self.fget, fset)

class MyClass:
    def __init__(self):
        self._x = None
        
    @AdvancedProperty
    def x(self):
        return self._x
        
    @x.setter
    def x(self, value):
        print(f"Setting x to {value}")
        self._x = value

def demo_descriptor():
    obj = MyClass()
    obj.x = 42
    print(f"Retrieved x: {obj.x}")

if __name__ == "__main__":
    demo_descriptor()

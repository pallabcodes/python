"""
Module: CPython Memory Internals & Data Layout
Target: L5/L7 Engineers

Deep dive into CPython's memory management, small object allocators (pymalloc),
and reference counting mechanics.
"""
import sys
import gc

def explore_memory_layout():
    print("=== Small Integer Caching ===")
    # Small integers (-5 to 256) are cached globally in CPython
    a = 256
    b = 256
    print(f"256 is same object: {a is b}") # True
    c = 257
    d = 257
    print(f"257 is same object: {c is d} (depends on compile unit, generally False in REPL)") 

    print("\n=== Object Overheads ===")
    # sys.getsizeof shows the exact PyObject footprint.
    # Empty list is ~56 bytes (on 64-bit). 
    print(f"Size of empty list: {sys.getsizeof([])} bytes")
    print(f"Size of empty dict: {sys.getsizeof({})} bytes")
    # Why? PyVarObject struct + PyObject** for pointers.
    
    print("\n=== String Interning ===")
    # String Interning (useful for dictionary keys lookup optimizations)
    s1 = sys.intern("some_very_long_string_with_underscores")
    s2 = sys.intern("some_very_long_string_with_underscores")
    print(f"Interned strings identity match: {s1 is s2}") 
    print("Benefit: O(1) pointer comparison vs O(N) string comparison")

if __name__ == "__main__":
    explore_memory_layout()

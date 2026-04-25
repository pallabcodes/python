"""
Module: Advanced Memory Edge Cases & Fragmentation

Topics:
1. Reference Cycles with __del__: Why your objects might never be collected.
2. Memory Fragmentation: The trade-off between pymalloc and jemalloc.
3. Zero-copy with mmap: Handling large files without saturating RAM.
"""
import gc
import mmap
import os

class LeakyObject:
    def __init__(self, name):
        self.name = name
        self.other = None
        
    def __del__(self):
        # DANGER: In older Python versions, reference cycles with __del__ 
        # were uncollectable. In 3.4+, they are collectable but still risky.
        pass

def cycle_demo():
    print("=== Reference Cycles & GC ===")
    a = LeakyObject("A")
    b = LeakyObject("B")
    a.other = b
    b.other = a
    
    del a
    del b
    
    # Even though we deleted 'a' and 'b', they stay in memory because of the cycle.
    # The GC must run to break the cycle.
    collected = gc.collect()
    print(f"GC broken cycles and collected {collected} objects.")

def mmap_demo():
    print("\n=== Zero-copy Memory Mapping (mmap) ===")
    # Ideal for L7 engineers handling TB-scale data on Pinterest/Uber scale.
    filename = "test_mmap.bin"
    with open(filename, "wb") as f:
        f.write(b"Hello World" * 1024)
        
    with open(filename, "r+b") as f:
        # Map the file into memory. No read() call needed.
        mm = mmap.mmap(f.fileno(), 0)
        print(f"Read from mmap without copying to RAM: {mm[:11]}")
        mm.close()
    
    os.remove(filename)

if __name__ == "__main__":
    cycle_demo()
    mmap_demo()
    
    print("\n--- Engineering Note: Fragmentation ---")
    print("Python's 'pymalloc' is optimized for objects < 512 bytes.")
    print("For large-scale services (Google/Uber), replacing the system allocator")
    print("with 'jemalloc' or 'mimalloc' often reduces fragmentation by 10-20%.")

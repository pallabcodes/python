"""
Module: Buffer Protocol and Zero-Copy Interactions

How to bypass the serialization overhead when communicating with native extensions
(C/C++/Rust) or reading I/O directly into pre-allocated memory using Python's Buffer Protocol.
"""
import ctypes
import struct

def zero_copy_demo():
    print("=== Zero Copy with MemoryView ===")
    # 1. Pre-allocate raw bytes
    data = bytearray(1024 * 1024) # 1 MB buffer
    
    # 2. Create a memoryview (Zero-copy wrapper implementing Buffer Protocol)
    view = memoryview(data)
    
    # 3. Cast the view to a different type (e.g., unsigned ints) without copying
    int_view = view.cast('I')
    
    # Mutate the view, mutates the underlying bytearray
    int_view[0] = 42
    
    print(f"First 4 bytes of underlying data after cast mutation: {list(data[:4])}")
    print("Use Case: socket.recv_into(view) allows reading directly into memory.")
    
    print("\n=== Native C-Interop without Copying ===")
    # 4. ctypes interaction: Pass the buffer directly to a hypothetical C function
    c_buffer = (ctypes.c_char * len(data)).from_buffer(data)
    print(f"C-compatible buffer created without copying memory. Size: {ctypes.sizeof(c_buffer)} bytes")

if __name__ == "__main__":
    zero_copy_demo()

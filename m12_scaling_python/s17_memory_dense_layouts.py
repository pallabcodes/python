"""
Module: Memory-Dense Data Layouts
Target: L7 Systems Engineers (Google standard for large datasets)

Key Techniques:
1. array.array: Compact typed arrays (No PyObject overhead).
2. ctypes.Structure: C-style structs for memory-perfect alignment.
3. slots: Reducing class memory footprint by eliminating __dict__.
"""

import array
import sys
import ctypes
import logging

logger = logging.getLogger(__name__)

# 1. The 'Slots' Pattern
# Reduces memory for instances by 40-60%.
class SlottedUser:
    __slots__ = ("id", "score") # No __dict__ created!
    def __init__(self, id, score):
        self.id = id
        self.score = score

# 2. The 'Array' Pattern
# Stores millions of integers in a contiguous block of memory.
def array_memory_benchmark():
    count = 1_000_000
    
    # Standard List of integers
    py_list = list(range(count))
    list_size = sys.getsizeof(py_list) + sum(sys.getsizeof(i) for i in py_list)
    
    # Compact Typed Array (int32)
    compact_array = array.array('i', range(count))
    array_size = sys.getsizeof(compact_array) + compact_array.buffer_info()[1] * compact_array.itemsize
    
    logger.info(f"List Size: {list_size / 1024 / 1024:.2f} MB")
    logger.info(f"Compact Array Size: {array_size / 1024 / 1024:.2f} MB")
    logger.info(f"Memory Savings: {((list_size - array_size) / list_size) * 100:.1f}%")

# 3. The 'C-Struct' Pattern
# Perfect for memory-mapped files or wire protocols.
class NetworkPacket(ctypes.Structure):
    _fields_ = [
        ("version", ctypes.c_uint8),
        ("payload_type", ctypes.c_uint8),
        ("payload_size", ctypes.c_uint32),
        ("timestamp", ctypes.c_uint64)
    ]

def ctypes_demo():
    packet = NetworkPacket(1, 5, 1024, 1629876543)
    logger.info(f"CTypes Packet Size: {ctypes.sizeof(packet)} bytes (Fixed size!)")
    # You can access raw buffer bytes directly
    buffer = bytes(packet)
    logger.info(f"Raw binary: {buffer.hex()}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    array_memory_benchmark()
    ctypes_demo()

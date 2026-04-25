"""
Module: Bit Manipulation and Wire Protocols
Target: L7 Systems Engineers (Discord/Google Wire Standard)

Key Techniques:
1. Struct: Packing data into compact C-style binary buffers.
2. Bitmasks: Using a single integer to store 64+ boolean flags (Discord Permissions).
3. Memoryview: Zero-copy slicing of large binary buffers.
4. Bitwise Ops: AND/OR/XOR for high-performance state management.
"""

import struct
import io
import logging

logger = logging.getLogger(__name__)

# 1. The Discord Pattern: Bitmasks for Permissions
# Instead of a dict of 30 booleans, we use one 64-bit integer.
class Permissions:
    READ_MESSAGE    = 1 << 0  # 0001 (1)
    SEND_MESSAGE    = 1 << 1  # 0010 (2)
    MANAGE_MESSAGES = 1 << 2  # 0100 (4)
    ADMINISTRATOR   = 1 << 3  # 1000 (8)

    @staticmethod
    def has_permission(user_mask: int, perm: int) -> bool:
        return (user_mask & perm) == perm

# 2. The Wire Pattern: Struct Packing
# Google-grade binary protocols (like a mini-protobuf)
# Format: < (Little Endian), I (Unsigned Int, 4 bytes), H (Unsigned Short, 2 bytes)
def pack_packet(user_id: int, status_code: int):
    # Pack into 6 bytes total
    return struct.pack("<IH", user_id, status_code)

def unpack_packet(binary_data: bytes):
    return struct.unpack("<IH", binary_data)

# 3. High-Performance Buffers: Memoryview
# Essential for large stream processing without allocating new strings/bytes.
def process_large_buffer(data: bytes):
    view = memoryview(data)
    # Slice without copying memory!
    header = view[:4]
    payload = view[4:]
    logger.info(f"Processing payload of size: {len(payload)}")
    return header, payload

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Bitmask Demo
    my_perms = Permissions.READ_MESSAGE | Permissions.SEND_MESSAGE
    print(f"Can Read: {Permissions.has_permission(my_perms, Permissions.READ_MESSAGE)}")
    print(f"Can Manage: {Permissions.has_permission(my_perms, Permissions.MANAGE_MESSAGES)}")

    # Wire Demo
    packet = pack_packet(12345, 200)
    print(f"Binary Packet (6 bytes): {packet.hex()}")
    uid, status = unpack_packet(packet)
    print(f"Unpacked: UID={uid}, Status={status}")

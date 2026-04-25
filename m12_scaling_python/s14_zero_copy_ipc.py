"""
Module: Zero-Copy IPC (Inter-Process Communication)
Target: L7 Systems Engineers (Core Python Standard)

Key Techniques:
1. SharedMemory: Allocating a block of RAM accessible by multiple processes.
2. mmap: Memory-mapping files for high-speed disk IO.
3. Zero-Copy: Accessing data without pickling or memory allocation.
"""

import multiprocessing
from multiprocessing import shared_memory
import mmap
import os
import time
import logging

logger = logging.getLogger(__name__)

def shared_memory_demo():
    """
    Demonstrates Python 3.8+ SharedMemory.
    Process A creates it, Process B reads/modifies it. Zero copying involved.
    """
    # 1. Create a shared memory block (1 KB)
    shm_a = shared_memory.SharedMemory(create=True, size=1024, name="google_scale_shm")
    
    # Use the buffer like a bytearray
    buffer = shm_a.buf
    buffer[:11] = b"HELLO GOOGLE"
    
    def process_b():
        # Connect to existing shared memory
        existing_shm = shared_memory.SharedMemory(name="google_scale_shm")
        logger.info(f"Process B read: {bytes(existing_shm.buf[:11]).decode()}")
        # Modify it
        existing_shm.buf[:11] = b"HELLO ELITE "
        existing_shm.close()

    p = multiprocessing.Process(target=process_b)
    p.start()
    p.join()

    logger.info(f"Process A final: {bytes(shm_a.buf[:11]).decode()}")
    
    shm_a.close()
    shm_a.unlink() # Cleanup

def mmap_demo():
    """
    Demonstrates mmap for fast file access.
    Maps a file to memory so it can be accessed like an array.
    """
    filename = "large_data.bin"
    # Create a 1MB file
    with open(filename, "wb") as f:
        f.seek(1024 * 1024 - 1)
        f.write(b"\0")

    with open(filename, "r+b") as f:
        # Memory-map the file, size 0 means whole file
        with mmap.mmap(f.fileno(), 0) as mm:
            logger.info(f"mmap size: {len(mm)} bytes")
            # Write to the file via memory
            mm[0:11] = b"ELITE SCALE"
            mm.flush() # Ensure it's written to disk
            
            # Read back
            mm.seek(0)
            logger.info(f"mmap read: {mm.read(11).decode()}")

    os.remove(filename)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    shared_memory_demo()
    mmap_demo()

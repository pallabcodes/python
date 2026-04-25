"""
Module: C Interoperability with ctypes

Key Insights:
1. 'ctypes' is a foreign function library for Python.
2. It provides C compatible data types and allows calling functions in DLLs or shared libraries.
3. No compilation required on the Python side.
"""

import ctypes
from ctypes.util import find_library

# 1. Loading the standard C library
libc_name = find_library('c')
libc = ctypes.CDLL(libc_name)

# 2. Basic function call (no args)
# Equivalent to time_t t = time(NULL);
current_time = libc.time(None)
print(f"C time(): {current_time}")

# 3. Handling arguments and return types
# Equivalent to int abs(int j);
libc.abs.argtypes = [ctypes.c_int]
libc.abs.restype = ctypes.c_int

print(f"C abs(-42): {libc.abs(-42)}")

# 4. Working with Strings (char*)
# Equivalent to int printf(const char *format, ...);
libc.printf(b"Hello from C's printf! %d\n", 123)

# 5. Passing by reference (Pointers)
# Equivalent to:
# struct tm *localtime(const time_t *timer);
class TM(ctypes.Structure):
    _fields_ = [
        ("tm_sec", ctypes.c_int),
        ("tm_min", ctypes.c_int),
        ("tm_hour", ctypes.c_int),
        ("tm_mday", ctypes.c_int),
        ("tm_mon", ctypes.c_int),
        ("tm_year", ctypes.c_int),
        ("tm_wday", ctypes.c_int),
        ("tm_yday", ctypes.c_int),
        ("tm_isdst", ctypes.c_int),
    ]

t = ctypes.c_long(current_time)
libc.localtime.restype = ctypes.POINTER(TM)
tm_ptr = libc.localtime(ctypes.byref(t))

print(f"Year from C struct: {tm_ptr.contents.tm_year + 1900}")

if __name__ == "__main__":
    pass

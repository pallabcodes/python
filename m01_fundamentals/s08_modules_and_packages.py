"""
Module: The Python Import System

Key Insights:
1. 'import' is an executable statement, not a pre-processor directive.
2. sys.path: Where Python looks for modules.
3. Packages are directories containing an '__init__.py' (though optional since 3.3, it's still best practice).
"""

import sys
import os

# 1. Understanding sys.path
# This is equivalent to C++'s include path or Java's classpath.
# print(f"Search paths: {sys.path}")

# 2. Package Structure
# my_package/
#   ├── __init__.py    # Run when the package is imported
#   ├── module_a.py
#   └── sub_package/
#       ├── __init__.py
#       └── module_b.py

# 3. Absolute vs Relative Imports
# Absolute: from my_package.module_a import some_func
# Relative: from .module_a import some_func (Only works within a package)

# 4. The __name__ == "__main__" Guard
# This is the "main function" equivalent in Python.
# It prevents code from running when the file is imported as a module.
if __name__ == "__main__":
    print("Script is running directly.")
else:
    print(f"Module {__name__} was imported.")

# 5. Circular Imports
# A common issue for C++ developers used to forward declarations.
# Python evaluates imports at runtime, so circular imports will fail
# unless handled (e.g., by moving the import inside a function).

# 6. Reloading Modules
# Unlike C++, you can reload a module at runtime using importlib.reload().
# Useful for hot-reloading in long-running services.
import importlib
# importlib.reload(os) 

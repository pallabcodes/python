"""
Module: Native Extension Strategy — The Python Glue Code Architecture
Target: L7 Systems Engineers (The Google Blueprint)

Key Insights:
1. Python is the "Glue"; C++/Rust/C is the "Engine".
2. PyBind11: The industry standard for C++/Python integration.
3. GIL Release: The most critical part of native extensions for parallelism.
"""

# This file is a documentation-centric architecture guide.

"""
### The Strategy: "Write in Python, Optimize in C++"

#### 1. PyBind11 (The Google/Standard Choice)
- **Why**: Seamless integration with C++11 and later. Handles type conversion automatically.
- **Google Connection**: Used in TensorFlow, PyTorch, and thousands of internal Google services.
- **Example Pattern**:
    ```cpp
    #include <pybind11/pybind11.h>
    int add(int i, int j) { return i + j; }
    PYBIND11_MODULE(example, m) {
        m.def("add", &add, "A function that adds two numbers");
    }
    ```

#### 2. Releasing the GIL
In a native extension, you can allow TRUE parallelism by releasing the Global Interpreter Lock:
```cpp
// Inside a C++ function called from Python
{
    pybind11::gil_scoped_release release;
    // Perform heavy CPU/IO work here. 
    // Other Python threads can now run concurrently!
}
```

#### 3. Cython
- **Why**: Good for migrating existing Python code to C-level speeds without writing pure C.
- **Discord Connection**: Discord used Cython extensively in their early Go-migration phase.

#### 4. CFFI / ctypes
- **Why**: Good for calling legacy C libraries where you don't want to write a wrapper.

### Architectural Decision Matrix

| Requirement | Recommendation |
| :--- | :--- |
| High-performance C++ integration | **PyBind11** |
| Accelerating existing Python loops | **Cython** |
| Modern, safe systems integration | **PyO3 (Rust)** |
| Simple call to a shared .so / .dll | **ctypes** |

"""

if __name__ == "__main__":
    print("This module provides an architectural overview of Native Extensions.")
    print("Refer to the docstrings for the decision matrix.")

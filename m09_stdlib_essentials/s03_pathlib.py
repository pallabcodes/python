"""
Module: Pathlib — Modern Object-Oriented Filesystem I/O
Target: L5+ Systems Engineers

Key Insights for C++ Engineers:
1. 'pathlib' replaces 'os.path' and 'glob'.
2. Paths are objects, not strings.
3. Overloads '/' operator for path joining (similar to C++17 std::filesystem).
"""

from pathlib import Path

# 1. Path Manipulation
base_dir = Path(".")
config_file = base_dir / "config" / "settings.json"
print(f"Absolute path: {config_file.absolute()}")
print(f"File suffix: {config_file.suffix}")
print(f"Parent directory: {config_file.parent}")

# 2. Filesystem Operations
if not base_dir.exists():
    base_dir.mkdir(parents=True)

# 3. Reading/Writing (Shortcuts)
data_file = Path("data.txt")
data_file.write_text("Hello from Pathlib!")
content = data_file.read_text()
print(f"Content: {content}")

# 4. Directory Traversal
print("\nDirectory contents:")
for path in base_dir.iterdir():
    type_str = "DIR" if path.is_dir() else "FILE"
    print(f"[{type_str}] {path.name}")

# 5. Pattern Matching (Globbing)
print("\nPython files in root:")
for py_file in base_dir.glob("*.py"):
    print(py_file)

# Cleanup
if data_file.exists():
    data_file.unlink()

if __name__ == "__main__":
    pass

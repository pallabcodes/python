"""
Module: Advanced Collections (collections module)

Key Insights for C++ Engineers:
1. deque       -> std::deque (Double-ended queue, O(1) start/end operations)
2. namedtuple  -> Lightweight struct-like objects
3. Counter     -> std::unordered_map<T, int> specialized for counting
4. defaultdict -> Dict that provides a default value for missing keys
"""

from collections import deque, namedtuple, Counter, defaultdict

# 1. Deque (Thread-safe, double-ended)
# Efficiently add/remove from BOTH ends.
q = deque(["a", "b", "c"])
q.append("d")
q.appendleft("z")
q.pop()
q.popleft()
print(f"Deque: {q}")

# 2. NamedTuple (Immutable records)
# Memory-efficient and more readable than regular tuples.
Point = namedtuple("Point", ["x", "y"])
p = Point(10, 20)
print(f"Point: {p.x}, {p.y} (as tuple: {p[0]})")

# 3. Counter (Histogram)
counts = Counter("abracadabra")
print(f"Most common: {counts.most_common(2)}")
print(f"Count of 'a': {counts['a']}")

# 4. DefaultDict (Automatic initialization)
# No more KeyError when appending to a non-existent list in a dict.
user_groups = defaultdict(list)
user_groups["admin"].append("Jose")
user_groups["guest"].append("Rolf")
print(f"Groups: {dict(user_groups)}")

# 5. ChainMap (Combining dicts without copying)
from collections import ChainMap
defaults = {"theme": "dark", "level": 1}
user_settings = {"level": 2}
settings = ChainMap(user_settings, defaults)
print(f"Effective Level: {settings['level']}")  # 2 (found in first dict)
print(f"Effective Theme: {settings['theme']}") # dark (found in second dict)

if __name__ == "__main__":
    pass

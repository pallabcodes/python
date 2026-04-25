"""
Module: Core Collections (Built-in Data Structures)

Mental Mapping for C++ Engineers:
- list  -> std::vector<PyObject*> (Dynamic array of pointers)
- tuple -> Immutable array (Fixed size)
- dict  -> std::unordered_map (Hash map)
- set   -> std::unordered_set (Hash set)
"""

# 1. Lists (Dynamic Arrays)
# Highly optimized for appending. O(1) amortized append, O(n) insert/delete.
friends = ["Rolf", "Bob", "Anne"]
friends.append("Jen")
friends.insert(1, "Charlie")  # Costly!
print(f"List length: {len(friends)}")

# 2. Tuples (Immutable Arrays)
# More memory efficient than lists. Used for fixed records.
point = (10, 20)
# point[0] = 15  # TypeError
print(f"Type: {type(point)}")

# Destructuring (Unpacking)
x, y = point
print(f"Unpacked: x={x}, y={y}")

# 3. Dictionaries (Hash Maps)
# Since Python 3.7, dicts maintain insertion order as an implementation detail (guaranteed in 3.7+).
user = {
    "id": 1,
    "name": "Jose",
    "access_level": "admin"
}
print(f"User Name: {user.get('name', 'Unknown')}")

# Iterating over dicts
for key, value in user.items():
    print(f"{key} => {value}")

# 4. Sets (Unique Hash Collections)
# O(1) membership testing.
art_friends = {"Rolf", "Anne", "Jen"}
science_friends = {"Jen", "Charlie"}

# Set operations (the real power)
print(f"Both: {art_friends & science_friends}")  # Intersection
print(f"Either: {art_friends | science_friends}") # Union
print(f"Only Art: {art_friends - science_friends}") # Difference

# 5. Frozenset (Immutable Set)
# Can be used as a dictionary key (regular sets cannot as they aren't hashable).
fs = frozenset([1, 2, 3])

if __name__ == "__main__":
    pass

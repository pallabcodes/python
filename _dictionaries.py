friend_ages = {"Rolf": 24, "Adam": 30, "Anne": 27}

print(friend_ages["Rolf"])  # 24
# friend_ages["Bob"]  ERROR

# -- Adding a new key to the dictionary --

friend_ages["Bob"] = 20
print(friend_ages)  # {'Rolf': 24, 'Adam': 30, 'Anne': 27, 'Bob': 20}

# -- Modifying existing keys --

friend_ages["Rolf"] = 25

print(friend_ages)  # {'Rolf': 25, 'Adam': 30, 'Anne': 27, 'Bob': 20}

# -- Lists of dictionaries --
# Imagine you have a program that stores information about your friends.
# This is the perfect place to use a list of dictionaries.
# That way you can store multiple pieces of data about each friend, all in a single variable.

friends = [
    {"name": "Rolf Smith", "age": 24},
    {"name": "Adam Wool", "age": 30},
    {"name": "Anne Pun", "age": 27},
]

# You can turn a list of lists / matrix or tuples into a dictionary:

friends = [("Rolf", 24), ("Adam", 30), ("Anne", 27), ("Mane", 34)]
friend_ages = dict(friends)
print(friend_ages["Mane"])


# iterating over the friend_ages

friend_ages = {"Rolf": 25, "Anne": 37, "Charlie": 31, "Bob": 22}

for name in friend_ages:
    print(f"friend_name:{name}")


for age in friend_ages.values():
    print(age)


for name, age in friend_ages.items():
    print(f"{name} is {age} years old.")


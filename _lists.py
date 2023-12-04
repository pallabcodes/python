friend1 = "Rolf"
friend2 = "Bob"
friend3 = "Anne"

friends = ["Rolf", "Bob", "Anne"]

print(friends[0])  # This is called a subscript
print(friends[1])

# You can put anything you like inside a list, but it's almost always a good idea to keep it homogeneous.

friends = ["Rolf", 2, "Anne"]  # Generally a bad idea

# -- Length of a list --

friends = ["Rolf", "Anne"]
print(len(friends))  # 2

# -- Lists inside lists --
# As mentioned earlier, you can put anything inside a list—and that includes other lists.

friends = [["Rolf", 24], ["Bob", 30], ["Anne", 27]]
print(friends[0][1])  # 24
print(friends[1][0])  # Bob

# -- Long lists --

friends = [
    ["Rolf", 24],
    ["Bob", 30],
    ["Anne", 27],
    ["Charlie", 37],
    ["Jen", 25],
    ["Adam", 29],
]

# -- Adding to a list --

friends = ["Rolf", "Bob", "Anne"]
friends.append("Jen")

print(friends)  # ["Rolf", "Bob", "Anne", "Jen"]

# -- Removing from a list --

friends.remove("Bob")

print(friends)  # ["Rolf", "Anne", "Jen"]

# Remember if you have a list of lists, for example, you still need the entire thing you want to remove:

friends = [["Rolf", 24], ["Bob", 30], ["Anne", 27]]

friends.remove(["Bob", 30])


# Imagine you've got all your friends in a list, and you want to print it out.
friends = ["Rolf", "Anne", "Charlie"]
print(f"My friends are {friends}.")

# Not the prettiest, so instead you can join your friends using a ",":
friends = ["Rolf", "Anne", "Charlie"]
comma_separated = ", ".join(friends)
print(f"My friends are {comma_separated}.")

# Want the last one to say ", and" ?
# You'll have to wait until we cover list slicing in the next section!


# slicing from the lists or tuple or strings

friends = ["Rolf", "Charlie", "Anna", "Bob", "Jen"]

# in case of slice when using "negative" then last element is -1

print(friends[2:4])
print(friends[2:])
print(friends[:4])
print(friends[:])
print(friends[-3:])
print(friends[:-2])
print(friends[-3:-1])


# list_comprehensions

numbers = [0, 1, 2, 3, 4]
doubled_numbers = []

for num in numbers:
    doubled_numbers.append(num * 2)

print(doubled_numbers)

# -- List comprehension --

numbers = [0, 1, 2, 3, 4]  # alernatively, list(range(5)) is better rather than [0, 1, 2, 3, 4]
doubled_numbers = [num * 2 for num in numbers]
# [num * 2 for num in range(5)] would be even better.

print(doubled_numbers)

# -- You can add anything to the new list --

friend_ages = [22, 31, 35, 37]
age_strings = [f"My friend is {age} years old." for age in friend_ages]

print(age_strings)


# -- This includes things like --
names = ["Rolf", "Bob", "Jen"]
lower = [name.lower() for name in names]

# That is particularly useful for working with user input.
# By turning everything to lowercase, it's less likely we'll miss a match.

friend = input("Enter your friend name: ")
friends = ["Rolf", "Bob", "Jen", "Charlie", "Anne"]
friends_lower = [name.lower() for name in friends]

if friend.lower() in friends_lower:
    print(f"I know {friend}!")


# comprehensions_with_conditionals

ages = [22, 35, 27, 21, 20]
odds = [n for n in ages if n % 2 == 1]

# -- with strings --

friends = ["Rolf", "ruth", "charlie", "Jen"]
guests = ["jose", "Bob", "Rolf", "Charlie", "michael"]

friends_lower = [f.lower() for f in friends]

present_friends = [
    name.capitalize() for name in guests if name.lower() in friends_lower
]

# -- nested list comprehensions --
# Don't do this, because it's almost completely unreadable.
# Splitting things out into variables is better.

friends = ["Rolf", "ruth", "charlie", "Jen"]
guests = ["jose", "Bob", "Rolf", "Charlie", "michael"]

present_friends = [
    name.capitalize() for name in guests if name.lower() in [f.lower() for f in friends] # unreadable
]


# set_dictionary_comprehensions

friends = ["Rolf", "ruth", "charlie", "Jen"]
guests = ["jose", "Bob", "Rolf", "Charlie", "michael"]

friends_lower = {n.lower() for n in friends}
guests_lower = {n.lower() for n in guests}

present_friends = friends_lower.intersection(guests_lower)
present_friends = {name.capitalize() for name in friends_lower & guests_lower}

print(present_friends)

# Transforming data for easier consumption and processing is a very common task.
# Working with homogeneous data is really nice, but often you can't (e.g. when working with user input!).

# -- Dictionary comprehension --
# Works just like set comprehension, but you need to do key-value pairs.

friends = ["Rolf", "Bob", "Jen", "Anne"]
time_since_seen = [3, 7, 15, 11]

long_timers = {
    friends[i]: time_since_seen[i]
    for i in range(len(friends)) # i = 0 (inclusion) and range(len(friends = 4)) exclusion
    if time_since_seen[i] > 5
}

print(long_timers)

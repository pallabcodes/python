friends = ["Rolf", "John", "Anna"]

for counter, friend in enumerate(friends, start=1):
	print(f"here{counter, friend}")

# prints

# 1 Rolf
# 2 John
# 3 Anna


friends = ["Rolf", "John", "Anna"]
print(f"friends: {friends}")

# This is how to take a List and turn it into a 2d Array  / Matrix -> to access list(enumerate(friends)[0][0]) = "Rolf"
print(list(enumerate(friends)))  # [(0, 'Rolf'), (1, 'John'), (2, 'Anna')]

matrix = list(enumerate(friends))
print(f"matrix: {matrix} => {matrix[1][0]}")

print(dict(enumerate(friends)))  # {0: 'Rolf', 1: 'John', 2: 'Anna'} : This turned into a dictionary

"""
Module: Control Flow and Pattern Matching
Target: L5+ Systems Engineers

Key Insights:
1. 'match/case' (Structural Pattern Matching) is Python 3.10's answer to Rust/C++ variant switching.
2. 'for...else' runs if the loop completes WITHOUT a 'break'.
3. Iterables vs Iterators (Brief intro).
"""

# 1. Conditionals
status_code = 404
if 200 <= status_code < 300:
    print("Success")
elif 400 <= status_code < 500:
    print("Client Error")
else:
    print("Unknown status")

# 2. Structural Pattern Matching (Python 3.10+)
# Much more powerful than a simple switch.
command = "split filename.txt"
match command.split():
    case ["quit"]:
        print("Quitting...")
    case ["load", filename]:
        print(f"Loading {filename}...")
    case ["split", filename]:
        print(f"Splitting {filename}...")
    case _:
        print("Command not recognized")

# 3. Loops and the 'else' clause
# The 'else' block executes if the loop finishes naturally.
# Common use case: searching for an item and handling "not found".
primes = [2, 3, 5, 7, 11]
target = 13

for n in primes:
    if n == target:
        print(f"Found {target}!")
        break
else:
    # This runs ONLY if 'break' was not hit.
    print(f"Could not find {target} in the list.")

# 4. Enumeration (Getting index and value)
friends = ["Rolf", "Bob", "Anne"]
for index, friend in enumerate(friends, start=1):
    print(f"#{index}: {friend}")

# 5. Zipping (Parallel Iteration)
ages = [24, 30, 27]
for name, age in zip(friends, ages):
    print(f"{name} is {age}")

if __name__ == "__main__":
    pass

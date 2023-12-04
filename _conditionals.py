# if else

friend = "Rolf"
user_name = input("Enter your name: ")

if user_name == friend:
    print("Hello, friend!")
else:
    print("Hello, stranger!")


# On loops, you can add an `else` clause. This only runs if the loop does not encounter a `break` or an error.
# That means, if the loop completes successfully, the `else` part will run.

cars = ["ok", "ok", "ok", "faulty", "ok", "ok"]

for status in cars:
    if status == "faulty":
        print(f"This car is {status}.")
        break
    else:
        print("All cars built successfully. No faulty cars!")

# -- Checking whether the if statement will run --

print(bool(user_name == friend))  # if this is True, the if statement will run

# -- Using the `in` keyword --

friends = ["Rolf", "Bob", "Anne"]
family = ["Jen", "Charlie"]

user_name = input("Enter your name: ")

if user_name in friends:
    print("Hello, friend!")
elif user_name in family:
    print("Hello, family!")
else:
    print("I don't know you.")

    # while loop

    is_learning = True

# while is_learning:
# print("You're learning!") # This will be infinite loop


# -- Ending a loop with user input --

user_input = input("Do you wish to run the program? (yes/no): ")

while user_input == "yes":
    print("We're running!")
    user_input = input("Do you wish to run the program? (yes/no): ")

print("We stopped running.")


# -- break --
# Exits out of the loop, so that no more iterations occur.

cars = ["ok", "ok", "ok", "faulty", "ok", "ok"]

for status in cars:
    if status == "faulty":
        print("Stopping the production line!")
        break

    print(f"This car is {status}.")

# -- continue --
# Terminates the current iteration and moves onto the next one.

cars = ["ok", "ok", "ok", "faulty", "ok", "ok"]

for status in cars:
    if status == "faulty":
        print("Found faulty car, skipping...")
        continue

    print(f"This car is {status}.")
    print("Shipping new car to customer!")


# for loop

friends = ["Rolf", "Jen", "Anne"]

for friend in friends:
    print(friend)

elements = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

for index in elements:
    print(index)

for index in range(10):
    print(index)

for index in range(5, 10):
    print(index)

for index in range(2, 20, 3):
    print(index)


# -- Using each value while you iterate --

students = [
    {"name": "Rolf", "grade": 90},
    {"name": "Bob", "grade": 78},
    {"name": "Jen", "grade": 100},
    {"name": "Anne", "grade": 80},
]


for student in students:  # student is a variable used for iteration
    name = student["name"]
    grade = student["grade"]
    print(f"{name} has a grade of {grade}.")


# prime numbers

for n in range(2, 10):
    for x in range(2, n):
        if n % x == 0:  # if n is divisible by x, it means it's not a prime number.
            print(f"{n} equals {x} * {n//x}")
            break
    else:  # if n was not divisible by any x, it means it is a prime number.
        print(f"{n} is a prime number.")

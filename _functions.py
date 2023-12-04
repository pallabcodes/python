def greet():
    name = input("Enter your name: ")
    print(f"Hello, {name}!")


# Running this does nothing, because although we have defined a function, we haven't executed it. so invoke it as below 

greet()


# Imagine you've got some code that calculates the fuel efficiency of a car:

car = {"make": "Ford", "model": "Fiesta", "mileage": 23000, "fuel_consumed": 460}

mpg = car["mileage"] / car["fuel_consumed"]
name = f"{car['make']} {car['model']}"
print(f"{name} does {mpg} miles per gallon.")

# You could put this in a function:


def calculate_mpg():
    car = {"make": "Ford", "model": "Fiesta", "mileage": 23000, "fuel_consumed": 460}

    mpg = car["mileage"] / car["fuel_consumed"]
    name = f"{car['make']} {car['model']}"
    print(f"{name} does {mpg} miles per gallon.")


calculate_mpg()

# But this is not a very reusable function since it only calculates the mpg of a single car.
# What if we made it calculate the mpg of "any" arbitrary car?

car = {"make": "Ford", "model": "Fiesta", "mileage": 23000, "fuel_consumed": 460}


def calculate_mpg(car_to_calculate):  # This can be renamed to `car`
    mpg = car_to_calculate["mileage"] / car_to_calculate["fuel_consumed"]
    name = f"{car_to_calculate['make']} {car_to_calculate['model']}"
    print(f"{name} does {mpg} miles per gallon.")


calculate_mpg(car)

# This means that given a list of cars with the correct data format, we can run the function for all of them!

cars = [
    {"make": "Ford", "model": "Fiesta", "mileage": 23000, "fuel_consumed": 460},
    {"make": "Ford", "model": "Focus", "mileage": 17000, "fuel_consumed": 350},
    {"make": "Mazda", "model": "MX-5", "mileage": 49000, "fuel_consumed": 900},
    {"make": "Mini", "model": "Cooper", "mileage": 31000, "fuel_consumed": 235},
]

for car in cars:
    calculate_mpg(car)



# returning values

def calculate_mpg(car):
    mpg = car["mileage"] / car["fuel_consumed"]
    return mpg  # Ends the function, gives back the value


def car_name(car):
    return f"{car['make']} {car['model']}"


def print_car_info(car):
    name = car_name(car)
    mpg = calculate_mpg(car)

    print(f"{name} does {mpg} miles per gallon.")
    # Returns None by default, as all functions do


cars = [
    {"make": "Ford", "model": "Fiesta", "mileage": 23000, "fuel_consumed": 460},
    {"make": "Ford", "model": "Focus", "mileage": 17000, "fuel_consumed": 350},
    {"make": "Mazda", "model": "MX-5", "mileage": 49000, "fuel_consumed": 900},
    {"make": "Mini", "model": "Cooper", "mileage": 31000, "fuel_consumed": 235},
]

for car in cars:
    print_car_info(car)
    # try print(print_car_info(car)), you'll see None


# -- Multiple returns --
def divide(x, y):
    if y == 0:
        return "You tried to divide by zero!"
    else:
        return x / y


print(divide(10, 2))  # 5
print(divide(6, 0))  # You tried to divide by zero!


# default parameter

def add(x, y=3):  # x=2, y is not OK
    total = x + y
    print(total)


add(5)
add(2, 6)
add(x=3)
add(x=5, y=2)

# add(y=2)  # ERROR!
# add(x=2, 5)  # ERROR!


# -- More named arguments --

print(1, 2, 3, 4, 5, sep=" - ")  # default is " "

# You can use almost anything as a default parameter value.
# But using variables as default parameter values is discouraged, as that can introduce difficult to spot bugs

default_y = 3


def add(x, y=default_y):
    sum = x + y
    print(sum)


add(2)  # 5

default_y = 4
print(default_y)  # 4

add(2)  # 5

# Be careful when using lists or dictionaries as default parameter values. Unlike integers or strings, these will update if you modify the original list or dictionary.

# This is due to a language feature called mutability. It's not important to understand this now, but just know that they behave differently to integers and strings behind the scenes when you change them.


# lambada functions / arrow functions

# Lambda functions are functions that are almost solely used to get inputs and return outputs.
# That means we don't often use them to make actions.
# For example, the `print()` function is a function that performs an action. As such, it would not be suitable for lambda function.
# If we wanted a function that just divided two numbers, that might be suitable for a lambda function.

# That's because that function takes inputs, processes them, and returns outputs. And, it's a short, simple function. You'll see why that is relevant with this example.

divide = lambda x, y: x / y
# This spacing is common. After each comma in the parameters, after the colon but not before, and between operators (though that's optional, and sometimes will be seen without spaces).

# That is a lambda function, which takes two arguments and returns the result of dividing one by the other. It is almost identical to this function:


def divide(x, y):
    return x / y


# In both cases you would call it as a normal function:

print(divide(15, 3))

# While traditional functions _need_ the name (you can't define one without it), lambda functions don't have names unless you assign them to a variable.

result = (lambda x, y: x + y)(15, 3)
print(result)

# However you can see that lambda functions can be quite difficult to read, so we won't be using them very often. The main reason to use lambda function is because they are short, so if we use them in conjunction with other functions that can help make our programs a bit more flexible.

# Here's an example. Instead of this:


def average(sequence):
    return sum(sequence) / len(sequence)


students = [
    {"name": "Rolf", "grades": (67, 90, 95, 100)},
    {"name": "Bob", "grades": (56, 78, 80, 90)},
    {"name": "Jen", "grades": (98, 90, 95, 99)},
    {"name": "Anne", "grades": (100, 100, 95, 100)},
]

for student in students:
    print(average(student["grades"]))

# Since the average function just takes inputs and returns an output, we could re-define it as a lambda function.

average = lambda sequence: sum(sequence) / len(sequence)

students = [
    {"name": "Rolf", "grades": (67, 90, 95, 100)},
    {"name": "Bob", "grades": (56, 78, 80, 90)},
    {"name": "Jen", "grades": (98, 90, 95, 99)},
    {"name": "Anne", "grades": (100, 100, 95, 100)},
]

for student in students:
    print(average(student["grades"]))



# fitst_class_functions (Python, Functions are First class citizen (which is same in JavaScript as well) )
    
    # In Python, functions are first class citizens.
# That means that, just like any other value, they can be passed as arguments to functions or assigned to variables.
# Here's a simple (yet not terribly useful) example to illustrate it:


def greet():
    print("Hello!")


hello = greet  # hello is another name for the greet function now.

hello()

# Let's move on to a more useful example.

# These don't _have_ to be lambdas. They could be normal functions too!
# I'm making them lambdas because they're really short.

avg =  lambda seq: sum(seq) / len(seq)
total = lambda seq: sum(seq)  # could just be `sum`
top = lambda seq: max(seq)  # could just be `max`

students = [
    {"name": "Rolf", "grades": (67, 90, 95, 100)},
    {"name": "Bob", "grades": (56, 78, 80, 90)},
    {"name": "Jen", "grades": (98, 90, 95, 99)},
    {"name": "Anne", "grades": (100, 100, 95, 100)},
]

for student in students:
    name = student["name"]
    grades = student["grades"]

    print(f"Student: {name}")
    operation = input("Enter 'average', 'total', or 'top': ")
    
    if operation == "average":
        print(avg(grades))
    elif operation == "total":
        print(total(grades))
    elif operation == "top":
        print(top(grades))

# Here, you can see how we can store functions inside a dictionary—just as we could do with numbers, strings, or any other type of data.
# We're creating a dictionary of what would be user input to the function that we want to run in each case.

operations = {
    "average": avg,
    "total": total,  # could just be `sum`
    "top": top,  # could just be `max`
}

# The `operations` dictionary could also be defined inline:

operations = {
    "average": lambda seq: sum(seq) / len(seq),
    "total": lambda seq: sum(seq),  # could just be `sum`
    "top": lambda seq: max(seq),  # could just be `max`
}

# The rest of the code can make use of the `operations` dictionary

for student in students:
    name = student["name"]
    grades = student["grades"]

    print(f"Student: {name}")
    operation = input("Enter 'average', 'total', or 'top': ")
    operation_function = operations[operation]  # This means we don't need an if statement (but could get errors!)

    print(operation_function(grades))


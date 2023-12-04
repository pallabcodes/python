my_string = "Hello, world!"
single_quote_string = "Hello, world!"

# Strings can use either single or double quotes. It's up to you which one you use!

string_with_quotes = "Hello, it's me."
another_with_quotes = 'He said "You are amazing!" yesterday.'

escaped_quotes = 'He said "You are amazing!" yesterday.'

print(escaped_quotes) # prints : He said "You are amazing!" Yesterday

multiline = """Hello, world.

My name is Jose. Welcome to my program.
"""
print(multiline)

# concatenate them (join them together).

name = "Jose"
greeting = "Hello, " + name

print(greeting)


# You cannot add strings and numbers, as that always results in an error:

# age = 34
# print("You are " + age)

age = 34
age_as_string = str(34)
print("You are " + age_as_string)


# String formatting

another_greeting = f"How are you, {name}?"
print(another_greeting)

final_greeting = "How are you, {}?".format(name)
print(final_greeting)

friend_name = "Rolf"
goodbye = "Goodbye, {name}!"
goodbye_rolf = goodbye.format(name=friend_name)
print(goodbye_rolf)


# Another example of using `.format()` on a variable:

greeting = "How are you, {}?"
print(greeting.format(name))
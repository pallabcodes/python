# -- Defining tuples --

short_tuple = "Rolf", "Bob"
a_bit_clearer = ("Rolf", "Bob")
not_a_tuple = "Rolf"

# -- Adding to a tuple --

friends = ("Rolf", "Bob", "Anne")
# friends.append("Jen")  # ERROR! Since Tuple is immutable

print(friends)  # ["Rolf", "Bob", "Anne", "Jen"]

# -- Removing from a tuple --

# friends.remove("Bob")  # ERROR!

print(friends)  # ["Rolf", "Anne", "Jen"]
print(type(friends))

# Tuples are useful for when you want to keep it unchanged forever.
# Most of the time I'd recommend using tuples over lists, and only use lists when you specifically want to allow changes.

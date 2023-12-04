"""
We use input() to present the user with a prompt.
They can then type, and when they press Enter everything they typed gets returned.
We can assign that to a variable if we want!
"""


my_name = "Jose"
# your_name = '?'
your_name = input("Enter your name: ")

print(f"Hello {your_name}. My name is {my_name}.")


age = input("Enter your age: ")  # Enter 2
age_num = int(age) # take the user input i.e. stored in "age variable" and now convert it into interger and store it in "age_num"
print(f"Two years mean total {age_num * 12} months.") 


age = int(input("Enter your age: "))  # Enter 2
print(f"Two years mean total {age * 12} months.") 


age = int(input("Enter your age: "))  # Enter 2
months = age * 12

print(f"Two years mean total {months} months.") 

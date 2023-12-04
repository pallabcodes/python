# renmainder ( divisor = 5, divident = 13, quotient = 2 and remainder = 3)

integer_division = 13 // 5  # should be 2.6
print(integer_division)  # prints 2


# modulo ( divisor, divident, quotient and remainder)

# 10 % 5 = 0 or 12 % 5 = 2 and when divident is smaller than divisor e.g. 0 % 5 = 0 and 1 % 5 = 1

remainder = 13 % 5
print(remainder)  # prints 3


# length and total of numbers

grades = [80, 75, 90, 100]
grades = (80, 75, 90, 100)
grades = {80, 75, 90, 100}  # This one, because of no duplicates


total = sum(grades)
length = len(grades)

average = total / length

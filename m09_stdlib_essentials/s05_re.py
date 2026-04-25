"""
Module: Regular Expressions (re module)

Key Insights:
1. 're.search' vs 're.match': Search looks anywhere; match looks from the start.
2. 're.findall' returns all matches as a list of strings.
3. Use raw strings (r"") for regex patterns to avoid escaping backslashes.
"""

import re

text = "User: Jose, Email: jose@tecladocode.com, Phone: +1-555-0199"

# 1. Simple search
# Extracting the email
email_pattern = r"[\w\.-]+@[\w\.-]+\.\w+"
match = re.search(email_pattern, text)
if match:
    print(f"Found email: {match.group(0)}")

# 2. Captured Groups
# Extracting name and email separately
pattern = r"User: (\w+), Email: ([\w\.-]+@[\w\.-]+\.\w+)"
match = re.search(pattern, text)
if match:
    print(f"Name: {match.group(1)}")
    print(f"Email: {match.group(2)}")

# 3. Find All
# Extracting all words
words = re.findall(r"\w+", text)
print(f"First 5 words: {words[:5]}")

# 4. Substitution (Find and Replace)
censored = re.sub(r"\+1-\d{3}-\d{4}", "[REDACTED]", text)
print(f"Censored: {censored}")

# 5. Compiled Regex (Performance)
# Recommended if you use the same pattern multiple times.
prog = re.compile(r"\d+")
print(f"Numbers: {prog.findall(text)}")

if __name__ == "__main__":
    pass

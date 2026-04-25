"""
Module: Datetime and Timezones

Key Insights:
1. Always work with UTC internally.
2. 'datetime.now(timezone.utc)' is the modern best practice.
3. Use 'strftime' for formatting and 'strptime' for parsing.
"""

from datetime import datetime, timezone, timedelta

# 1. Current UTC time
now = datetime.now(timezone.utc)
print(f"Current UTC: {now}")

# 2. Arithmetic (Timedelta)
tomorrow = now + timedelta(days=1)
print(f"Tomorrow: {tomorrow}")

# 3. Formatting (to string)
# %Y: Year, %m: Month, %d: Day, %H: Hour, %M: Minute, %S: Second
fmt = now.strftime("%Y-%m-%d %H:%M:%S %Z")
print(f"Formatted: {fmt}")

# 4. Parsing (from string)
date_str = "2026-04-23 14:30:00"
parsed = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
# Note: strptime result is "naive" (no timezone) by default.
# Always localize it!
localized = parsed.replace(tzinfo=timezone.utc)
print(f"Parsed & Localized: {localized}")

# 5. Unix Timestamps (C-Interop friendly)
timestamp = now.timestamp()
print(f"Unix Timestamp: {timestamp}")
from_ts = datetime.fromtimestamp(timestamp, tz=timezone.utc)

if __name__ == "__main__":
    pass

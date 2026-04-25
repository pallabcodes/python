"""
Module: High-Performance Data Modeling with Pydantic V2

Key Insights for Systems Engineers:
1. Pydantic V2 is written in RUST, making it significantly faster than V1 or standard dataclasses.
2. It provides STRICT type validation at the boundary of your system (JSON, ENV, DB).
3. 'Serialization' and 'Validation' are first-class citizens.
"""

from typing import List, Optional
from pydantic import BaseModel, Field, EmailStr, ValidationError

# 1. Defining a Model
# Similar to a C struct but with runtime validation.
class User(BaseModel):
    id: int
    username: str = Field(..., min_length=3)
    email: str # In production, use EmailStr (requires 'pydantic[email]')
    tags: List[str] = []
    metadata: Optional[dict] = None

# 2. Parsing and Validation
raw_data = {
    "id": "123",  # Note: Pydantic will coerce string to int if possible
    "username": "jose",
    "email": "jose@tecladocode.com",
    "tags": ["admin", "python"]
}

try:
    user = User(**raw_data)
    print(f"Validated User: {user}")
except ValidationError as e:
    print(f"Validation failed: {e.json()}")

# 3. Handling Invalid Data
invalid_data = {"id": "abc", "username": "jo"}
try:
    User(**invalid_data)
except ValidationError as e:
    print(f"Caught expected error: {len(e.errors())} issues found.")

# 4. Serialization
# Convert model back to dict or JSON
print(f"As Dict: {user.model_dump()}")
print(f"As JSON: {user.model_dump_json()}")

# 5. Performance Note:
# Pydantic is the backbone of FastAPI (Discord's backend choice) 
# and is used heavily at Google for handling complex gRPC-to-JSON transformations.

if __name__ == "__main__":
    pass

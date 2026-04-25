from pydantic import BaseModel, Field, field_validator
import re

class Book(BaseModel):
    name: str = Field(..., min_length=1)
    price: float = Field(..., gt=0)
    rating: int = Field(..., ge=1, le=5)
    link: str

    @field_validator('price', mode='before')
    @classmethod
    def parse_price(cls, v):
        if isinstance(v, str):
            # Extract float from "£51.77"
            match = re.search(r"(\d+\.\d+)", v)
            if match:
                return float(match.group(1))
        return v

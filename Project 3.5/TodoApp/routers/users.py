from typing import Annotated
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, Path
from starlette import status
from models import Users
from database import SessionLocal
from .auth import get_current_user
from passlib.context import CryptContext

# Create a router for user endpoints
router = APIRouter(
    prefix='/user',  # All endpoints start with /user
    tags=['user']    # Tag for documentation
)

# Dependency function to get a database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]
bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

# Model for verifying and changing passwords
class UserVerification(BaseModel):
    password: str  # Current password
    new_password: str = Field(min_length=6)  # New password (must be at least 6 characters)

# Endpoint to get the current user's profile info
@router.get('/', status_code=status.HTTP_200_OK)
async def get_user(user: user_dependency, db: db_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication Failed')
    # Return the user info from the database
    return db.query(Users).filter(Users.id == user.get('id')).first()

# Endpoint to change the user's password
@router.put("/password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(user: user_dependency, db: db_dependency,
                          user_verification: UserVerification):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication Failed')
    # Get the user from the database
    user_model = db.query(Users).filter(Users.id == user.get('id')).first()
    # Check if the current password is correct
    if not bcrypt_context.verify(user_verification.password, user_model.hashed_password):
        raise HTTPException(status_code=401, detail='Error on password change')
    # Hash and set the new password
    user_model.hashed_password = bcrypt_context.hash(user_verification.new_password)
    db.add(user_model)
    db.commit()

# Endpoint to change the user's phone number
@router.put("/phonenumber/{phone_number}", status_code=status.HTTP_204_NO_CONTENT)
async def change_phonenumber(user: user_dependency, db: db_dependency,
                          phone_number: str):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication Failed')
    # Get the user from the database
    user_model = db.query(Users).filter(Users.id == user.get('id')).first()
    # Update the phone number
    user_model.phone_number = phone_number
    db.add(user_model)
    db.commit()


# Lets users view their profile, change their password, and update their phone number.
# Password changes require the current password for security.
# Only authenticated users can access these endpoints.


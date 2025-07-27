from typing import Annotated
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, Path
from starlette import status
from models import Todos
from database import SessionLocal
from .auth import get_current_user

# Create a router for admin endpoints
router = APIRouter(
    prefix='/admin',  # All endpoints will start with /admin
    tags=['admin']    # Tag for documentation
)

# Dependency function to get a database session
def get_db():
    db = SessionLocal()  # Create a new session
    try:
        yield db         # Provide the session to the endpoint
    finally:
        db.close()       # Always close the session after use

# Dependency for database session and current user
db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]

# Endpoint to get all todos in the system (admin only)
@router.get("/todo", status_code=status.HTTP_200_OK)
async def read_all(user: user_dependency, db: db_dependency):
    # Only allow if user is authenticated and has 'admin' role
    if user is None or user.get('user_role') != 'admin':
        raise HTTPException(status_code=401, detail='Authentication Failed')
    # Return all todos from the database
    return db.query(Todos).all()

# Endpoint to delete any todo by its ID (admin only)
@router.delete("/todo/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(user: user_dependency, db: db_dependency, todo_id: int = Path(gt=0)):
    # Only allow if user is authenticated and has 'admin' role
    if user is None or user.get('user_role') != 'admin':
        raise HTTPException(status_code=401, detail='Authentication Failed')
    # Find the todo by ID
    todo_model = db.query(Todos).filter(Todos.id == todo_id).first()
    if todo_model is None:
        raise HTTPException(status_code=404, detail='Todo not found.')
    # Delete the todo from the database
    db.query(Todos).filter(Todos.id == todo_id).delete()
    db.commit()








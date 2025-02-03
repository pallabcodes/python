from fastapi import FastAPI, Form, UploadFile, File, Depends, HTTPException
from typing import List, Optional
from pydantic import BaseModel, validator
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import Session, sessionmaker, DeclarativeBase, Mapped, mapped_column
import os
app = FastAPI()

DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String, unique=True, index=True)
    name: Mapped[str] = mapped_column(String)
    age: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    email: Mapped[str] = mapped_column(String, nullable=True)


class UserCreate(BaseModel):
    username: str
    name: str
    email: str
    age: int = 10

    @validator("name")
    def name_must_not_be_empty(cls, value):
        if not value.strip():
            raise ValueError("must not be empty")
        return value

    @validator("username")
    def username_must_not_contain_spaces(cls, v):
        if " " in v:
            raise ValueError("username must not contain spaces")
        return v

class UserResponse(BaseModel):
    id: int
    username: str
    name: str
    email: Optional[str] = None

    class Config:
        from_attributes = True


Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/users", response_model=UserResponse)
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    print("Received user:", user)

    existing_user = db.query(User).filter(User.username == user.username).first()
    print("Existing user:", existing_user)

    if existing_user:
        raise HTTPException(status_code=400, detail="Username already taken")

    new_user = User(username=user.username, name=user.name, email=user.email, age=user.age)

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        print("User created successfully:", new_user)
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")  # Debugging
        raise HTTPException(status_code=500, detail="Error creating user")

    return new_user



@app.get("/users", response_model=List[UserResponse])
def read_users(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    return db.query(User).offset(skip).limit(limit).all()


@app.get("/users/{user_id}", response_model=UserResponse)
def read_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.post("/register")
async def register_user(user: UserCreate):
    return user


@app.post("/login")
async def login_user(username: str = Form(...), password: str = Form(...)):
    return {"username": username, "message": "login successful"}


@app.post("/uploadfile")
async def create_upload_file(file: UploadFile = File(...)):
    return {"filename": file.filename}


@app.post("/uploadfiles")
async def create_upload_files(files: List[UploadFile] = File(...)):
    return {"filenames": [file.filename for file in files]}


@app.post("/savefile")
async def save_upload_file(file: UploadFile = File(...)):
    os.makedirs('uploads', exist_ok=True)
    with open(f'uploads/{file.filename}', "wb") as f:
        f.write(await file.read())
    return {"message": f"File '{file.filename}' saved successfully"}


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.post("/items")
def create_item(name: str, price: float):
    return {"name": name, "price": price}


@app.get("/items/{item_id}/reviews")
def get_item_reviews(item_id: int, limit: int = 5):
    return {"item_id": item_id, "limit": limit, "reviews": f"Returning {limit} reviews for item {item_id}"}


@app.put("/items/{item_id}")
def update_item(item_id: int, name: str, price: float):
    return {"item_id": item_id, "name": name, "price": price}


@app.delete("/items/{item_id}")
def delete_item(item_id: int):
    return {"item_id": item_id}


@app.get("/users/{user_id}/details")
def read_user_details(user_id: int, include_email: bool = False):
    if include_email:
        return {"user_id": user_id, "include_email": include_email, "email": "<EMAIL>"}
    else:
        return {"user_id": user_id, "include_email": "email is not included"}


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None


@app.put("/users/{user_id}", response_model=UserResponse)
def update_user(user_id: int, user: UserUpdate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    if user.name is not None:
        db_user.name = user.name
    if user.email is not None:
        db_user.email = user.email

    db.commit()
    db.refresh(db_user)
    return db_user


@app.delete("/users/{user_id}", response_model=UserResponse)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(db_user)
    db.commit()
    return db_user

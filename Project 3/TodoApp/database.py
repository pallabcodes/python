from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# The database URL for SQLite. The database file will be todosapp.db in the current folder.
SQLALCHEMY_DATABASE_URL = 'sqlite:///./todosapp.db'

# Create a database engine to connect to SQLite.
# 'check_same_thread=False' allows usage in FastAPI's async environment.
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={'check_same_thread': False})

# Create a session factory for database operations.
# This lets you open and close connections to the database easily.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all ORM models (tables).
# You will use this to define your database tables in models.py.
Base = declarative_base()

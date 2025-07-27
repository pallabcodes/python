from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# The database URL for SQLite. The database file will be todosapp.db in the current folder.
SQLALCHEMY_DATABASE_URL = 'sqlite:///./todosapp.db'

# Create a database engine to connect to SQLite.
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={'check_same_thread': False})

# Create a session factory for database operations.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all ORM models (tables).
Base = declarative_base()


# Sets up the connection to the SQLite database.
# Provides tools to open/close database sessions.
# Prepares a base class for defining tables.
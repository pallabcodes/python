from fastapi import FastAPI
import models
from database import engine
from routers import auth, todos, admin, users

# Create the FastAPI app instance
app = FastAPI()

# Create all database tables defined in models.py if they don't exist yet
models.Base.metadata.create_all(bind=engine)

# Register the authentication, todos, admin, and user routers with the app
app.include_router(auth.router)
app.include_router(todos.router)
app.include_router(admin.router)
app.include_router(users.router)


# Sets up the FastAPI app.
# Initializes the database tables.
# Connects all the main API endpoints (auth, todos, admin, users) to the app.
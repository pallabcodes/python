from fastapi import FastAPI
from .models import Base
from .database import engine
from .routers import auth, todos, admin, users

# Create the FastAPI app instance
app = FastAPI()

# Create all database tables defined in models.py if they don't exist yet
Base.metadata.create_all(bind=engine)

# Health check endpoint to verify the app is running
@app.get("/healthy")
def health_check():
    return {'status': 'Healthy'}

# Register all routers for authentication, todos, admin, and users
app.include_router(auth.router)
app.include_router(todos.router)
app.include_router(admin.router)
app.include_router(users.router)

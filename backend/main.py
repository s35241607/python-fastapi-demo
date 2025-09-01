from fastapi import FastAPI
from app.routers import items, users

app = FastAPI(
    title="FastAPI Demo Application",
    description="A sample FastAPI application with a modular structure",
    version="0.1.0"
)

# Include routers
app.include_router(items.router, prefix="/items", tags=["items"])
app.include_router(users.router, prefix="/users", tags=["users"])

@app.get("/")
async def root():
    return {"message": "Welcome to the FastAPI Demo Application!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
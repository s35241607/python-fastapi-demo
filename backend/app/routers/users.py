from fastapi import APIRouter, HTTPException
from typing import List

router = APIRouter()

# Sample data
users = [
    {"id": 1, "name": "User 1", "email": "user1@example.com"},
    {"id": 2, "name": "User 2", "email": "user2@example.com"},
]

@router.get("/", response_model=List[dict])
async def read_users():
    return users

@router.get("/{user_id}", response_model=dict)
async def read_user(user_id: int):
    for user in users:
        if user["id"] == user_id:
            return user
    raise HTTPException(status_code=404, detail="User not found")

@router.post("/", response_model=dict)
async def create_user(user: dict):
    # In a real app, this would save to a database
    new_user = {"id": len(users) + 1, **user}
    users.append(new_user)
    return new_user
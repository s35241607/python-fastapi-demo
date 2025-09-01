from fastapi import APIRouter, HTTPException
from typing import List

router = APIRouter()

# Sample data
items = [
    {"id": 1, "name": "Item 1", "description": "This is item 1"},
    {"id": 2, "name": "Item 2", "description": "This is item 2"},
]

@router.get("/", response_model=List[dict])
async def read_items():
    return items

@router.get("/{item_id}", response_model=dict)
async def read_item(item_id: int):
    for item in items:
        if item["id"] == item_id:
            return item
    raise HTTPException(status_code=404, detail="Item not found")

@router.post("/", response_model=dict)
async def create_item(item: dict):
    # In a real app, this would save to a database
    new_item = {"id": len(items) + 1, **item}
    items.append(new_item)
    return new_item

@router.put("/{item_id}", response_model=dict)
async def update_item(item_id: int, item: dict):
    for i, existing_item in enumerate(items):
        if existing_item["id"] == item_id:
            items[i] = {"id": item_id, **item}
            return items[i]
    raise HTTPException(status_code=404, detail="Item not found")

@router.delete("/{item_id}")
async def delete_item(item_id: int):
    for i, item in enumerate(items):
        if item["id"] == item_id:
            items.pop(i)
            return {"message": "Item deleted successfully"}
    raise HTTPException(status_code=404, detail="Item not found")
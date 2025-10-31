from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.get("/list")
def list_users():
    # Example static list
    return [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]


@router.post("/create")
def create_user(user: dict):
    # In real app, validate and save user
    return {"id": 3, **user}


@router.get("/{user_id}")
def get_user(user_id: int):
    # Example retrieval
    if user_id == 1:
        return {"id": 1, "name": "Alice"}
    return {"id": user_id, "name": f"User {user_id}"}

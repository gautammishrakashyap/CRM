from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


@router.get("/stats")
def stats():
    return {"users": 123, "active": 100}


@router.post("/config")
def update_config(payload: dict):
    return {"status": "updated", "payload": payload}

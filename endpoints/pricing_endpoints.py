from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/pricing", tags=["pricing"])


@router.get("/plans")
def plans():
    return [{"plan": "free", "price": 0}, {"plan": "pro", "price": 49}]


@router.post("/subscribe")
def subscribe(payload: dict):
    return {"status": "subscribed", "payload": payload}

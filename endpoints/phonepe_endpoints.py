from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/phonepe", tags=["phonepe"])


@router.post("/pay")
def pay(payload: dict):
    return {"status": "payment_initiated", "details": payload}


@router.get("/status/{order_id}")
def payment_status(order_id: str):
    return {"order_id": order_id, "status": "completed"}

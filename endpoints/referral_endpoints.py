from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/referral", tags=["referral"])


@router.post("/generate")
def generate_referral(payload: dict):
    return {"code": "REF12345", "payload": payload}


@router.get("/rewards")
def rewards():
    return {"rewards": [{"user": 1, "points": 100}]}

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/test", tags=["test"])


@router.get("/ping")
def ping():
    return {"message": "pong"}


@router.get("/status")
def status():
    return {"status": "ok", "service": "test"}

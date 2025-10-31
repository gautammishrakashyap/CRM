from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


@router.post("/send")
def send_message(payload: dict):
    # placeholder: echo
    return {"status": "sent", "message": payload}


@router.get("/history")
def history():
    return [{"from": "Alice", "text": "Hello"}, {"from": "Bob", "text": "Hi"}]

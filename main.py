import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi import Request

# Load environment variables from .env if present
load_dotenv()

app = FastAPI()


@app.get("/")
def read_root():
    return {"message": "CRM API is running", "status": "active"}


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "CRM"}


@app.post("/api/v1/token")
def login_for_access_token(username: str = None, password: str = None):
    # Basic token endpoint — placeholder for real auth
    if username and password:
        return {"access_token": "fake-token-12345", "token_type": "bearer"}
    return {"error": "Missing credentials"}


# Database startup/shutdown hooks (optional)
@app.on_event("startup")
async def startup_event():
    # Try to connect to the database if DATABASE_URL is set, but handle errors gracefully
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        # No DB configured; continue without failing
        return
    try:
        # Lazy import to avoid hard dependency if not installed at import time
        from pymongo import MongoClient
        client = MongoClient(db_url)
        # simple server_info check
        client.admin.command("ping")
        app.state._db_client = client
    except Exception as exc:
        # Log to stdout for Render logs; do not raise to keep the app alive
        print(f"[startup] Warning: could not connect to MongoDB: {exc}")


@app.on_event("shutdown")
async def shutdown_event():
    client = getattr(app.state, "_db_client", None)
    if client:
        try:
            client.close()
        except Exception:
            pass


if __name__ == "__main__":
    import uvicorn
    PORT = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=PORT)

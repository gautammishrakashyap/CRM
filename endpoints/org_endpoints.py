from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/org", tags=["org"])


@router.get("/list")
def list_orgs():
    return [{"id": 1, "name": "Org A"}, {"id": 2, "name": "Org B"}]


@router.post("/create")
def create_org(payload: dict):
    return {"id": 3, **payload}

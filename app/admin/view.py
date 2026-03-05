from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def metrics():
    return {"admin": "Hello"}
